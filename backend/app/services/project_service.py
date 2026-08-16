from datetime import date
from typing import Any

from backend.app import db
from backend.app.models.project import PROJECT_STATUSES, PROJECT_PRIORITIES, Project, ProjectMembership
from backend.app.repositories.organization_repository import OrganizationRepository
from backend.app.repositories.project_repository import ProjectRepository
from backend.app.repositories.user_repository import UserRepository
from backend.app.services.support_services import NotificationService
from backend.app.services.realtime_service import RealtimeService
from backend.app.utils.uuid_helpers import parse_uuid


class ProjectService:
    MANAGER_ROLES = {"Organization Owner", "Project Manager"}

    def __init__(
        self,
        project_repository: ProjectRepository | None = None,
        organization_repository: OrganizationRepository | None = None,
        user_repository: UserRepository | None = None,
    ):
        self.project_repository = project_repository or ProjectRepository()
        self.organization_repository = organization_repository or OrganizationRepository()
        self.user_repository = user_repository or UserRepository()
        self.notifications = NotificationService()

    @staticmethod
    def _parse_date(value: str | None) -> date | None:
        if not value:
            return None
        try:
            return date.fromisoformat(str(value)[:10])
        except ValueError as exc:
            raise ValueError("Invalid date format; use YYYY-MM-DD") from exc

    def _get_org_membership(self, organization_id: str, user_id: str):
        membership = self.organization_repository.get_membership(organization_id, user_id)
        if not membership or membership.status != "active":
            raise PermissionError("Access denied")
        return membership

    def _can_manage_projects(self, org_membership) -> bool:
        return org_membership.role.name in self.MANAGER_ROLES

    def _get_project_with_access(self, user_id: str, project_id: str) -> Project:
        project = self.project_repository.get_by_id(project_id)
        if not project or project.deleted_at is not None:
            raise ValueError("Project not found")
        org_membership = self._get_org_membership(str(project.organization_id), user_id)
        project_membership = self.project_repository.get_membership(project.id, user_id)
        if not project_membership and not self._can_manage_projects(org_membership):
            raise PermissionError("Access denied")
        return project

    def create_project(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        organization_id = payload.get("organization_id")
        if not organization_id:
            raise ValueError("organization_id is required")
        org_membership = self._get_org_membership(organization_id, user_id)
        if not self._can_manage_projects(org_membership):
            raise PermissionError("Insufficient permissions")

        name = (payload.get("name") or "").strip()
        if not name:
            raise ValueError("Name is required")

        status = (payload.get("status") or "Planning").strip()
        if status not in PROJECT_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(PROJECT_STATUSES)}")

        priority = (payload.get("priority") or "Medium").strip()
        if priority not in PROJECT_PRIORITIES:
            raise ValueError(f"Priority must be one of: {', '.join(PROJECT_PRIORITIES)}")

        code = (payload.get("code") or "").strip() or None
        if code and self.project_repository.get_by_code(organization_id, code):
            raise ValueError("Project code already in use")

        owner_id = parse_uuid(payload.get("owner_user_id")) or parse_uuid(user_id)
        if not owner_id:
            raise ValueError("Invalid owner")

        project = Project(
            organization_id=parse_uuid(organization_id),
            owner_user_id=owner_id,
            name=name,
            code=code,
            description=(payload.get("description") or "").strip() or None,
            status=status,
            priority=priority,
            start_date=self._parse_date(payload.get("start_date")),
            end_date=self._parse_date(payload.get("end_date")),
            progress_percent=int(payload.get("progress_percent") or 0),
        )
        self.project_repository.create(project)

        owner_membership = ProjectMembership(
            project_id=project.id,
            user_id=owner_id,
            access_level="owner",
        )
        self.project_repository.create_membership(owner_membership)

        if owner_id != parse_uuid(user_id):
            creator_membership = ProjectMembership(
                project_id=project.id,
                user_id=parse_uuid(user_id),
                access_level="manager",
            )
            self.project_repository.create_membership(creator_membership)

        db.session.commit()
        result = project.to_dict()
        RealtimeService.organization(str(project.organization_id), "project.created", result)
        return result

    def list_projects(self, user_id: str, query_params: dict[str, Any]) -> dict[str, Any]:
        page = max(int(query_params.get("page") or 1), 1)
        per_page = min(max(int(query_params.get("per_page") or 20), 1), 100)
        organization_id = query_params.get("organization_id")
        status = query_params.get("status")
        search = query_params.get("search")

        if organization_id:
            self._get_org_membership(organization_id, user_id)
            org_membership = self.organization_repository.get_membership(organization_id, user_id)
            if self._can_manage_projects(org_membership):
                all_projects = self.project_repository.list_for_organization(organization_id)
                if status:
                    all_projects = [p for p in all_projects if p.status == status]
                if search:
                    term = search.strip().lower()
                    all_projects = [
                        p for p in all_projects
                        if term in p.name.lower() or (p.code and term in p.code.lower())
                    ]
                total = len(all_projects)
                offset = (page - 1) * per_page
                projects = all_projects[offset : offset + per_page]
            else:
                projects, total = self.project_repository.list_for_user(
                    user_id, organization_id, status, search, page, per_page
                )
        else:
            projects, total = self.project_repository.list_for_user(
                user_id, None, status, search, page, per_page
            )

        return {
            "items": [p.to_dict() for p in projects],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page if total else 0,
            },
        }

    def get_project(self, user_id: str, project_id: str) -> dict[str, Any]:
        project = self._get_project_with_access(user_id, project_id)
        return project.to_dict()

    def update_project(self, user_id: str, project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        project = self._get_project_with_access(user_id, project_id)
        org_membership = self.organization_repository.get_membership(str(project.organization_id), user_id)
        project_membership = self.project_repository.get_membership(project.id, user_id)
        is_manager = self._can_manage_projects(org_membership)
        is_project_owner = project_membership and project_membership.access_level == "owner"
        if not is_manager and not is_project_owner:
            raise PermissionError("Insufficient permissions")

        if "name" in payload and payload.get("name"):
            project.name = payload.get("name").strip()
        if "description" in payload:
            project.description = (payload.get("description") or "").strip() or None
        if "status" in payload and payload.get("status"):
            status = payload.get("status").strip()
            if status not in PROJECT_STATUSES:
                raise ValueError(f"Status must be one of: {', '.join(PROJECT_STATUSES)}")
            project.status = status
        if "priority" in payload and payload.get("priority"):
            priority = payload.get("priority").strip()
            if priority not in PROJECT_PRIORITIES:
                raise ValueError(f"Priority must be one of: {', '.join(PROJECT_PRIORITIES)}")
            project.priority = priority
        if "code" in payload:
            code = (payload.get("code") or "").strip() or None
            if code and code != project.code:
                existing = self.project_repository.get_by_code(project.organization_id, code)
                if existing and existing.id != project.id:
                    raise ValueError("Project code already in use")
            project.code = code
        if "start_date" in payload:
            project.start_date = self._parse_date(payload.get("start_date"))
        if "end_date" in payload:
            project.end_date = self._parse_date(payload.get("end_date"))
        if "progress_percent" in payload and payload.get("progress_percent") is not None:
            progress = int(payload.get("progress_percent"))
            if progress < 0 or progress > 100:
                raise ValueError("progress_percent must be between 0 and 100")
            project.progress_percent = progress
        if "owner_user_id" in payload and is_manager:
            owner_id = parse_uuid(payload.get("owner_user_id"))
            if owner_id:
                project.owner_user_id = owner_id

        self.project_repository.update(project)
        db.session.commit()
        result = project.to_dict()
        RealtimeService.organization(str(project.organization_id), "project.updated", result)
        return result

    def delete_project(self, user_id: str, project_id: str) -> dict[str, Any]:
        project = self._get_project_with_access(user_id, project_id)
        org_membership = self.organization_repository.get_membership(str(project.organization_id), user_id)
        if not self._can_manage_projects(org_membership):
            raise PermissionError("Insufficient permissions")
        self.project_repository.delete(project)
        db.session.commit()
        RealtimeService.organization(str(project.organization_id), "project.deleted", {"project_id": str(project.id), "organization_id": str(project.organization_id)})
        return {"message": "Project archived"}

    def list_members(self, user_id: str, project_id: str) -> list[dict[str, Any]]:
        self._get_project_with_access(user_id, project_id)
        memberships = self.project_repository.list_memberships(project_id)
        return [m.to_dict() for m in memberships]

    def add_member(self, acting_user_id: str, project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        project = self._get_project_with_access(acting_user_id, project_id)
        org_membership = self.organization_repository.get_membership(str(project.organization_id), acting_user_id)
        if not self._can_manage_projects(org_membership):
            raise PermissionError("Insufficient permissions")

        target_identifier = (payload.get("user_id") or "").strip()
        target_user = None
        if "@" in target_identifier:
            target_user = self.user_repository.get_by_email(target_identifier.lower())
        else:
            target_user = self.user_repository.get_by_id(target_identifier)
        if not target_user:
            raise ValueError("User not found")

        org_member = self.organization_repository.get_membership(project.organization_id, target_user.id)
        if not org_member or org_member.status != "active":
            raise ValueError("User is not a member of the organization")
        if self.project_repository.get_membership(project.id, target_user.id):
            raise ValueError("Member already exists")

        role_id = parse_uuid(payload.get("role_id"))
        membership = ProjectMembership(
            project_id=project.id,
            user_id=target_user.id,
            role_id=role_id,
            access_level=(payload.get("access_level") or "member").strip(),
        )
        self.project_repository.create_membership(membership)
        self.notifications.notify_project_added(project, str(target_user.id), acting_user_id)
        db.session.commit()
        return membership.to_dict()

    def remove_member(self, acting_user_id: str, project_id: str, user_id: str) -> dict[str, Any]:
        project = self._get_project_with_access(acting_user_id, project_id)
        org_membership = self.organization_repository.get_membership(str(project.organization_id), acting_user_id)
        if not self._can_manage_projects(org_membership):
            raise PermissionError("Insufficient permissions")

        membership = self.project_repository.get_membership(project_id, user_id)
        if not membership:
            raise ValueError("Member not found")
        if str(membership.user_id) == str(project.owner_user_id):
            raise ValueError("Cannot remove project owner")
        self.project_repository.remove_membership(membership)
        db.session.commit()
        return {"message": "Member removed"}
