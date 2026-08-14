import uuid
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app import db

TASK_STATUSES = ("BACKLOG", "TODO", "IN_PROGRESS", "REVIEW", "DONE")
TASK_PRIORITIES = ("LOW", "MEDIUM", "HIGH", "CRITICAL")


class TaskTag(db.Model):
    __tablename__ = "task_tags"
    __table_args__ = (UniqueConstraint("project_id", "name"),)

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    project: Mapped["Project"] = relationship(back_populates="tags")
    task_associations: Mapped[list["TaskTagAssociation"]] = relationship(back_populates="tag", cascade="all, delete-orphan")

    def to_dict(self) -> dict[str, Any]:
        return {"id": str(self.id), "project_id": str(self.project_id), "name": self.name, "color": self.color}


class TaskTagAssociation(db.Model):
    __tablename__ = "task_tag_associations"
    __table_args__ = (UniqueConstraint("task_id", "tag_id"),)

    task_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), ForeignKey("tasks.id"), primary_key=True)
    tag_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), ForeignKey("task_tags.id"), primary_key=True)

    task: Mapped["Task"] = relationship(back_populates="tag_associations")
    tag: Mapped[TaskTag] = relationship(back_populates="task_associations")


class Task(db.Model):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(f"status IN ({', '.join(repr(s) for s in TASK_STATUSES)})", name="ck_task_status"),
        CheckConstraint(f"priority IN ({', '.join(repr(p) for p in TASK_PRIORITIES)})", name="ck_task_priority"),
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    team_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="BACKLOG", index=True)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIUM")
    creator_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    estimated_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    kanban_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped["Project"] = relationship(back_populates="tasks")
    creator: Mapped["User"] = relationship(foreign_keys=[creator_id])
    assignee: Mapped["User | None"] = relationship(foreign_keys=[assignee_id])
    subtasks: Mapped[list["Subtask"]] = relationship(back_populates="task", cascade="all, delete-orphan", order_by="Subtask.order_index")
    tag_associations: Mapped[list[TaskTagAssociation]] = relationship(back_populates="task", cascade="all, delete-orphan")
    comments: Mapped[list["Comment"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    attachments: Mapped[list["FileAttachment"]] = relationship(back_populates="task", cascade="all, delete-orphan")

    def to_dict(self, include_subtasks: bool = False) -> dict[str, Any]:
        tags = [a.tag.to_dict() for a in self.tag_associations if a.tag]
        data = {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "organization_id": str(self.organization_id),
            "team_id": str(self.team_id) if self.team_id else None,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "creator_id": str(self.creator_id),
            "assignee_id": str(self.assignee_id) if self.assignee_id else None,
            "creator": self.creator.to_dict() if self.creator else None,
            "assignee": self.assignee.to_dict() if self.assignee else None,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours,
            "kanban_order": self.kanban_order,
            "progress_percent": self.progress_percent,
            "tags": tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_subtasks:
            data["subtasks"] = [s.to_dict() for s in self.subtasks]
        return data


class Subtask(db.Model):
    __tablename__ = "subtasks"

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    task: Mapped[Task] = relationship(back_populates="subtasks")
    assignee: Mapped["User | None"] = relationship(foreign_keys=[assignee_id])

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "task_id": str(self.task_id),
            "title": self.title,
            "is_completed": self.is_completed,
            "assignee_id": str(self.assignee_id) if self.assignee_id else None,
            "order_index": self.order_index,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
