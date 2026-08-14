import mimetypes
import os
import uuid
from typing import Any

from werkzeug.utils import secure_filename

from backend.app import db
from backend.app.models.activity_log import ActivityLog
from backend.app.models.file_attachment import FileAttachment
from backend.app.repositories.support_repositories import ActivityRepository, CommentRepository, FileRepository
from backend.app.repositories.task_repository import TaskRepository
from backend.app.services.rbac_service import RBACService
from backend.app.storage.local_storage import get_storage
from backend.app.utils.uuid_helpers import parse_uuid

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".doc", ".docx", ".xls", ".xlsx", ".txt", ".csv", ".zip"}
BLOCKED_EXTENSIONS = {".exe", ".bat", ".cmd", ".sh", ".ps1", ".msi", ".dll", ".scr"}
MAX_FILE_SIZE = int(os.getenv("MAX_UPLOAD_SIZE_MB", "25")) * 1024 * 1024


class FileService:
    def __init__(self):
        self.repo = FileRepository()
        self.task_repo = TaskRepository()
        self.comment_repo = CommentRepository()
        self.rbac = RBACService()
        self.activity = ActivityRepository()
        self.storage = get_storage()

    def _validate_file(self, filename: str, file_data: bytes) -> str:
        if len(file_data) > MAX_FILE_SIZE:
            raise ValueError(f"File exceeds maximum size of {MAX_FILE_SIZE // (1024*1024)}MB")
        safe_name = secure_filename(filename)
        if not safe_name:
            raise ValueError("Invalid filename")
        ext = os.path.splitext(safe_name)[1].lower()
        if ext in BLOCKED_EXTENSIONS:
            raise ValueError("File type not allowed")
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"File extension {ext} not allowed")
        mime = mimetypes.guess_type(safe_name)[0] or "application/octet-stream"
        if mime.startswith("application/x-") and ext not in ALLOWED_EXTENSIONS:
            raise ValueError("Suspicious file type")
        return mime

    def upload(self, user_id: str, file_data: bytes, filename: str, task_id: str | None = None, project_id: str | None = None, comment_id: str | None = None) -> dict[str, Any]:
        mime = self._validate_file(filename, file_data)
        org_id = None

        if sum(bool(value) for value in (task_id, project_id, comment_id)) != 1:
            raise ValueError("Exactly one attachment parent is required")
        if comment_id:
            comment = self.comment_repo.get_by_id(comment_id)
            if not comment: raise ValueError("Comment not found")
            task = self.task_repo.get_by_id(str(comment.task_id))
            project = self.rbac.require_project_access(user_id, str(task.project_id))
            org_id = project.organization_id
            if not self.rbac.has_permission(user_id, "file.upload", organization_id=org_id): raise PermissionError("Insufficient permissions")
            task_id = None; project_id = None
        elif task_id:
            task = self.task_repo.get_by_id(task_id)
            if not task:
                raise ValueError("Task not found")
            project = self.rbac.require_project_access(user_id, str(task.project_id))
            org_id = project.organization_id
            if not self.rbac.has_permission(user_id, "file.upload", organization_id=org_id):
                raise PermissionError("Insufficient permissions")
            project_id = str(task.project_id)
        elif project_id:
            project = self.rbac.require_project_access(user_id, project_id)
            org_id = project.organization_id
            if not self.rbac.has_permission(user_id, "file.upload", organization_id=org_id):
                raise PermissionError("Insufficient permissions")
        else:
            raise ValueError("task_id or project_id is required")

        stored_filename = f"{uuid.uuid4().hex}{os.path.splitext(secure_filename(filename))[1].lower()}"
        storage_path = self.storage.save(file_data, stored_filename)

        attachment = FileAttachment(
            task_id=parse_uuid(task_id) if task_id else None,
            project_id=parse_uuid(project_id) if project_id else None,
            comment_id=parse_uuid(comment_id) if comment_id else None,
            uploader_id=parse_uuid(user_id),
            original_filename=secure_filename(filename),
            stored_filename=stored_filename,
            mime_type=mime,
            file_size=len(file_data),
            storage_path=storage_path,
        )
        self.repo.create(attachment)
        self.activity.create(ActivityLog(
            organization_id=org_id,
            actor_id=parse_uuid(user_id),
            action="file.uploaded",
            entity_type="file",
            entity_id=str(attachment.id),
            metadata_json={"filename": attachment.original_filename},
        ))
        db.session.commit()
        return attachment.to_dict()

    def list_files(self, user_id: str, task_id: str | None = None, project_id: str | None = None, comment_id: str | None = None) -> list[dict[str, Any]]:
        if comment_id:
            comment = self.comment_repo.get_by_id(comment_id)
            if not comment: raise ValueError("Comment not found")
            task = self.task_repo.get_by_id(str(comment.task_id)); self.rbac.require_project_access(user_id, str(task.project_id))
            return [f.to_dict() for f in self.repo.list_for_comment(comment_id)]
        if task_id:
            task = self.task_repo.get_by_id(task_id)
            if not task:
                raise ValueError("Task not found")
            self.rbac.require_project_access(user_id, str(task.project_id))
            return [f.to_dict() for f in self.repo.list_for_task(task_id)]
        if project_id:
            self.rbac.require_project_access(user_id, project_id)
            return [f.to_dict() for f in self.repo.list_for_project(project_id)]
        raise ValueError("task_id or project_id is required")

    def download(self, user_id: str, file_id: str) -> tuple[bytes, str, str]:
        attachment = self.repo.get_by_id(file_id)
        if not attachment:
            raise ValueError("File not found")
        if attachment.comment_id:
            comment = self.comment_repo.get_by_id(str(attachment.comment_id)); task = self.task_repo.get_by_id(str(comment.task_id)); self.rbac.require_project_access(user_id, str(task.project_id))
        elif attachment.task_id:
            task = self.task_repo.get_by_id(str(attachment.task_id))
            self.rbac.require_project_access(user_id, str(task.project_id))
        elif attachment.project_id:
            self.rbac.require_project_access(user_id, str(attachment.project_id))
        else:
            raise ValueError("File not found")
        data = self.storage.read(attachment.storage_path)
        return data, attachment.mime_type, attachment.original_filename

    def delete_file(self, user_id: str, file_id: str) -> dict[str, Any]:
        attachment = self.repo.get_by_id(file_id)
        if not attachment:
            raise ValueError("File not found")
        org_id = None
        if attachment.comment_id:
            comment = self.comment_repo.get_by_id(str(attachment.comment_id)); task = self.task_repo.get_by_id(str(comment.task_id)); project = self.rbac.require_project_access(user_id, str(task.project_id)); org_id = project.organization_id
        elif attachment.task_id:
            task = self.task_repo.get_by_id(str(attachment.task_id))
            project = self.rbac.require_project_access(user_id, str(task.project_id))
            org_id = project.organization_id
        elif attachment.project_id:
            project = self.rbac.require_project_access(user_id, str(attachment.project_id))
            org_id = project.organization_id

        if not self.rbac.has_permission(user_id, "file.delete", organization_id=org_id):
            if str(attachment.uploader_id) != str(user_id):
                raise PermissionError("Insufficient permissions")

        try:
            self.storage.delete(attachment.storage_path)
        except (ValueError, OSError):
            pass
        self.repo.delete(attachment)
        db.session.commit()
        return {"message": "File deleted"}
