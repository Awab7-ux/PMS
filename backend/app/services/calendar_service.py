from datetime import date, timedelta
from typing import Any

from backend.app.repositories.organization_repository import OrganizationRepository
from backend.app.repositories.project_repository import ProjectRepository
from backend.app.repositories.task_repository import TaskRepository
from backend.app.services.rbac_service import RBACService


class CalendarService:
    def __init__(self):
        self.task_repo = TaskRepository()
        self.project_repo = ProjectRepository()
        self.org_repo = OrganizationRepository()
        self.rbac = RBACService()

    def get_events(self, user_id: str, query_params: dict[str, Any]) -> dict[str, Any]:
        organization_id = query_params.get("organization_id")
        if not organization_id:
            raise ValueError("organization_id is required")
        self.rbac.require_org_membership(user_id, organization_id)

        start_str = query_params.get("start")
        end_str = query_params.get("end")
        start = date.fromisoformat(start_str[:10]) if start_str else date.today().replace(day=1)
        end = date.fromisoformat(end_str[:10]) if end_str else (start + timedelta(days=31))

        events = []
        projects, _ = self.project_repo.list_for_user(user_id, organization_id, None, None, 1, 1000)
        for project in projects:
            if project.end_date and start <= project.end_date <= end:
                events.append({
                    "type": "project_deadline",
                    "title": f"Project deadline: {project.name}",
                    "date": project.end_date.isoformat(),
                    "entity_id": str(project.id),
                    "entity_type": "project",
                })

        tasks, _ = self.task_repo.list_for_project(
            projects[0].id if projects else "00000000-0000-0000-0000-000000000000",
            page=1, per_page=1000,
        ) if projects else ([], 0)

        from backend.app import db
        from backend.app.models.task import Task
        import uuid
        try:
            parsed_org = uuid.UUID(str(organization_id))
        except (ValueError, TypeError):
            parsed_org = None

        if parsed_org:
            all_tasks = db.session.execute(
                db.select(Task).where(
                    Task.organization_id == parsed_org,
                    Task.due_date.isnot(None),
                    Task.due_date >= start,
                    Task.due_date <= end,
                    Task.deleted_at.is_(None),
                )
            ).scalars().all()
            for task in all_tasks:
                events.append({
                    "type": "task_due",
                    "title": task.title,
                    "date": task.due_date.isoformat(),
                    "entity_id": str(task.id),
                    "entity_type": "task",
                    "status": task.status,
                    "priority": task.priority,
                })

        events.sort(key=lambda e: e["date"])
        return {"events": events, "start": start.isoformat(), "end": end.isoformat()}
