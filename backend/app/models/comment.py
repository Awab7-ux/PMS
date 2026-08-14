import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app import db


class Comment(db.Model):
    __tablename__ = "comments"

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False, index=True)
    author_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    mentions_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    task: Mapped["Task"] = relationship(back_populates="comments")
    author: Mapped["User"] = relationship(foreign_keys=[author_id])
    attachments: Mapped[list["FileAttachment"]] = relationship(back_populates="comment", cascade="all, delete-orphan")

    @property
    def mentions(self) -> list[str]:
        import json
        if not self.mentions_json:
            return []
        try:
            return json.loads(self.mentions_json)
        except (json.JSONDecodeError, TypeError):
            return []

    @mentions.setter
    def mentions(self, value: list[str] | None) -> None:
        import json
        self.mentions_json = json.dumps(value or [])

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "task_id": str(self.task_id),
            "author_id": str(self.author_id),
            "author_name": self.author.full_name if self.author else None,
            "content": self.content,
            "mentions": self.mentions,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
