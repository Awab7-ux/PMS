import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import desc, and_

from backend.app import db
from backend.app.models.conversation import Conversation, ConversationMember, Message
from backend.app.models.user import User


class ConversationRepository:
    def create(self, conversation: Conversation) -> Conversation:
        db.session.add(conversation)
        db.session.flush()
        return conversation

    def update(self, conversation: Conversation) -> Conversation:
        db.session.flush()
        return conversation

    def get_by_id(self, conversation_id: str | uuid.UUID | None) -> Optional[Conversation]:
        if not conversation_id:
            return None
        try:
            parsed = uuid.UUID(str(conversation_id))
        except (ValueError, TypeError):
            return None
        return db.session.get(Conversation, parsed)

    def list_for_user(self, user_id: str | uuid.UUID, organization_id: str | uuid.UUID, page: int = 1, per_page: int = 20) -> tuple[list[Conversation], int]:
        """List conversations accessible to the user in an organization."""
        try:
            user_uuid = uuid.UUID(str(user_id))
            org_uuid = uuid.UUID(str(organization_id))
        except (ValueError, TypeError):
            return [], 0

        # Join with ConversationMember to ensure user is a member
        query = (
            db.select(Conversation)
            .join(ConversationMember, Conversation.id == ConversationMember.conversation_id)
            .where(
                and_(
                    Conversation.organization_id == org_uuid,
                    ConversationMember.user_id == user_uuid,
                    Conversation.deleted_at.is_(None),
                )
            )
            .order_by(desc(Conversation.updated_at))
        )

        total = db.session.query(Conversation).join(
            ConversationMember, Conversation.id == ConversationMember.conversation_id
        ).filter(
            and_(
                Conversation.organization_id == org_uuid,
                ConversationMember.user_id == user_uuid,
                Conversation.deleted_at.is_(None),
            )
        ).count()

        items = db.session.execute(
            query.offset((page - 1) * per_page).limit(per_page)
        ).scalars().all()

        return items, total

    def get_direct_conversation(self, organization_id: str | uuid.UUID, user_a_id: str | uuid.UUID, user_b_id: str | uuid.UUID) -> Optional[Conversation]:
        """Get direct conversation between two users in an organization."""
        try:
            org_uuid = uuid.UUID(str(organization_id))
            user_a_uuid = uuid.UUID(str(user_a_id))
            user_b_uuid = uuid.UUID(str(user_b_id))
        except (ValueError, TypeError):
            return None

        # Find all direct conversations in the organization
        conversations = db.session.execute(
            db.select(Conversation).where(
                and_(
                    Conversation.organization_id == org_uuid,
                    Conversation.type == "direct",
                    Conversation.deleted_at.is_(None),
                )
            )
        ).scalars().all()

        # Check each conversation for membership of both users
        for conv in conversations:
            members = db.session.execute(
                db.select(ConversationMember).where(
                    ConversationMember.conversation_id == conv.id
                )
            ).scalars().all()
            member_ids = {str(m.user_id) for m in members}
            if str(user_a_uuid) in member_ids and str(user_b_uuid) in member_ids:
                return conv

        return None


class ConversationMemberRepository:
    def create(self, member: ConversationMember) -> ConversationMember:
        db.session.add(member)
        db.session.flush()
        return member

    def get_by_id(self, member_id: str | uuid.UUID | None) -> Optional[ConversationMember]:
        if not member_id:
            return None
        try:
            parsed = uuid.UUID(str(member_id))
        except (ValueError, TypeError):
            return None
        return db.session.get(ConversationMember, parsed)

    def get_member(self, conversation_id: str | uuid.UUID, user_id: str | uuid.UUID) -> Optional[ConversationMember]:
        """Get a specific member of a conversation."""
        try:
            conv_uuid = uuid.UUID(str(conversation_id))
            user_uuid = uuid.UUID(str(user_id))
        except (ValueError, TypeError):
            return None

        return db.session.execute(
            db.select(ConversationMember).where(
                and_(
                    ConversationMember.conversation_id == conv_uuid,
                    ConversationMember.user_id == user_uuid,
                )
            )
        ).scalar_one_or_none()

    def list_members(self, conversation_id: str | uuid.UUID) -> list[ConversationMember]:
        """List all members of a conversation."""
        try:
            conv_uuid = uuid.UUID(str(conversation_id))
        except (ValueError, TypeError):
            return []

        return db.session.execute(
            db.select(ConversationMember).where(
                ConversationMember.conversation_id == conv_uuid
            ).order_by(ConversationMember.joined_at)
        ).scalars().all()

    def member_exists(self, conversation_id: str | uuid.UUID, user_id: str | uuid.UUID) -> bool:
        """Check if a user is a member of a conversation."""
        return self.get_member(conversation_id, user_id) is not None

    def update_last_read(self, conversation_id: str | uuid.UUID, user_id: str | uuid.UUID) -> Optional[ConversationMember]:
        """Update last_read_at for a member."""
        member = self.get_member(conversation_id, user_id)
        if member:
            member.last_read_at = datetime.now(timezone.utc)
            db.session.flush()
        return member

    def delete(self, member: ConversationMember) -> None:
        db.session.delete(member)
        db.session.flush()


class MessageRepository:
    def create(self, message: Message) -> Message:
        db.session.add(message)
        db.session.flush()
        return message

    def get_by_id(self, message_id: str | uuid.UUID | None) -> Optional[Message]:
        if not message_id:
            return None
        try:
            parsed = uuid.UUID(str(message_id))
        except (ValueError, TypeError):
            return None
        return db.session.get(Message, parsed)

    def get_messages(self, conversation_id: str | uuid.UUID, limit: int = 50, offset: int = 0) -> tuple[list[Message], int]:
        """Get messages for a conversation with pagination."""
        try:
            conv_uuid = uuid.UUID(str(conversation_id))
        except (ValueError, TypeError):
            return [], 0

        query = db.select(Message).where(
            and_(
                Message.conversation_id == conv_uuid,
                Message.deleted_at.is_(None),
            )
        ).order_by(desc(Message.created_at))

        total = db.session.query(Message).filter(
            and_(
                Message.conversation_id == conv_uuid,
                Message.deleted_at.is_(None),
            )
        ).count()

        items = db.session.execute(
            query.offset(offset).limit(limit)
        ).scalars().all()

        return list(reversed(items)), total  # Reverse to get chronological order

    def get_messages_after(self, conversation_id: str | uuid.UUID, after_message_id: str | uuid.UUID | None = None, limit: int = 50) -> list[Message]:
        """Get new messages after a specific message ID."""
        try:
            conv_uuid = uuid.UUID(str(conversation_id))
        except (ValueError, TypeError):
            return []

        if after_message_id:
            try:
                after_uuid = uuid.UUID(str(after_message_id))
                after_msg = self.get_by_id(after_uuid)
                if not after_msg:
                    return []
                
                query = db.select(Message).where(
                    and_(
                        Message.conversation_id == conv_uuid,
                        Message.created_at > after_msg.created_at,
                        Message.deleted_at.is_(None),
                    )
                ).order_by(Message.created_at).limit(limit)
            except (ValueError, TypeError):
                return []
        else:
            query = db.select(Message).where(
                and_(
                    Message.conversation_id == conv_uuid,
                    Message.deleted_at.is_(None),
                )
            ).order_by(Message.created_at).limit(limit)

        return db.session.execute(query).scalars().all()

    def update(self, message: Message) -> Message:
        db.session.flush()
        return message

    def soft_delete(self, message: Message) -> Message:
        """Soft delete a message."""
        message.deleted_at = datetime.now(timezone.utc)
        db.session.flush()
        return message
