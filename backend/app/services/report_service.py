from typing import Any

from sqlalchemy import func

from backend.app import db
from backend.app.models.project import Project
from backend.app.models.task import Task
from backend.app.repositories.project_repository import ProjectRepository
from backend.app.repositories.task_repository import TaskRepository
from backend.app.services.rbac_service import RBACService
from backend.app.repositories.support_repositories import ActivityRepository


class ReportService:
    def __init__(self):
        self.project_repo = ProjectRepository()
        self.task_repo = TaskRepository()
        self.rbac = RBACService()
        self.activity = ActivityRepository()

    def get_analytics(self, user_id: str, organization_id: str) -> dict[str, Any]:
        self.rbac.require_org_membership(user_id, organization_id)
        perms = self.rbac.get_user_permissions(user_id, organization_id)
        if "report.view" not in perms:
            user_perms = perms
            if not user_perms:
                raise PermissionError("Insufficient permissions")

        import uuid
        try:
            parsed = uuid.UUID(str(organization_id))
        except (ValueError, TypeError):
            raise ValueError("Invalid organization")

        total_projects = db.session.execute(
            db.select(func.count(Project.id)).where(
                Project.organization_id == parsed, Project.deleted_at.is_(None)
            )
        ).scalar() or 0

        active_projects = db.session.execute(
            db.select(func.count(Project.id)).where(
                Project.organization_id == parsed,
                Project.status == "Active",
                Project.deleted_at.is_(None),
            )
        ).scalar() or 0

        completed_projects = db.session.execute(
            db.select(func.count(Project.id)).where(
                Project.organization_id == parsed,
                Project.status == "Completed",
                Project.deleted_at.is_(None),
            )
        ).scalar() or 0

        total_tasks = db.session.execute(
            db.select(func.count(Task.id)).where(
                Task.organization_id == parsed, Task.deleted_at.is_(None)
            )
        ).scalar() or 0

        completed_tasks = db.session.execute(
            db.select(func.count(Task.id)).where(
                Task.organization_id == parsed,
                Task.status == "DONE",
                Task.deleted_at.is_(None),
            )
        ).scalar() or 0

        overdue_tasks = len(self.task_repo.list_overdue(organization_id))
        tasks_by_status = self.task_repo.count_by_status(organization_id)
        tasks_by_priority = self.task_repo.count_by_priority(organization_id)

        avg_progress = db.session.execute(
            db.select(func.avg(Project.progress_percent)).where(
                Project.organization_id == parsed, Project.deleted_at.is_(None)
            )
        ).scalar() or 0

        return {
            "total_projects": total_projects,
            "active_projects": active_projects,
            "completed_projects": completed_projects,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "overdue_tasks": overdue_tasks,
            "tasks_by_status": tasks_by_status,
            "tasks_by_priority": tasks_by_priority,
            "average_project_progress": round(float(avg_progress), 1),
            "completion_rate": round((completed_tasks / total_tasks * 100) if total_tasks else 0, 1),
        }

    def get_activity(self, user_id: str, query_params: dict[str, Any]) -> dict[str, Any]:
        organization_id = query_params.get("organization_id")
        if organization_id:
            self.rbac.require_org_membership(user_id, organization_id)
        page = max(int(query_params.get("page") or 1), 1)
        per_page = min(max(int(query_params.get("per_page") or 50), 1), 100)
        items, total = self.activity.list(
            organization_id=organization_id,
            entity_type=query_params.get("entity_type"),
            entity_id=query_params.get("entity_id"),
            page=page,
            per_page=per_page,
        )
        return {
            "items": [a.to_dict() for a in items],
            "pagination": {"page": page, "per_page": per_page, "total": total, "pages": (total + per_page - 1) // per_page if total else 0},
        }
