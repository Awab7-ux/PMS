import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app import db

CONVERSATION_TYPES = ("direct", "group", "project", "team")


class Conversation(db.Model):
    __tablename__ = "conversations"
    __table_args__ = (
        CheckConstraint(
            f"type IN ({', '.join(repr(t) for t in CONVERSATION_TYPES)})",
            name="ck_conversation_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="direct")
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    project_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True, index=True)
    team_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    organization: Mapped["Organization"] = relationship(foreign_keys=[organization_id])
    creator: Mapped["User"] = relationship(foreign_keys=[created_by])
    project: Mapped["Project | None"] = relationship(foreign_keys=[project_id])
    team: Mapped["Team | None"] = relationship(foreign_keys=[team_id])
    members: Mapped[list["ConversationMember"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "type": self.type,
            "name": self.name,
            "created_by": str(self.created_by),
            "project_id": str(self.project_id) if self.project_id else None,
            "team_id": str(self.team_id) if self.team_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ConversationMember(db.Model):
    __tablename__ = "conversation_members"
    __table_args__ = (UniqueConstraint("conversation_id", "user_id", name="uq_conversation_member"),)

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    last_read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    conversation: Mapped[Conversation] = relationship(back_populates="members")
    user: Mapped["User"] = relationship()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "user_id": str(self.user_id),
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "last_read_at": self.last_read_at.isoformat() if self.last_read_at else None,
        }


class Message(db.Model):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
    sender_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
    sender: Mapped["User"] = relationship(foreign_keys=[sender_id])

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "sender_id": str(self.sender_id),
            "sender_name": self.sender.full_name if self.sender else "Unknown",
            "sender_avatar_url": self.sender.avatar_url if self.sender else None,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "is_deleted": self.deleted_at is not None,
        }
