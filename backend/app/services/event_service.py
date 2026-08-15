from datetime import date, datetime, time, timezone
from typing import Any

from backend.app import db
from backend.app.models.activity_log import ActivityLog
from backend.app.models.event import Event
from backend.app.repositories.event_repository import EventRepository
from backend.app.repositories.organization_repository import TeamRepository
from backend.app.repositories.support_repositories import ActivityRepository
from backend.app.services.rbac_service import RBACService
from backend.app.services.support_services import NotificationService
from backend.app.services.realtime_service import RealtimeService
from backend.app.utils.uuid_helpers import parse_uuid


class EventService:
    def __init__(self):
        self.repo, self.rbac = EventRepository(), RBACService()
        self.teams, self.activity, self.notifications = TeamRepository(), ActivityRepository(), NotificationService()

    @staticmethod
    def _datetime(value, field, required=False):
        if value in (None, ""):
            if required:
                raise ValueError(f"{field} is required")
            return None
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"Invalid {field} datetime; use ISO 8601") from exc
        if parsed.tzinfo is None:
            raise ValueError(f"{field} must include a timezone")
        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _range_datetime(value, end=False):
        if not value:
            return None
        if len(str(value)) == 10:
            try:
                return datetime.combine(date.fromisoformat(str(value)), time.max if end else time.min, tzinfo=timezone.utc)
            except ValueError as exc:
                raise ValueError("Invalid date format; use YYYY-MM-DD or ISO 8601") from exc
        return EventService._datetime(value, "end" if end else "start", True)

    def _related(self, user_id, payload, existing=None):
        project_id = payload.get("project_id", str(existing.project_id) if existing and existing.project_id else None)
        team_id = payload.get("team_id", str(existing.team_id) if existing and existing.team_id else None)
        project = self.rbac.require_project_access(user_id, project_id) if project_id else None
        team = self.teams.get_by_id(team_id) if team_id else None
        if team_id and (not team or team.deleted_at is not None):
            raise ValueError("Team not found")
        org_id = project.organization_id if project else (team.organization_id if team else (existing.organization_id if existing else parse_uuid(payload.get("organization_id"))))
        if not org_id:
            raise ValueError("project_id, team_id, or organization_id is required")
        self.rbac.require_org_membership(user_id, str(org_id))
        if team and team.organization_id != org_id:
            raise ValueError("Team must belong to the event organization")
        return org_id, project, team

    def _access(self, user_id, event, permission=None):
        self.rbac.require_org_membership(user_id, str(event.organization_id))
        if event.project_id:
            self.rbac.require_project_access(user_id, str(event.project_id))
        if permission and str(event.created_by_id) != str(user_id) and not self.rbac.has_permission(user_id, permission, event.organization_id):
            raise PermissionError("Insufficient permissions")

    def _log(self, event, actor_id, action, metadata=None):
        self.activity.create(ActivityLog(organization_id=event.organization_id, actor_id=parse_uuid(actor_id), action=action, entity_type="event", entity_id=str(event.id), metadata_json=metadata or {}))

    def _notify_team(self, event, actor_id, kind):
        if not event.team_id:
            return
        for membership in self.teams.list_memberships(event.team_id):
            if str(membership.user_id) != str(actor_id):
                self.notifications.create(str(membership.user_id), kind, "Calendar event updated" if kind == "EVENT_UPDATED" else "Calendar event cancelled", event.title, "event", str(event.id))

    def create(self, user_id: str, payload: dict[str, Any]) -> dict:
        title = (payload.get("title") or "").strip()
        if not title:
            raise ValueError("Title is required")
        if len(title) > 255:
            raise ValueError("Title must be 255 characters or fewer")
        org_id, project, team = self._related(user_id, payload)
        if not self.rbac.has_permission(user_id, "event.create", org_id):
            raise PermissionError("Insufficient permissions")
        start_at = self._datetime(payload.get("start_at"), "start_at", True)
        all_day = bool(payload.get("all_day"))
        end_at = self._datetime(payload.get("end_at"), "end_at")
        if not all_day and not end_at:
            raise ValueError("end_at is required for timed events")
        if end_at and end_at < start_at:
            raise ValueError("end_at must be on or after start_at")
        event = Event(organization_id=org_id, project_id=project.id if project else None, team_id=team.id if team else None, created_by_id=parse_uuid(user_id), title=title, description=(payload.get("description") or "").strip() or None, start_at=start_at, end_at=end_at, all_day=all_day, location=(payload.get("location") or "").strip() or None, reminder_settings={"offsets_minutes": [1440, 60]})
        self.repo.create(event); self._log(event, user_id, "event.created", {"title": title}); db.session.commit()
        result = event.to_dict(); RealtimeService.organization(str(event.organization_id), "calendar_event.created", result)
        if event.project_id: RealtimeService.publish(f"project:{event.project_id}", "calendar_event.created", result)
        return result

    def get(self, user_id, event_id):
        event = self.repo.get_by_id(event_id)
        if not event: raise ValueError("Event not found")
        self._access(user_id, event)
        result = event.to_dict(); RealtimeService.organization(str(event.organization_id), "calendar_event.updated", result)
        if event.project_id: RealtimeService.publish(f"project:{event.project_id}", "calendar_event.updated", result)
        return result

    def list(self, user_id, query):
        org_id = parse_uuid(query.get("organization_id"))
        if not org_id: raise ValueError("organization_id is required")
        self.rbac.require_org_membership(user_id, str(org_id))
        start = self._range_datetime(query.get("start"))
        end = self._range_datetime(query.get("end"), True)
        if start and end and end < start: raise ValueError("end must be on or after start")
        project_id, team_id = parse_uuid(query.get("project_id")), parse_uuid(query.get("team_id"))
        if query.get("project_id") and not project_id: raise ValueError("Invalid project_id")
        if query.get("team_id") and not team_id: raise ValueError("Invalid team_id")
        events = []
        for event in self.repo.list(org_id, start, end, project_id, team_id):
            try: self._access(user_id, event)
            except PermissionError: continue
            events.append(event.to_dict())
        return {"items": events}

    def update(self, user_id, event_id, payload):
        event = self.repo.get_by_id(event_id)
        if not event: raise ValueError("Event not found")
        self._access(user_id, event, "event.update")
        old_start = event.start_at
        org_id, project, team = self._related(user_id, payload, event)
        if org_id != event.organization_id: raise ValueError("Event organization cannot be changed")
        if "title" in payload:
            title = (payload.get("title") or "").strip()
            if not title or len(title) > 255: raise ValueError("Title must be between 1 and 255 characters")
            event.title = title
        for key in ("description", "location"):
            if key in payload: setattr(event, key, (payload.get(key) or "").strip() or None)
        if "all_day" in payload: event.all_day = bool(payload["all_day"])
        if "start_at" in payload: event.start_at = self._datetime(payload.get("start_at"), "start_at", True)
        if "end_at" in payload: event.end_at = self._datetime(payload.get("end_at"), "end_at")
        if not event.all_day and not event.end_at: raise ValueError("end_at is required for timed events")
        if event.end_at and event.end_at < event.start_at: raise ValueError("end_at must be on or after start_at")
        event.project_id, event.team_id = (project.id if project else None), (team.id if team else None)
        self.repo.update(event); action = "event.rescheduled" if event.start_at != old_start else "event.updated"; self._log(event, user_id, action); self._notify_team(event, user_id, "EVENT_UPDATED"); db.session.commit()
        return event.to_dict()

    def delete(self, user_id, event_id):
        event = self.repo.get_by_id(event_id)
        if not event: raise ValueError("Event not found")
        self._access(user_id, event, "event.delete")
        self._log(event, user_id, "event.deleted", {"title": event.title}); self._notify_team(event, user_id, "EVENT_CANCELLED"); self.repo.delete(event); db.session.commit()
        payload = {"event_id": str(event.id), "organization_id": str(event.organization_id)}; RealtimeService.organization(str(event.organization_id), "calendar_event.deleted", payload)
        if event.project_id: RealtimeService.publish(f"project:{event.project_id}", "calendar_event.deleted", payload)
        return {"message": "Event deleted"}
