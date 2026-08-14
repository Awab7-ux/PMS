from datetime import date, timedelta
from typing import Any

from backend.app import db
from backend.app.models.task import Task
from backend.app.repositories.event_repository import EventRepository
from backend.app.repositories.project_repository import ProjectRepository
from backend.app.services.event_service import EventService
from backend.app.services.rbac_service import RBACService
from backend.app.utils.uuid_helpers import parse_uuid


class CalendarService:
    """Combined calendar feed; due-dated tasks remain task entities."""
    def __init__(self):
        self.projects, self.events, self.rbac = ProjectRepository(), EventRepository(), RBACService()
        self.event_service = EventService()

    @staticmethod
    def _date(value, fallback):
        if not value:
            return fallback
        try:
            return date.fromisoformat(str(value)[:10])
        except ValueError as exc:
            raise ValueError("Invalid date format; use YYYY-MM-DD") from exc

    def get_events(self, user_id: str, query_params: dict[str, Any]) -> dict[str, Any]:
        org_id = parse_uuid(query_params.get("organization_id"))
        if not org_id:
            raise ValueError("organization_id is required")
        self.rbac.require_org_membership(user_id, str(org_id))
        start = self._date(query_params.get("start"), date.today().replace(day=1))
        end = self._date(query_params.get("end"), start + timedelta(days=31))
        if end < start:
            raise ValueError("end must be on or after start")
        project_filter, team_filter = parse_uuid(query_params.get("project_id")), parse_uuid(query_params.get("team_id"))
        if query_params.get("project_id") and not project_filter: raise ValueError("Invalid project_id")
        if query_params.get("team_id") and not team_filter: raise ValueError("Invalid team_id")
        projects, _ = self.projects.list_for_user(user_id, str(org_id), page=1, per_page=1000)
        project_ids = {project.id for project in projects}
        if project_filter and project_filter not in project_ids:
            raise PermissionError("Access denied")
        task_query = db.select(Task).where(Task.organization_id == org_id, Task.deleted_at.is_(None), Task.due_date.isnot(None), Task.due_date >= start, Task.due_date <= end, Task.project_id.in_(project_ids or [parse_uuid("00000000-0000-0000-0000-000000000000")]))
        if project_filter: task_query = task_query.where(Task.project_id == project_filter)
        if team_filter: task_query = task_query.where(Task.team_id == team_filter)
        if query_params.get("status"): task_query = task_query.where(Task.status == query_params["status"].upper())
        if query_params.get("priority"): task_query = task_query.where(Task.priority == query_params["priority"].upper())
        items = []
        for task in db.session.execute(task_query).scalars():
            items.append({"id": str(task.id), "type": "task", "title": task.title, "date": task.due_date.isoformat(), "due_date": task.due_date.isoformat(), "status": task.status, "priority": task.priority, "project": {"id": str(task.project.id), "name": task.project.name} if task.project else None, "assignee": {"id": str(task.assignee.id), "full_name": task.assignee.full_name} if task.assignee else None})
        for event in self.events.list(org_id, None, None, project_filter, team_filter):
            if event.start_at.date() > end or (event.end_at and event.end_at.date() < start):
                continue
            try: self.event_service._access(user_id, event)
            except PermissionError: continue
            data = event.to_dict(); data["date"] = data["start_at"][:10]; items.append(data)
        items.sort(key=lambda item: (item["date"], item["title"].lower()))
        return {"events": items, "start": start.isoformat(), "end": end.isoformat()}
