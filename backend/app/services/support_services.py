import re
from typing import Any

from backend.app import db
from backend.app.models.activity_log import ActivityLog
from backend.app.models.comment import Comment
from backend.app.models.notification import Notification
from backend.app.repositories.support_repositories import ActivityRepository, CommentRepository, NotificationRepository
from backend.app.repositories.task_repository import TaskRepository
from backend.app.services.rbac_service import RBACService
from backend.app.utils.uuid_helpers import parse_uuid


class NotificationService:
    def __init__(self):
        self.repo = NotificationRepository()

    def create(self, user_id: str, event_type: str, title: str, message: str | None = None, entity_type: str | None = None, entity_id: str | None = None, metadata: dict | None = None) -> Notification:
        notification = Notification(
            user_id=parse_uuid(user_id),
            event_type=event_type,
            title=title,
            message=message,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata_json=metadata or {},
        )
        self.repo.create(notification)
        return notification

    def notify_task_assigned(self, task, assignee_id: str) -> None:
        self.create(
            assignee_id,
            "task.assigned",
            f"Task assigned: {task.title}",
            f"You have been assigned to task '{task.title}'",
            "task",
            str(task.id),
        )

    def notify_status_changed(self, task) -> None:
        if task.assignee_id:
            self.create(
                str(task.assignee_id),
                "task.status_changed",
                f"Task status changed: {task.title}",
                f"Status changed to {task.status}",
                "task",
                str(task.id),
            )

    def notify_comment(self, task, comment, mentioned_ids: list[str]) -> None:
        if task.assignee_id:
            self.create(
                str(task.assignee_id),
                "comment.added",
                f"New comment on: {task.title}",
                comment.content[:100],
                "task",
                str(task.id),
            )
        for uid in mentioned_ids:
            self.create(uid, "mention", f"You were mentioned in {task.title}", comment.content[:100], "comment", str(comment.id))

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

    def _extract_mentions(self, content: str) -> list[str]:
        from backend.app.repositories.user_repository import UserRepository
        user_repo = UserRepository()
        mentioned_ids = []
        for match in self.MENTION_PATTERN.findall(content):
            user = user_repo.get_by_username(match)
            if user:
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
        mentions = self._extract_mentions(content)
        comment.mentions = mentions
        self.repo.create(comment)

        self.notifications.notify_comment(task, comment, mentions)
        self.activity.create(ActivityLog(
            organization_id=project.organization_id,
            actor_id=parse_uuid(user_id),
            action="comment.created",
            entity_type="comment",
            entity_id=str(comment.id),
        ))
        db.session.commit()
        return comment.to_dict()

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
        comment.mentions = self._extract_mentions(content)
        self.repo.update(comment)
        db.session.commit()
        return comment.to_dict()

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
        return {"message": "Comment deleted"}
