import uuid
from datetime import date, datetime, timezone
from typing import Any, Optional

from backend.app import db
from backend.app.models.comment import Comment
from backend.app.models.file_attachment import FileAttachment
from backend.app.models.notification import Notification
from backend.app.models.activity_log import ActivityLog


class CommentRepository:
    def create(self, comment: Comment) -> Comment:
        db.session.add(comment)
        db.session.flush()
        return comment

    def get_by_id(self, comment_id: str | uuid.UUID) -> Optional[Comment]:
        try:
            parsed = uuid.UUID(str(comment_id))
        except (ValueError, TypeError):
            return None
        comment = db.session.get(Comment, parsed)
        if comment and comment.deleted_at is not None:
            return None
        return comment

    def list_for_task(self, task_id: str | uuid.UUID) -> list[Comment]:
        try:
            parsed = uuid.UUID(str(task_id))
        except (ValueError, TypeError):
            return []
        return db.session.execute(
            db.select(Comment)
            .where(Comment.task_id == parsed, Comment.deleted_at.is_(None))
            .order_by(Comment.created_at.asc())
        ).scalars().all()

    def update(self, comment: Comment) -> Comment:
        comment.updated_at = datetime.now(timezone.utc)
        db.session.flush()
        return comment

    def delete(self, comment: Comment) -> None:
        comment.deleted_at = datetime.now(timezone.utc)
        db.session.flush()


class FileRepository:
    def create(self, attachment: FileAttachment) -> FileAttachment:
        db.session.add(attachment)
        db.session.flush()
        return attachment

    def get_by_id(self, file_id: str | uuid.UUID) -> Optional[FileAttachment]:
        try:
            parsed = uuid.UUID(str(file_id))
        except (ValueError, TypeError):
            return None
        attachment = db.session.get(FileAttachment, parsed)
        if attachment and attachment.deleted_at is not None:
            return None
        return attachment

    def list_for_task(self, task_id: str | uuid.UUID) -> list[FileAttachment]:
        try:
            parsed = uuid.UUID(str(task_id))
        except (ValueError, TypeError):
            return []
        return db.session.execute(
            db.select(FileAttachment).where(
                FileAttachment.task_id == parsed,
                FileAttachment.deleted_at.is_(None),
            )
        ).scalars().all()

    def list_for_project(self, project_id: str | uuid.UUID) -> list[FileAttachment]:
        try:
            parsed = uuid.UUID(str(project_id))
        except (ValueError, TypeError):
            return []
        return db.session.execute(
            db.select(FileAttachment).where(
                FileAttachment.project_id == parsed,
                FileAttachment.deleted_at.is_(None),
            )
        ).scalars().all()

    def delete(self, attachment: FileAttachment) -> None:
        attachment.deleted_at = datetime.now(timezone.utc)
        db.session.flush()


class NotificationRepository:
    def create(self, notification: Notification) -> Notification:
        db.session.add(notification)
        db.session.flush()
        return notification

    def list_for_user(self, user_id: str | uuid.UUID, unread_only: bool = False, page: int = 1, per_page: int = 20) -> tuple[list[Notification], int]:
        try:
            parsed = uuid.UUID(str(user_id))
        except (ValueError, TypeError):
            return [], 0
        query = db.select(Notification).where(Notification.user_id == parsed)
        if unread_only:
            query = query.where(Notification.is_read.is_(False))
        query = query.order_by(Notification.created_at.desc())
        all_items = db.session.execute(query).scalars().all()
        total = len(all_items)
        offset = (page - 1) * per_page
        return all_items[offset : offset + per_page], total

    def count_unread(self, user_id: str | uuid.UUID) -> int:
        try:
            parsed = uuid.UUID(str(user_id))
        except (ValueError, TypeError):
            return 0
        return db.session.execute(
            db.select(db.func.count(Notification.id)).where(
                Notification.user_id == parsed,
                Notification.is_read.is_(False),
            )
        ).scalar() or 0

    def get_by_id(self, notification_id: str | uuid.UUID) -> Optional[Notification]:
        try:
            parsed = uuid.UUID(str(notification_id))
        except (ValueError, TypeError):
            return None
        return db.session.get(Notification, parsed)

    def mark_read(self, notification: Notification) -> None:
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        db.session.flush()

    def mark_all_read(self, user_id: str | uuid.UUID) -> int:
        try:
            parsed = uuid.UUID(str(user_id))
        except (ValueError, TypeError):
            return 0
        items = db.session.execute(
            db.select(Notification).where(Notification.user_id == parsed, Notification.is_read.is_(False))
        ).scalars().all()
        for item in items:
            item.is_read = True
            item.read_at = datetime.now(timezone.utc)
        db.session.flush()
        return len(items)

    def delete(self, notification: Notification) -> None:
        db.session.delete(notification)
        db.session.flush()


class ActivityRepository:
    def create(self, log: ActivityLog) -> ActivityLog:
        db.session.add(log)
        db.session.flush()
        return log

    def list(
        self,
        organization_id: str | uuid.UUID | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> tuple[list[ActivityLog], int]:
        query = db.select(ActivityLog)
        if organization_id:
            try:
                parsed = uuid.UUID(str(organization_id))
                query = query.where(ActivityLog.organization_id == parsed)
            except (ValueError, TypeError):
                return [], 0
        if entity_type:
            query = query.where(ActivityLog.entity_type == entity_type)
        if entity_id:
            query = query.where(ActivityLog.entity_id == entity_id)
        query = query.order_by(ActivityLog.created_at.desc())
        all_items = db.session.execute(query).scalars().all()
        total = len(all_items)
        offset = (page - 1) * per_page
        return all_items[offset : offset + per_page], total
