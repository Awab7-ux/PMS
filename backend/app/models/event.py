import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app import db


class Event(db.Model):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True, index=True)
    team_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True, index=True)
    created_by_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    all_day: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reminder_settings: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    project: Mapped["Project | None"] = relationship(foreign_keys=[project_id])
    team: Mapped["Team | None"] = relationship(foreign_keys=[team_id])
    creator: Mapped["User"] = relationship(foreign_keys=[created_by_id])

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id), "type": "event", "organization_id": str(self.organization_id),
            "title": self.title, "description": self.description,
            "start_at": self.start_at.isoformat() if self.start_at else None,
            "end_at": self.end_at.isoformat() if self.end_at else None,
            "all_day": self.all_day, "location": self.location,
            "project_id": str(self.project_id) if self.project_id else None,
            "project": {"id": str(self.project.id), "name": self.project.name} if self.project else None,
            "team_id": str(self.team_id) if self.team_id else None,
            "team": {"id": str(self.team.id), "name": self.team.name} if self.team else None,
            "created_by_id": str(self.created_by_id),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
