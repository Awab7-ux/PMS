import uuid
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app import db

PROJECT_STATUSES = ("Planning", "Active", "On Hold", "Completed", "Archived")
PROJECT_PRIORITIES = ("Low", "Medium", "High", "Critical")


class Project(db.Model):
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("organization_id", "code"),
        CheckConstraint(
            f"status IN ({', '.join(repr(s) for s in PROJECT_STATUSES)})",
            name="ck_project_status",
        ),
        CheckConstraint(
            f"priority IN ({', '.join(repr(p) for p in PROJECT_PRIORITIES)})",
            name="ck_project_priority",
        ),
        CheckConstraint("progress_percent >= 0 AND progress_percent <= 100", name="ck_project_progress"),
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    parent_project_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="Planning")
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="Medium")
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    organization: Mapped["Organization"] = relationship(back_populates="projects")
    owner: Mapped["User"] = relationship(foreign_keys=[owner_user_id])
    memberships: Mapped[list["ProjectMembership"]] = relationship(back_populates="project", cascade="all, delete-orphan")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "owner_user_id": str(self.owner_user_id),
            "parent_project_id": str(self.parent_project_id) if self.parent_project_id else None,
            "name": self.name,
            "code": self.code,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "progress_percent": self.progress_percent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ProjectMembership(db.Model):
    __tablename__ = "project_memberships"
    __table_args__ = (UniqueConstraint("project_id", "user_id"),)

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True), ForeignKey("roles.id"), nullable=True)
    access_level: Mapped[str] = mapped_column(String(50), nullable=False, default="member")
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    project: Mapped[Project] = relationship(back_populates="memberships")
    user: Mapped["User"] = relationship(foreign_keys=[user_id])
    role: Mapped["Role | None"] = relationship(foreign_keys=[role_id])

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "user_id": str(self.user_id),
            "role_id": str(self.role_id) if self.role_id else None,
            "role": self.role.name if self.role else None,
            "access_level": self.access_level,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
