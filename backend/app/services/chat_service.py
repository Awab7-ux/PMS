import uuid
from typing import Any

from backend.app import db
from backend.app.models.conversation import Conversation, ConversationMember, Message, CONVERSATION_TYPES
from backend.app.models.project import Project, ProjectMembership
from backend.app.models.team import Team, TeamMembership
from backend.app.models.user import User
from backend.app.repositories.conversation_repository import ConversationRepository, ConversationMemberRepository, MessageRepository
from backend.app.repositories.organization_repository import OrganizationRepository
from backend.app.repositories.project_repository import ProjectRepository
from backend.app.repositories.user_repository import UserRepository
from backend.app.repositories.support_repositories import NotificationRepository
from backend.app.services.rbac_service import RBACService
from backend.app.services.support_services import NotificationService
from backend.app.utils.uuid_helpers import parse_uuid


class ConversationService:
    def __init__(
        self,
        conv_repo: ConversationRepository | None = None,
        member_repo: ConversationMemberRepository | None = None,
        message_repo: MessageRepository | None = None,
        org_repo: OrganizationRepository | None = None,
        user_repo: UserRepository | None = None,
        project_repo: ProjectRepository | None = None,
        rbac: RBACService | None = None,
        notifications: NotificationService | None = None,
    ):
        self.conv_repo = conv_repo or ConversationRepository()
        self.member_repo = member_repo or ConversationMemberRepository()
        self.message_repo = message_repo or MessageRepository()
        self.org_repo = org_repo or OrganizationRepository()
        self.user_repo = user_repo or UserRepository()
        self.project_repo = project_repo or ProjectRepository()
        self.rbac = rbac or RBACService()
        self.notifications = notifications or NotificationService()

    def _get_current_user(self, user_id: str | uuid.UUID) -> User:
        """Get current user, raise ValueError if not found."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        return user

    def _verify_organization_access(self, user_id: str | uuid.UUID, organization_id: str | uuid.UUID) -> None:
        """Verify user is a member of the organization."""
        membership = self.org_repo.get_membership(organization_id, user_id)
        if not membership or membership.status != "active":
            raise PermissionError("Not a member of this organization")

    def _verify_conversation_membership(self, user_id: str | uuid.UUID, conversation_id: str | uuid.UUID) -> ConversationMember:
        """Verify user is a member of the conversation."""
        member = self.member_repo.get_member(conversation_id, user_id)
        if not member:
            raise PermissionError("Not a member of this conversation")
        return member

    def list_conversations(self, user_id: str, organization_id: str, page: int = 1, per_page: int = 20) -> dict[str, Any]:
        """List conversations for the user in an organization."""
        user_id = parse_uuid(user_id)
        organization_id = parse_uuid(organization_id)

        self._verify_organization_access(user_id, organization_id)

        conversations, total = self.conv_repo.list_for_user(user_id, organization_id, page, per_page)
        return {
            "items": [self._format_conversation(conv, user_id) for conv in conversations],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page if total else 0,
            },
        }

    def get_conversation(self, user_id: str, conversation_id: str) -> dict[str, Any]:
        """Get conversation details."""
        user_id = parse_uuid(user_id)
        conversation_id = parse_uuid(conversation_id)

        conversation = self.conv_repo.get_by_id(conversation_id)
        if not conversation or conversation.deleted_at:
            raise ValueError("Conversation not found")

        self._verify_conversation_membership(user_id, conversation_id)
        self._verify_organization_access(user_id, conversation.organization_id)

        return self._format_conversation(conversation, user_id)

    def create_direct_message_conversation(self, user_id: str, other_user_id: str, organization_id: str) -> dict[str, Any]:
        """Create or get a direct message conversation between two users."""
        user_id = parse_uuid(user_id)
        other_user_id = parse_uuid(other_user_id)
        organization_id = parse_uuid(organization_id)

        if user_id == other_user_id:
            raise ValueError("Cannot create a conversation with yourself")

        self._verify_organization_access(user_id, organization_id)
        self._verify_organization_access(other_user_id, organization_id)

        # Try to find existing direct conversation
        existing = self.conv_repo.get_direct_conversation(organization_id, user_id, other_user_id)
        if existing:
            return self._format_conversation(existing, user_id)

        # Create new direct conversation
        conversation = Conversation(
            organization_id=organization_id,
            type="direct",
            created_by=user_id,
        )
        self.conv_repo.create(conversation)

        # Add both users as members
        self.member_repo.create(ConversationMember(conversation_id=conversation.id, user_id=user_id))
        self.member_repo.create(ConversationMember(conversation_id=conversation.id, user_id=other_user_id))

        db.session.commit()

        return self._format_conversation(conversation, user_id)

    def create_group_conversation(self, user_id: str, organization_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a group conversation."""
        user_id = parse_uuid(user_id)
        organization_id = parse_uuid(organization_id)

        self._verify_organization_access(user_id, organization_id)

        name = (payload.get("name") or "").strip()
        if not name:
            raise ValueError("Group name is required")

        conversation = Conversation(
            organization_id=organization_id,
            type="group",
            name=name,
            created_by=user_id,
        )
        self.conv_repo.create(conversation)

        # Add creator as member
        self.member_repo.create(ConversationMember(conversation_id=conversation.id, user_id=user_id))

        # Add other members if specified
        member_ids = payload.get("member_ids", [])
        for member_id in member_ids:
            member_uuid = parse_uuid(member_id)
            if member_uuid and member_uuid != user_id:
                try:
                    self._verify_organization_access(member_uuid, organization_id)
                    self.member_repo.create(ConversationMember(conversation_id=conversation.id, user_id=member_uuid))
                except (ValueError, PermissionError):
                    # Skip invalid members
                    pass

        db.session.commit()

        return self._format_conversation(conversation, user_id)

    def create_project_conversation(self, user_id: str, organization_id: str, project_id: str) -> dict[str, Any]:
        """Create a project conversation for a project."""
        user_id = parse_uuid(user_id)
        organization_id = parse_uuid(organization_id)
        project_id = parse_uuid(project_id)

        self._verify_organization_access(user_id, organization_id)

        # Verify project exists and user has access
        project = self.project_repo.get_by_id(project_id)
        if not project or str(project.organization_id) != str(organization_id):
            raise ValueError("Project not found or not in this organization")

        # Check if user has project access
        project_member = db.session.execute(
            db.select(ProjectMembership).where(
                (ProjectMembership.project_id == project_id) & (ProjectMembership.user_id == user_id)
            )
        ).scalar_one_or_none()
        if not project_member:
            raise PermissionError("No access to this project")

        # Check if conversation already exists
        existing = db.session.execute(
            db.select(Conversation).where(
                (Conversation.project_id == project_id)
                & (Conversation.type == "project")
                & (Conversation.deleted_at.is_(None))
            )
        ).scalar_one_or_none()
        if existing:
            return self._format_conversation(existing, user_id)

        # Create project conversation
        conversation = Conversation(
            organization_id=organization_id,
            type="project",
            name=f"{project.name} - Chat",
            project_id=project_id,
            created_by=user_id,
        )
        self.conv_repo.create(conversation)

        # Add all project members to conversation
        project_members = db.session.execute(
            db.select(ProjectMembership).where(ProjectMembership.project_id == project_id)
        ).scalars().all()

        for pm in project_members:
            self.member_repo.create(ConversationMember(conversation_id=conversation.id, user_id=pm.user_id))

        db.session.commit()

        return self._format_conversation(conversation, user_id)

    def create_team_conversation(self, user_id: str, organization_id: str, team_id: str) -> dict[str, Any]:
        """Create a team conversation for a team."""
        user_id = parse_uuid(user_id)
        organization_id = parse_uuid(organization_id)
        team_id = parse_uuid(team_id)

        self._verify_organization_access(user_id, organization_id)

        # Verify team exists and user has access
        team = db.session.execute(
            db.select(Team).where((Team.id == team_id) & (Team.organization_id == organization_id))
        ).scalar_one_or_none()
        if not team:
            raise ValueError("Team not found or not in this organization")

        # Check if user is a team member
        team_member = db.session.execute(
            db.select(TeamMembership).where((TeamMembership.team_id == team_id) & (TeamMembership.user_id == user_id))
        ).scalar_one_or_none()
        if not team_member:
            raise PermissionError("Not a member of this team")

        # Check if conversation already exists
        existing = db.session.execute(
            db.select(Conversation).where(
                (Conversation.team_id == team_id) & (Conversation.type == "team") & (Conversation.deleted_at.is_(None))
            )
        ).scalar_one_or_none()
        if existing:
            return self._format_conversation(existing, user_id)

        # Create team conversation
        conversation = Conversation(
            organization_id=organization_id,
            type="team",
            name=f"{team.name} - Chat",
            team_id=team_id,
            created_by=user_id,
        )
        self.conv_repo.create(conversation)

        # Add all team members to conversation
        team_members = db.session.execute(
            db.select(TeamMembership).where(TeamMembership.team_id == team_id)
        ).scalars().all()

        for tm in team_members:
            self.member_repo.create(ConversationMember(conversation_id=conversation.id, user_id=tm.user_id))

        db.session.commit()

        return self._format_conversation(conversation, user_id)

    def update_conversation(self, user_id: str, conversation_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Update conversation (for group conversations only)."""
        user_id = parse_uuid(user_id)
        conversation_id = parse_uuid(conversation_id)

        conversation = self.conv_repo.get_by_id(conversation_id)
        if not conversation or conversation.deleted_at:
            raise ValueError("Conversation not found")

        self._verify_conversation_membership(user_id, conversation_id)
        self._verify_organization_access(user_id, conversation.organization_id)

        # Only allow updates to group conversations
        if conversation.type != "group":
            raise PermissionError("Cannot update this conversation type")

        # Only creator can update
        if str(conversation.created_by) != str(user_id):
            raise PermissionError("Only the creator can update this conversation")

        name = payload.get("name")
        if name is not None:
            conversation.name = name.strip()

        self.conv_repo.update(conversation)
        db.session.commit()

        return self._format_conversation(conversation, user_id)

    def delete_conversation(self, user_id: str, conversation_id: str) -> dict[str, Any]:
        """Delete a conversation (soft delete)."""
        user_id = parse_uuid(user_id)
        conversation_id = parse_uuid(conversation_id)

        conversation = self.conv_repo.get_by_id(conversation_id)
        if not conversation or conversation.deleted_at:
            raise ValueError("Conversation not found")

        self._verify_conversation_membership(user_id, conversation_id)
        self._verify_organization_access(user_id, conversation.organization_id)

        # Only creator can delete
        if str(conversation.created_by) != str(user_id):
            raise PermissionError("Only the creator can delete this conversation")

        from datetime import datetime, timezone
        conversation.deleted_at = datetime.now(timezone.utc)
        self.conv_repo.update(conversation)
        db.session.commit()

        return {"message": "Conversation deleted"}

    def add_member(self, user_id: str, conversation_id: str, new_member_id: str) -> dict[str, Any]:
        """Add a member to a group conversation."""
        user_id = parse_uuid(user_id)
        conversation_id = parse_uuid(conversation_id)
        new_member_id = parse_uuid(new_member_id)

        conversation = self.conv_repo.get_by_id(conversation_id)
        if not conversation or conversation.deleted_at:
            raise ValueError("Conversation not found")

        self._verify_conversation_membership(user_id, conversation_id)
        self._verify_organization_access(user_id, conversation.organization_id)

        # Only allow adding members to group conversations
        if conversation.type != "group":
            raise PermissionError("Cannot add members to this conversation type")

        # Verify new member exists and is in the organization
        self._verify_organization_access(new_member_id, conversation.organization_id)

        # Check if already a member
        if self.member_repo.member_exists(conversation_id, new_member_id):
            raise ValueError("User is already a member of this conversation")

        member = ConversationMember(conversation_id=conversation_id, user_id=new_member_id)
        self.member_repo.create(member)
        db.session.commit()

        return member.to_dict()

    def remove_member(self, user_id: str, conversation_id: str, member_id: str) -> dict[str, Any]:
        """Remove a member from a group conversation."""
        user_id = parse_uuid(user_id)
        conversation_id = parse_uuid(conversation_id)
        member_id = parse_uuid(member_id)

        conversation = self.conv_repo.get_by_id(conversation_id)
        if not conversation or conversation.deleted_at:
            raise ValueError("Conversation not found")

        self._verify_conversation_membership(user_id, conversation_id)
        self._verify_organization_access(user_id, conversation.organization_id)

        # Only allow removing members from group conversations
        if conversation.type != "group":
            raise PermissionError("Cannot remove members from this conversation type")

        # Users can remove themselves, or only creator can remove others
        if member_id != user_id and str(conversation.created_by) != str(user_id):
            raise PermissionError("Only the creator can remove other members")

        member = self.member_repo.get_member(conversation_id, member_id)
        if not member:
            raise ValueError("Member not found")

        self.member_repo.delete(member)
        db.session.commit()

        return {"message": "Member removed"}

    def get_members(self, user_id: str, conversation_id: str) -> dict[str, Any]:
        """Get members of a conversation."""
        user_id = parse_uuid(user_id)
        conversation_id = parse_uuid(conversation_id)

        self._verify_conversation_membership(user_id, conversation_id)

        members = self.member_repo.list_members(conversation_id)
        return {
            "items": [
                {
                    **m.to_dict(),
                    "user": {
                        "id": str(m.user.id),
                        "username": m.user.username,
                        "full_name": m.user.full_name,
                        "avatar_url": m.user.avatar_url,
                    },
                }
                for m in members
            ],
            "count": len(members),
        }

    def _format_conversation(self, conversation: Conversation, requesting_user_id: uuid.UUID) -> dict[str, Any]:
        """Format a conversation for response."""
        members = self.member_repo.list_members(conversation.id)
        last_message = db.session.execute(
            db.select(Message)
            .where(
                (Message.conversation_id == conversation.id)
                & (Message.deleted_at.is_(None))
            )
            .order_by(Message.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()

        # Count unread messages for this user
        user_member = self.member_repo.get_member(conversation.id, requesting_user_id)
        unread_count = 0
        if user_member:
            unread_query = db.select(Message).where(
                (Message.conversation_id == conversation.id)
                & (Message.deleted_at.is_(None))
                & (Message.created_at > user_member.last_read_at if user_member.last_read_at else True)
            )
            unread_count = db.session.query(Message).filter(
                (Message.conversation_id == conversation.id)
                & (Message.deleted_at.is_(None))
                & (Message.created_at > user_member.last_read_at if user_member.last_read_at else True)
            ).count()

        return {
            **conversation.to_dict(),
            "members_count": len(members),
            "last_message": last_message.to_dict() if last_message else None,
            "unread_count": unread_count,
            "last_read_at": user_member.last_read_at.isoformat() if user_member and user_member.last_read_at else None,
        }

    # Message operations
    def send_message(self, user_id: str, conversation_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Send a message to a conversation."""
        user_id = parse_uuid(user_id)
        conversation_id = parse_uuid(conversation_id)

        self._verify_conversation_membership(user_id, conversation_id)

        conversation = self.conv_repo.get_by_id(conversation_id)
        if not conversation or conversation.deleted_at:
            raise ValueError("Conversation not found")

        self._verify_organization_access(user_id, conversation.organization_id)

        content = (payload.get("content") or "").strip()
        if not content:
            raise ValueError("Message content is required")

        if len(content) > 10000:
            raise ValueError("Message is too long (max 10000 characters)")

        message = Message(
            conversation_id=conversation_id,
            sender_id=user_id,
            content=content,
        )
        self.message_repo.create(message)

        # Update conversation's updated_at
        from datetime import datetime, timezone
        conversation.updated_at = datetime.now(timezone.utc)
        self.conv_repo.update(conversation)

        db.session.commit()

        # TODO: Send notifications to other members
        self._notify_new_message(message, conversation, user_id)

        return message.to_dict()

    def edit_message(self, user_id: str, message_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Edit a message (only the sender can edit)."""
        user_id = parse_uuid(user_id)
        message_id = parse_uuid(message_id)

        message = self.message_repo.get_by_id(message_id)
        if not message or message.deleted_at:
            raise ValueError("Message not found")

        if str(message.sender_id) != str(user_id):
            raise PermissionError("You can only edit your own messages")

        self._verify_conversation_membership(user_id, message.conversation_id)

        content = (payload.get("content") or "").strip()
        if not content:
            raise ValueError("Message content is required")

        if len(content) > 10000:
            raise ValueError("Message is too long (max 10000 characters)")

        message.content = content
        self.message_repo.update(message)
        db.session.commit()

        return message.to_dict()

    def delete_message(self, user_id: str, message_id: str) -> dict[str, Any]:
        """Soft delete a message (only the sender can delete)."""
        user_id = parse_uuid(user_id)
        message_id = parse_uuid(message_id)

        message = self.message_repo.get_by_id(message_id)
        if not message or message.deleted_at:
            raise ValueError("Message not found")

        if str(message.sender_id) != str(user_id):
            raise PermissionError("You can only delete your own messages")

        self._verify_conversation_membership(user_id, message.conversation_id)

        self.message_repo.soft_delete(message)
        db.session.commit()

        return {"message": "Message deleted"}

    def get_messages(self, user_id: str, conversation_id: str, limit: int = 50, offset: int = 0) -> dict[str, Any]:
        """Get messages for a conversation."""
        user_id = parse_uuid(user_id)
        conversation_id = parse_uuid(conversation_id)

        self._verify_conversation_membership(user_id, conversation_id)

        limit = max(1, min(limit, 100))  # Clamp between 1 and 100
        offset = max(0, offset)

        messages, total = self.message_repo.get_messages(conversation_id, limit, offset)

        return {
            "items": [m.to_dict() for m in messages],
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": total,
            },
        }

    def get_messages_after(self, user_id: str, conversation_id: str, after_message_id: str | None = None, limit: int = 50) -> dict[str, Any]:
        """Get new messages after a specific message (for polling)."""
        user_id = parse_uuid(user_id)
        conversation_id = parse_uuid(conversation_id)

        self._verify_conversation_membership(user_id, conversation_id)

        limit = max(1, min(limit, 100))

        messages = self.message_repo.get_messages_after(conversation_id, after_message_id, limit)

        return {
            "items": [m.to_dict() for m in messages],
            "has_more": len(messages) == limit,
        }

    def mark_as_read(self, user_id: str, conversation_id: str) -> dict[str, Any]:
        """Mark conversation as read."""
        user_id = parse_uuid(user_id)
        conversation_id = parse_uuid(conversation_id)

        self._verify_conversation_membership(user_id, conversation_id)

        member = self.member_repo.update_last_read(conversation_id, user_id)
        db.session.commit()

        return member.to_dict()

    def _notify_new_message(self, message: Message, conversation: Conversation, sender_id: uuid.UUID) -> None:
        """Send notifications to conversation members about new message."""
        members = self.member_repo.list_members(conversation.id)
        sender_user = self.user_repo.get_by_id(sender_id)

        for member in members:
            if str(member.user_id) != str(sender_id):
                # Prepare notification title based on conversation type
                if conversation.type == "direct":
                    title = f"New message from {sender_user.full_name}"
                    entity_type = "direct_message"
                elif conversation.type == "group":
                    title = f"New message in {conversation.name}"
                    entity_type = "group_message"
                elif conversation.type == "project":
                    title = f"New message in project"
                    entity_type = "project_message"
                elif conversation.type == "team":
                    title = f"New message in team"
                    entity_type = "team_message"
                else:
                    title = "New message"
                    entity_type = "message"

                # Create notification
                try:
                    self.notifications.create(
                        str(member.user_id),
                        "MESSAGE_RECEIVED",
                        title,
                        message.content[:100] if message.content else "",
                        entity_type,
                        str(message.id),
                        {"conversation_id": str(conversation.id)},
                    )
                except (ValueError, Exception):
                    # Continue even if notification fails
                    pass
