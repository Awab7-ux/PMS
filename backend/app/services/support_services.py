import re
from typing import Any

from backend.app import db
from backend.app.models.activity_log import ActivityLog
from backend.app.models.comment import Comment
from backend.app.models.notification import NOTIFICATION_TYPES, Notification
from backend.app.repositories.support_repositories import ActivityRepository, CommentRepository, NotificationRepository
from backend.app.repositories.task_repository import TaskRepository
from backend.app.services.rbac_service import RBACService
from backend.app.services.realtime_service import RealtimeService
from backend.app.utils.uuid_helpers import parse_uuid


class NotificationService:
    def __init__(self):
        self.repo = NotificationRepository()

    def create(self, user_id: str, event_type: str, title: str, message: str | None = None, entity_type: str | None = None, entity_id: str | None = None, metadata: dict | None = None) -> Notification:
        recipient_id = parse_uuid(user_id)
        if not recipient_id:
            raise ValueError("Invalid notification recipient")
        if event_type not in NOTIFICATION_TYPES:
            raise ValueError("Invalid notification type")
        if self.repo.exists(recipient_id, event_type, entity_type, entity_id):
            return None
        notification = Notification(
            user_id=recipient_id,
            event_type=event_type,
            title=title,
            message=message,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata_json=metadata or {},
        )
        self.repo.create(notification)
        RealtimeService.notify_notification(str(recipient_id), notification.to_dict())
        return notification

    def notify_task_assigned(self, task, assignee_id: str, actor_id: str | None = None) -> None:
        if str(assignee_id) == str(actor_id):
            return
        self.create(
            assignee_id,
            "TASK_ASSIGNED",
            "You were assigned a task",
            task.title,
            "task",
            str(task.id),
        )

    def notify_status_changed(self, task, actor_id: str | None = None) -> None:
        recipients = {str(user_id) for user_id in (task.creator_id, task.assignee_id) if user_id and str(user_id) != str(actor_id)}
        for recipient_id in recipients:
            self.create(recipient_id, "TASK_STATUS_CHANGED", "Task status changed", f"{task.title} is now {task.status}", "task", str(task.id))

    def notify_comment(self, task, comment, mentioned_ids: list[str], actor_id: str) -> None:
        participants = {str(user_id) for user_id in (task.creator_id, task.assignee_id) if user_id and str(user_id) != str(actor_id)}
        mentioned = {str(user_id) for user_id in mentioned_ids if str(user_id) != str(actor_id)}
        for recipient_id in participants:
            event_type = "TASK_MENTIONED" if recipient_id in mentioned else "TASK_COMMENTED"
            title = "You were mentioned in a task" if event_type == "TASK_MENTIONED" else "New comment on a task"
            self.create(recipient_id, event_type, title, comment.content[:100], "task", str(task.id))
        for recipient_id in mentioned - participants:
            self.create(recipient_id, "TASK_MENTIONED", "You were mentioned in a task", comment.content[:100], "task", str(task.id))

    def notify_project_added(self, project, user_id: str, actor_id: str) -> None:
        if str(user_id) != str(actor_id):
            self.create(user_id, "PROJECT_ADDED", "You were added to a project", project.name, "project", str(project.id))

    def notify_team_added(self, team, user_id: str, actor_id: str) -> None:
        if str(user_id) != str(actor_id):
            self.create(user_id, "TEAM_ADDED", "You were added to a team", team.name, "team", str(team.id))

    def notify_team_member_removed(self, user_id: str, actor_id: str, team) -> None:
        if str(user_id) != str(actor_id): self.create(user_id, "TEAM_MEMBER_REMOVED", "You were removed from a team", team.name, "team", str(team.id))

    def notify_organization_role_changed(self, user_id, actor_id, role, organization_id) -> None:
        if str(user_id) != str(actor_id): self.create(user_id, "ORGANIZATION_ROLE_CHANGED", "Your organization role changed", f"Your role is now {role}", "organization", str(organization_id))

    def notify_organization_member_removed(self, user_id, actor_id, organization_id) -> None:
        if str(user_id) != str(actor_id): self.create(user_id, "ORGANIZATION_MEMBER_REMOVED", "You were removed from an organization", None, "organization", str(organization_id))

    def list_notifications(self, user_id: str, query_params: dict[str, Any]) -> dict[str, Any]:
        page = max(int(query_params.get("page") or 1), 1)
        per_page = min(max(int(query_params.get("per_page") or 20), 1), 100)
        unread_only = query_params.get("unread_only", "").lower() == "true"
        items, total = self.repo.list_for_user(user_id, unread_only, page, per_page)
        return {
            "items": [n.to_dict() for n in items],
            "unread_count": self.repo.count_unread(user_id),
            "pagination": {"page": page, "per_page": per_page, "total": total, "pages": (total + per_page - 1) // per_page if total else 0},
        }

    def mark_read(self, user_id: str, notification_id: str) -> dict[str, Any]:
        notification = self.repo.get_by_id(notification_id)
        if not notification or str(notification.user_id) != str(user_id):
            raise ValueError("Notification not found")
        self.repo.mark_read(notification)
        db.session.commit()
        return notification.to_dict()

    def mark_all_read(self, user_id: str) -> dict[str, Any]:
        count = self.repo.mark_all_read(user_id)
        db.session.commit()
        return {"message": f"{count} notifications marked as read"}

    def delete_notification(self, user_id: str, notification_id: str) -> dict[str, Any]:
        notification = self.repo.get_by_id(notification_id)
        if not notification or str(notification.user_id) != str(user_id):
            raise ValueError("Notification not found")
        self.repo.delete(notification)
        db.session.commit()
        return {"message": "Notification deleted"}


class CommentService:
    MENTION_PATTERN = re.compile(r"@(\w+)")

    def __init__(self):
        self.repo = CommentRepository()
        self.task_repo = TaskRepository()
        self.rbac = RBACService()
        self.notifications = NotificationService()
        self.activity = ActivityRepository()

    def _extract_mentions(self, content: str, organization_id: str) -> list[str]:
        from backend.app.repositories.user_repository import UserRepository
        user_repo = UserRepository()
        mentioned_ids = []
        for match in self.MENTION_PATTERN.findall(content):
            user = user_repo.get_by_username(match)
            membership = self.rbac.org_repo.get_membership(organization_id, user.id) if user else None
            if membership and membership.status == "active":
                mentioned_ids.append(str(user.id))
        return mentioned_ids

    def create_comment(self, user_id: str, task_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        task = self.task_repo.get_by_id(task_id)
        if not task:
            raise ValueError("Task not found")
        project = self.rbac.require_project_access(user_id, str(task.project_id))
        if not self.rbac.has_permission(user_id, "comment.create", organization_id=project.organization_id):
            raise PermissionError("Insufficient permissions")

        content = (payload.get("content") or "").strip()
        if not content:
            raise ValueError("Content is required")

        comment = Comment(task_id=task.id, author_id=parse_uuid(user_id), content=content)
        mentions = self._extract_mentions(content, project.organization_id)
        comment.mentions = mentions
        self.repo.create(comment)

        self.notifications.notify_comment(task, comment, mentions, user_id)
        self.activity.create(ActivityLog(
            organization_id=project.organization_id,
            actor_id=parse_uuid(user_id),
            action="comment.created",
            entity_type="comment",
            entity_id=str(comment.id),
        ))
        db.session.commit()
        result = comment.to_dict()
        RealtimeService.notify_comment(str(task.id), result)
        RealtimeService.publish(f"project:{project.id}", "comment.created", result)
        return result

    def list_comments(self, user_id: str, task_id: str) -> list[dict[str, Any]]:
        task = self.task_repo.get_by_id(task_id)
        if not task:
            raise ValueError("Task not found")
        self.rbac.require_project_access(user_id, str(task.project_id))
        return [c.to_dict() for c in self.repo.list_for_task(task_id)]

    def update_comment(self, user_id: str, comment_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        comment = self.repo.get_by_id(comment_id)
        if not comment:
            raise ValueError("Comment not found")
        task = self.task_repo.get_by_id(str(comment.task_id))
        project = self.rbac.require_project_access(user_id, str(task.project_id))

        is_author = str(comment.author_id) == str(user_id)
        can_admin = self.rbac.has_permission(user_id, "comment.update", organization_id=project.organization_id)
        if not is_author and not can_admin:
            raise PermissionError("Insufficient permissions")

        content = (payload.get("content") or "").strip()
        if not content:
            raise ValueError("Content is required")
        comment.content = content
        comment.mentions = self._extract_mentions(content, project.organization_id)
        self.repo.update(comment)
        db.session.commit()
        result = comment.to_dict()
        RealtimeService.publish(f"task:{task.id}", "comment.updated", result)
        return result

    def delete_comment(self, user_id: str, comment_id: str) -> dict[str, Any]:
        comment = self.repo.get_by_id(comment_id)
        if not comment:
            raise ValueError("Comment not found")
        task = self.task_repo.get_by_id(str(comment.task_id))
        project = self.rbac.require_project_access(user_id, str(task.project_id))

        is_author = str(comment.author_id) == str(user_id)
        can_admin = self.rbac.has_permission(user_id, "comment.delete", organization_id=project.organization_id)
        if not is_author and not can_admin:
            raise PermissionError("Insufficient permissions")

        self.repo.delete(comment)
        db.session.commit()
        RealtimeService.publish(f"task:{task.id}", "comment.deleted", {"comment_id": str(comment.id), "task_id": str(task.id)})
        return {"message": "Comment deleted"}
