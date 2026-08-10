import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app import db


class FileAttachment(db.Model):
    __tablename__ = "file_attachments"

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True, index=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True, index=True)
    uploader_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    task: Mapped["Task | None"] = relationship(back_populates="attachments")
    uploader: Mapped["User"] = relationship(foreign_keys=[uploader_id])

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "task_id": str(self.task_id) if self.task_id else None,
            "project_id": str(self.project_id) if self.project_id else None,
            "uploader_id": str(self.uploader_id),
            "original_filename": self.original_filename,
            "mime_type": self.mime_type,
            "file_size": self.file_size,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
