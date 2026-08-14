from datetime import date
from typing import Any

from backend.app import db
from backend.app.models.activity_log import ActivityLog
from backend.app.models.task import TASK_PRIORITIES, TASK_STATUSES, Subtask, Task
from backend.app.repositories.support_repositories import ActivityRepository, CommentRepository, FileRepository, NotificationRepository
from backend.app.repositories.task_repository import TaskRepository
from backend.app.services.support_services import NotificationService
from backend.app.services.rbac_service import RBACService
from backend.app.utils.uuid_helpers import parse_uuid


class TaskService:
    def __init__(self):
        self.repo = TaskRepository()
        self.rbac = RBACService()
        self.activity = ActivityRepository()
        self.notifications = NotificationService()

    @staticmethod
    def _parse_date(value: str | None) -> date | None:
        if not value:
            return None
        try:
            return date.fromisoformat(str(value)[:10])
        except ValueError as exc:
            raise ValueError("Invalid date format; use YYYY-MM-DD") from exc

    def _log(self, org_id, actor_id, action, entity_type, entity_id, metadata=None):
        self.activity.create(ActivityLog(
            organization_id=org_id,
            actor_id=parse_uuid(actor_id),
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            metadata_json=metadata or {},
        ))

    def _check_perm(self, user_id, org_id, perm):
        if not self.rbac.has_permission(user_id, perm, organization_id=org_id):
            raise PermissionError("Insufficient permissions")

    def _validated_assignee(self, organization_id, assignee_id):
        """Only active members of the task's organization can be assigned."""
        parsed = parse_uuid(assignee_id)
        if assignee_id and not parsed:
            raise ValueError("Invalid assignee")
        if parsed:
            self.rbac.require_org_membership(str(parsed), str(organization_id))
        return parsed

    @staticmethod
    def _calc_progress(task: Task) -> int:
        if not task.subtasks:
            return 100 if task.status == "DONE" else 0
        completed = sum(1 for s in task.subtasks if s.is_completed)
        return int((completed / len(task.subtasks)) * 100)

    def create_task(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        project_id = payload.get("project_id")
        if not project_id:
            raise ValueError("project_id is required")
        project = self.rbac.require_project_access(user_id, project_id)
        self._check_perm(user_id, project.organization_id, "task.create")

        title = (payload.get("title") or "").strip()
        if not title:
            raise ValueError("Title is required")

        status = (payload.get("status") or "BACKLOG").upper()
        if status not in TASK_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(TASK_STATUSES)}")

        priority = (payload.get("priority") or "MEDIUM").upper()
        if priority not in TASK_PRIORITIES:
            raise ValueError(f"Priority must be one of: {', '.join(TASK_PRIORITIES)}")

        kanban_order = self.repo.max_kanban_order(project_id, status) + 1
        task = Task(
            project_id=project.id,
            organization_id=project.organization_id,
            team_id=parse_uuid(payload.get("team_id")),
            title=title,
            description=(payload.get("description") or "").strip() or None,
            status=status,
            priority=priority,
            creator_id=parse_uuid(user_id),
            assignee_id=self._validated_assignee(project.organization_id, payload.get("assignee_id")),
            start_date=self._parse_date(payload.get("start_date")),
            due_date=self._parse_date(payload.get("due_date")),
            estimated_hours=payload.get("estimated_hours"),
            kanban_order=kanban_order,
        )
        self.repo.create(task)

        for tag_name in payload.get("tags") or []:
            tag = self.repo.get_or_create_tag(project.id, tag_name.strip())
            self.repo.add_tag_to_task(task.id, tag.id)

        if task.assignee_id:
            self.notifications.notify_task_assigned(task, str(task.assignee_id))

        self._log(project.organization_id, user_id, "task.created", "task", task.id, {"title": title})
        db.session.commit()
        return task.to_dict()

    def list_tasks(self, user_id: str, query_params: dict[str, Any]) -> dict[str, Any]:
        project_id = query_params.get("project_id")
        if not project_id:
            raise ValueError("project_id is required")
        project = self.rbac.require_project_access(user_id, project_id)

        page = max(int(query_params.get("page") or 1), 1)
        per_page = min(max(int(query_params.get("per_page") or 20), 1), 100)
        tasks, total = self.repo.list_for_project(
            project_id,
            status=query_params.get("status"),
            priority=query_params.get("priority"),
            assignee_id=query_params.get("assignee_id"),
            search=query_params.get("search"),
            sort_by=query_params.get("sort_by") or "kanban_order",
            sort_dir=query_params.get("sort_dir") or "asc",
            page=page,
            per_page=per_page,
        )
        return {
            "items": [t.to_dict() for t in tasks],
            "pagination": {"page": page, "per_page": per_page, "total": total, "pages": (total + per_page - 1) // per_page if total else 0},
        }

    def get_task(self, user_id: str, task_id: str) -> dict[str, Any]:
        task = self.repo.get_by_id(task_id)
        if not task:
            raise ValueError("Task not found")
        self.rbac.require_project_access(user_id, str(task.project_id))
        return task.to_dict(include_subtasks=True)

    def update_task(self, user_id: str, task_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        task = self.repo.get_by_id(task_id)
        if not task:
            raise ValueError("Task not found")
        project = self.rbac.require_project_access(user_id, str(task.project_id))
        self._check_perm(user_id, project.organization_id, "task.update")

        old_status = task.status
        if "title" in payload and payload.get("title"):
            task.title = payload["title"].strip()
        if "description" in payload:
            task.description = (payload.get("description") or "").strip() or None
        if "status" in payload and payload.get("status"):
            status = payload["status"].upper()
            if status not in TASK_STATUSES:
                raise ValueError(f"Invalid status")
            task.status = status
        if "priority" in payload and payload.get("priority"):
            priority = payload["priority"].upper()
            if priority not in TASK_PRIORITIES:
                raise ValueError(f"Invalid priority")
            task.priority = priority
        if "assignee_id" in payload:
            new_assignee = self._validated_assignee(project.organization_id, payload.get("assignee_id"))
            if new_assignee != task.assignee_id:
                task.assignee_id = new_assignee
                if new_assignee:
                    self.notifications.notify_task_assigned(task, str(new_assignee))
        if "start_date" in payload:
            task.start_date = self._parse_date(payload.get("start_date"))
        if "due_date" in payload:
            task.due_date = self._parse_date(payload.get("due_date"))
        if "estimated_hours" in payload:
            task.estimated_hours = payload.get("estimated_hours")
        if "actual_hours" in payload:
            task.actual_hours = payload.get("actual_hours")

        task.progress_percent = self._calc_progress(task)
        self.repo.update(task)

        if old_status != task.status:
            self.notifications.notify_status_changed(task)
            self._log(project.organization_id, user_id, "task.status_changed", "task", task.id, {"from": old_status, "to": task.status})

        self._log(project.organization_id, user_id, "task.updated", "task", task.id)
        db.session.commit()
        return task.to_dict()

    def delete_task(self, user_id: str, task_id: str) -> dict[str, Any]:
        task = self.repo.get_by_id(task_id)
        if not task:
            raise ValueError("Task not found")
        project = self.rbac.require_project_access(user_id, str(task.project_id))
        self._check_perm(user_id, project.organization_id, "task.delete")
        self.repo.delete(task)
        self._log(project.organization_id, user_id, "task.deleted", "task", task.id)
        db.session.commit()
        return {"message": "Task deleted"}

    def assign_task(self, user_id: str, task_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self.update_task(user_id, task_id, {"assignee_id": payload.get("assignee_id")})

    def create_subtask(self, user_id: str, task_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        task = self.repo.get_by_id(task_id)
        if not task:
            raise ValueError("Task not found")
        project = self.rbac.require_project_access(user_id, str(task.project_id))
        self._check_perm(user_id, project.organization_id, "task.update")

        title = (payload.get("title") or "").strip()
        if not title:
            raise ValueError("Title is required")

        subtask = Subtask(
            task_id=task.id,
            title=title,
            assignee_id=self._validated_assignee(project.organization_id, payload.get("assignee_id")),
            order_index=len(task.subtasks),
        )
        self.repo.create_subtask(subtask)
        task.progress_percent = self._calc_progress(task)
        self.repo.update(task)
        db.session.commit()
        return subtask.to_dict()

    def update_subtask(self, user_id: str, task_id: str, subtask_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        task = self.repo.get_by_id(task_id)
        if not task:
            raise ValueError("Task not found")
        project = self.rbac.require_project_access(user_id, str(task.project_id))
        self._check_perm(user_id, project.organization_id, "task.update")

        subtask = self.repo.get_subtask(subtask_id)
        if not subtask or subtask.task_id != task.id:
            raise ValueError("Subtask not found")

        if "title" in payload and payload.get("title"):
            subtask.title = payload["title"].strip()
        if "is_completed" in payload:
            subtask.is_completed = bool(payload["is_completed"])
        if "assignee_id" in payload:
            subtask.assignee_id = self._validated_assignee(project.organization_id, payload.get("assignee_id"))

        self.repo.update_subtask(subtask)
        task.progress_percent = self._calc_progress(task)
        self.repo.update(task)
        db.session.commit()
        return subtask.to_dict()

    def delete_subtask(self, user_id: str, task_id: str, subtask_id: str) -> dict[str, Any]:
        task = self.repo.get_by_id(task_id)
        if not task:
            raise ValueError("Task not found")
        project = self.rbac.require_project_access(user_id, str(task.project_id))
        self._check_perm(user_id, project.organization_id, "task.update")

        subtask = self.repo.get_subtask(subtask_id)
        if not subtask or subtask.task_id != task.id:
            raise ValueError("Subtask not found")
        self.repo.delete_subtask(subtask)
        task.progress_percent = self._calc_progress(task)
        self.repo.update(task)
        db.session.commit()
        return {"message": "Subtask deleted"}

    def get_kanban_board(self, user_id: str, project_id: str) -> dict[str, Any]:
        self.rbac.require_project_access(user_id, project_id)
        board = {}
        for status in TASK_STATUSES:
            tasks = self.repo.list_by_status(project_id, status)
            board[status] = [t.to_dict() for t in tasks]
        return board

    def move_task(self, user_id: str, task_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        task = self.repo.get_by_id(task_id)
        if not task:
            raise ValueError("Task not found")
        project = self.rbac.require_project_access(user_id, str(task.project_id))
        self._check_perm(user_id, project.organization_id, "task.update")

        new_status = (payload.get("status") or task.status).upper()
        new_order = int(payload.get("kanban_order", task.kanban_order))

        if new_status not in TASK_STATUSES:
            raise ValueError("Invalid status")

        old_status = task.status
        if new_status != old_status:
            task.status = new_status

        column_tasks = self.repo.list_by_status(str(task.project_id), new_status)
        column_tasks = [t for t in column_tasks if t.id != task.id]
        column_tasks.insert(min(new_order, len(column_tasks)), task)
        for idx, t in enumerate(column_tasks):
            t.kanban_order = idx
            self.repo.update(t)

        if old_status != new_status:
            self.notifications.notify_status_changed(task)

        db.session.commit()
        return task.to_dict()

    def bulk_reorder(self, user_id: str, project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.rbac.require_project_access(user_id, project_id)
        project = self.rbac.require_project_access(user_id, project_id)
        self._check_perm(user_id, project.organization_id, "task.update")

        for item in payload.get("items") or []:
            task = self.repo.get_by_id(item.get("task_id"))
            if task and str(task.project_id) == project_id:
                if item.get("status"):
                    task.status = item["status"].upper()
                if "kanban_order" in item:
                    task.kanban_order = int(item["kanban_order"])
                self.repo.update(task)

        db.session.commit()
        return self.get_kanban_board(user_id, project_id)
