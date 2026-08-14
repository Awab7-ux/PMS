import uuid
from datetime import datetime, timezone

from backend.app import db
from backend.app.models.event import Event
from backend.app.utils.uuid_helpers import parse_uuid


class EventRepository:
    def create(self, event: Event) -> Event:
        db.session.add(event)
        db.session.flush()
        return event

    def get_by_id(self, event_id: str | uuid.UUID | None) -> Event | None:
        parsed = parse_uuid(event_id)
        return db.session.get(Event, parsed) if parsed else None

    def list(self, organization_id, start=None, end=None, project_id=None, team_id=None) -> list[Event]:
        query = db.select(Event).where(Event.organization_id == organization_id)
        if start:
            query = query.where(Event.start_at <= end, (Event.end_at.is_(None)) | (Event.end_at >= start))
        if project_id:
            query = query.where(Event.project_id == project_id)
        if team_id:
            query = query.where(Event.team_id == team_id)
        return list(db.session.execute(query.order_by(Event.start_at.asc(), Event.created_at.asc())).scalars().all())

    def update(self, event: Event) -> Event:
        event.updated_at = datetime.now(timezone.utc)
        db.session.flush()
        return event

    def delete(self, event: Event) -> None:
        db.session.delete(event)
        db.session.flush()
