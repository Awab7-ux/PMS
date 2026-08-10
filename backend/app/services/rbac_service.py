import uuid
from typing import Any

from backend.app import db
from backend.app.models.organization import OrganizationMembership, Permission, Role, RolePermission
from backend.app.models.project import Project, ProjectMembership
from backend.app.models.user import User
from backend.app.repositories.organization_repository import OrganizationRepository
from backend.app.repositories.project_repository import ProjectRepository
from backend.app.utils.permissions import ALL_PERMISSIONS, DEFAULT_ROLES, ROLE_PERMISSIONS


class RBACService:
    def __init__(self):
        self.org_repo = OrganizationRepository()
        self.project_repo = ProjectRepository()

    def seed_global_permissions(self) -> None:
        for code in ALL_PERMISSIONS:
            if not self.org_repo.get_permission(code):
                self.org_repo.create_permission(Permission(code=code, description=code))
        db.session.flush()

    def ensure_default_roles(self, organization_id: str | uuid.UUID) -> dict[str, Role]:
        self.seed_global_permissions()
        roles: dict[str, Role] = {}
        for role_name in DEFAULT_ROLES:
            role = self.org_repo.get_role_by_name(organization_id, role_name)
            if not role:
                role = Role(
                    organization_id=organization_id,
                    name=role_name,
                    description=role_name,
                    is_system_default=True,
                )
                self.org_repo.create_role(role)
            self._assign_role_permissions(role, ROLE_PERMISSIONS.get(role_name, []))
            roles[role_name] = role
        return roles

    def _assign_role_permissions(self, role: Role, permission_codes: list[str]) -> None:
        for code in permission_codes:
            permission = self.org_repo.get_permission(code)
            if permission and not self.org_repo.get_role_permission(role.id, permission.id):
                self.org_repo.create_role_permission(RolePermission(role_id=role.id, permission_id=permission.id))

    def get_user_permissions(self, user_id: str, organization_id: str | uuid.UUID) -> set[str]:
        user = db.session.get(User, uuid.UUID(str(user_id)))
        if user and user.is_superuser:
            return set(ALL_PERMISSIONS)

        membership = self.org_repo.get_membership(organization_id, user_id)
        if not membership or membership.status != "active":
            return set()

        if membership.is_owner:
            return set(ALL_PERMISSIONS)

        codes: set[str] = set()
        if membership.role:
            for rp in membership.role.role_permissions:
                if rp.permission:
                    codes.add(rp.permission.code)
        return codes

    def has_permission(
        self,
        user_id: str,
        permission_code: str,
        organization_id: str | uuid.UUID | None = None,
        context: dict[str, Any] | None = None,
    ) -> bool:
        user = db.session.get(User, uuid.UUID(str(user_id)))
        if user and user.is_superuser:
            return True

        org_id = organization_id
        if not org_id and context:
            project_id = context.get("project_id")
            if project_id:
                project = self.project_repo.get_by_id(project_id)
                if project:
                    org_id = project.organization_id
            team_id = context.get("team_id")
            if not org_id and team_id:
                from backend.app.repositories.organization_repository import TeamRepository
                team = TeamRepository().get_by_id(team_id)
                if team:
                    org_id = team.organization_id

        if not org_id:
            return False

        permissions = self.get_user_permissions(user_id, org_id)
        return permission_code in permissions

    def require_org_membership(self, user_id: str, organization_id: str) -> OrganizationMembership:
        membership = self.org_repo.get_membership(organization_id, user_id)
        if not membership or membership.status != "active":
            raise PermissionError("Access denied")
        return membership

    def require_project_access(self, user_id: str, project_id: str) -> Project:
        project = self.project_repo.get_by_id(project_id)
        if not project or project.deleted_at is not None:
            raise ValueError("Project not found")

        membership = self.org_repo.get_membership(project.organization_id, user_id)
        if not membership or membership.status != "active":
            raise PermissionError("Access denied")

        project_membership = self.project_repo.get_membership(project.id, user_id)
        perms = self.get_user_permissions(user_id, project.organization_id)
        manager_perms = {"project.update", "project.delete", "project.create"}
        if not project_membership and not (perms & manager_perms):
            raise PermissionError("Access denied")
        return project
