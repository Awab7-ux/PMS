import uuid
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import func, or_

from backend.app import db
from backend.app.models.task import Subtask, Task, TaskTag, TaskTagAssociation


class TaskRepository:
    def create(self, task: Task) -> Task:
        db.session.add(task)
        db.session.flush()
        return task

    def update(self, task: Task) -> Task:
        task.updated_at = datetime.now(timezone.utc)
        db.session.flush()
        return task

    def delete(self, task: Task) -> None:
        task.deleted_at = datetime.now(timezone.utc)
        db.session.flush()

    def get_by_id(self, task_id: str | uuid.UUID | None) -> Optional[Task]:
        if not task_id:
            return None
        try:
            parsed = uuid.UUID(str(task_id))
        except (ValueError, TypeError):
            return None
        task = db.session.get(Task, parsed)
        if task and task.deleted_at is not None:
            return None
        return task

    def list_for_project(
        self,
        project_id: str | uuid.UUID,
        status: str | None = None,
        priority: str | None = None,
        assignee_id: str | None = None,
        due_date: date | None = None,
        search: str | None = None,
        sort_by: str = "kanban_order",
        sort_dir: str = "asc",
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Task], int]:
        try:
            parsed = uuid.UUID(str(project_id))
        except (ValueError, TypeError):
            return [], 0

        query = db.select(Task).where(Task.project_id == parsed, Task.deleted_at.is_(None))
        if status:
            query = query.where(Task.status == status)
        if priority:
            query = query.where(Task.priority == priority)
        if assignee_id:
            try:
                query = query.where(Task.assignee_id == uuid.UUID(str(assignee_id)))
            except (ValueError, TypeError):
                pass
        if due_date:
            query = query.where(Task.due_date == due_date)
        if search:
            term = f"%{search.strip()}%"
            query = query.where(or_(Task.title.ilike(term), Task.description.ilike(term)))

        sortable_columns = {
            "kanban_order": Task.kanban_order,
            "due_date": Task.due_date,
            "created_at": Task.created_at,
            "updated_at": Task.updated_at,
            "priority": Task.priority,
            "title": Task.title,
        }
        sort_col = sortable_columns.get(sort_by, Task.kanban_order)
        query = query.order_by(sort_col.desc() if sort_dir == "desc" else sort_col.asc())

        all_tasks = db.session.execute(query).scalars().all()
        total = len(all_tasks)
        offset = (page - 1) * per_page
        return all_tasks[offset : offset + per_page], total

    def list_by_status(self, project_id: str | uuid.UUID, status: str) -> list[Task]:
        try:
            parsed = uuid.UUID(str(project_id))
        except (ValueError, TypeError):
            return []
        return db.session.execute(
            db.select(Task)
            .where(Task.project_id == parsed, Task.status == status, Task.deleted_at.is_(None))
            .order_by(Task.kanban_order.asc())
        ).scalars().all()

    def max_kanban_order(self, project_id: str | uuid.UUID, status: str) -> int:
        tasks = self.list_by_status(project_id, status)
        return max((t.kanban_order for t in tasks), default=-1)

    def create_subtask(self, subtask: Subtask) -> Subtask:
        db.session.add(subtask)
        db.session.flush()
        return subtask

    def get_subtask(self, subtask_id: str | uuid.UUID) -> Optional[Subtask]:
        try:
            parsed = uuid.UUID(str(subtask_id))
        except (ValueError, TypeError):
            return None
        return db.session.get(Subtask, parsed)

    def update_subtask(self, subtask: Subtask) -> Subtask:
        subtask.updated_at = datetime.now(timezone.utc)
        db.session.flush()
        return subtask

    def delete_subtask(self, subtask: Subtask) -> None:
        db.session.delete(subtask)
        db.session.flush()

    def get_or_create_tag(self, project_id: uuid.UUID, name: str, color: str | None = None) -> TaskTag:
        tag = db.session.execute(
            db.select(TaskTag).where(TaskTag.project_id == project_id, TaskTag.name == name)
        ).scalar_one_or_none()
        if not tag:
            tag = TaskTag(project_id=project_id, name=name, color=color)
            db.session.add(tag)
            db.session.flush()
        return tag

    def add_tag_to_task(self, task_id: uuid.UUID, tag_id: uuid.UUID) -> None:
        existing = db.session.execute(
            db.select(TaskTagAssociation).where(
                TaskTagAssociation.task_id == task_id,
                TaskTagAssociation.tag_id == tag_id,
            )
        ).scalar_one_or_none()
        if not existing:
            db.session.add(TaskTagAssociation(task_id=task_id, tag_id=tag_id))
            db.session.flush()

    def list_overdue(self, organization_id: str | uuid.UUID) -> list[Task]:
        try:
            parsed = uuid.UUID(str(organization_id))
        except (ValueError, TypeError):
            return []
        today = date.today()
        return db.session.execute(
            db.select(Task).where(
                Task.organization_id == parsed,
                Task.due_date < today,
                Task.status != "DONE",
                Task.deleted_at.is_(None),
            )
        ).scalars().all()

    def count_by_status(self, organization_id: str | uuid.UUID) -> dict[str, int]:
        try:
            parsed = uuid.UUID(str(organization_id))
        except (ValueError, TypeError):
            return {}
        from sqlalchemy import func
        rows = db.session.execute(
            db.select(Task.status, func.count(Task.id))
            .where(Task.organization_id == parsed, Task.deleted_at.is_(None))
            .group_by(Task.status)
        ).all()
        return {status: count for status, count in rows}

    def count_by_priority(self, organization_id: str | uuid.UUID) -> dict[str, int]:
        try:
            parsed = uuid.UUID(str(organization_id))
        except (ValueError, TypeError):
            return {}
        from sqlalchemy import func
        rows = db.session.execute(
            db.select(Task.priority, func.count(Task.id))
            .where(Task.organization_id == parsed, Task.deleted_at.is_(None))
            .group_by(Task.priority)
        ).all()
        return {priority: count for priority, count in rows}
