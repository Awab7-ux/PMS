from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import func

from backend.app import db
from backend.app.models.project import Project
from backend.app.models.task import Task
from backend.app.models.team import Team, TeamMembership
from backend.app.repositories.project_repository import ProjectRepository
from backend.app.repositories.task_repository import TaskRepository
from backend.app.services.rbac_service import RBACService
from backend.app.repositories.support_repositories import ActivityRepository


class ReportService:
    def __init__(self):
        self.project_repo = ProjectRepository()
        self.task_repo = TaskRepository()
        self.rbac = RBACService()
        self.activity = ActivityRepository()

    def get_analytics(self, user_id: str, organization_id: str) -> dict[str, Any]:
        self.rbac.require_org_membership(user_id, organization_id)
        perms = self.rbac.get_user_permissions(user_id, organization_id)
        if "report.view" not in perms:
            user_perms = perms
            if not user_perms:
                raise PermissionError("Insufficient permissions")

        import uuid
        try:
            parsed = uuid.UUID(str(organization_id))
        except (ValueError, TypeError):
            raise ValueError("Invalid organization")

        total_projects = db.session.execute(
            db.select(func.count(Project.id)).where(
                Project.organization_id == parsed, Project.deleted_at.is_(None)
            )
        ).scalar() or 0

        active_projects = db.session.execute(
            db.select(func.count(Project.id)).where(
                Project.organization_id == parsed,
                Project.status == "Active",
                Project.deleted_at.is_(None),
            )
        ).scalar() or 0

        completed_projects = db.session.execute(
            db.select(func.count(Project.id)).where(
                Project.organization_id == parsed,
                Project.status == "Completed",
                Project.deleted_at.is_(None),
            )
        ).scalar() or 0

        total_tasks = db.session.execute(
            db.select(func.count(Task.id)).where(
                Task.organization_id == parsed, Task.deleted_at.is_(None)
            )
        ).scalar() or 0

        completed_tasks = db.session.execute(
            db.select(func.count(Task.id)).where(
                Task.organization_id == parsed,
                Task.status == "DONE",
                Task.deleted_at.is_(None),
            )
        ).scalar() or 0

        overdue_tasks = len(self.task_repo.list_overdue(organization_id))
        tasks_by_status = self.task_repo.count_by_status(organization_id)
        tasks_by_priority = self.task_repo.count_by_priority(organization_id)

        avg_progress = db.session.execute(
            db.select(func.avg(Project.progress_percent)).where(
                Project.organization_id == parsed, Project.deleted_at.is_(None)
            )
        ).scalar() or 0

        return {
            "total_projects": total_projects,
            "active_projects": active_projects,
            "completed_projects": completed_projects,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "overdue_tasks": overdue_tasks,
            "tasks_by_status": tasks_by_status,
            "tasks_by_priority": tasks_by_priority,
            "average_project_progress": round(float(avg_progress), 1),
            "completion_rate": round((completed_tasks / total_tasks * 100) if total_tasks else 0, 1),
        }

    def get_activity(self, user_id: str, query_params: dict[str, Any]) -> dict[str, Any]:
        organization_id = query_params.get("organization_id")
        if organization_id:
            self.rbac.require_org_membership(user_id, organization_id)
        page = max(int(query_params.get("page") or 1), 1)
        per_page = min(max(int(query_params.get("per_page") or 50), 1), 100)
        items, total = self.activity.list(
            organization_id=organization_id,
            entity_type=query_params.get("entity_type"),
            entity_id=query_params.get("entity_id"),
            page=page,
            per_page=per_page,
        )
        return {
            "items": [a.to_dict() for a in items],
            "pagination": {"page": page, "per_page": per_page, "total": total, "pages": (total + per_page - 1) // per_page if total else 0},
        }

    def _scope(self, user_id, query):
        organization_id = query.get("organization_id")
        if not organization_id: raise ValueError("organization_id is required")
        self.rbac.require_org_membership(user_id, organization_id)
        import uuid
        try: org_id = uuid.UUID(str(organization_id))
        except ValueError as exc: raise ValueError("Invalid organization") from exc
        project_id = query.get("project_id")
        if project_id: self.rbac.require_project_access(user_id, project_id)
        return org_id, project_id

    def get_task_analytics(self, user_id, query):
        org_id, project_id = self._scope(user_id, query)
        tasks = db.select(Task).where(Task.organization_id == org_id, Task.deleted_at.is_(None))
        if project_id: tasks = tasks.where(Task.project_id == project_id)
        rows = db.session.execute(tasks).scalars().all()
        status, priority = {}, {}
        for task in rows: status[task.status] = status.get(task.status, 0) + 1; priority[task.priority] = priority.get(task.priority, 0) + 1
        completed = sum(task.status == "DONE" for task in rows); overdue = sum(bool(task.due_date and task.due_date < date.today() and task.status != "DONE") for task in rows)
        return {"status_distribution": [{"name": k, "value": v} for k,v in status.items()], "priority_distribution": [{"name": k, "value": v} for k,v in priority.items()], "completed": completed, "incomplete": len(rows)-completed, "overdue_count": overdue, "completion_rate": round(completed * 100 / len(rows), 1) if rows else 0}

    def get_project_analytics(self, user_id, query):
        org_id, project_id = self._scope(user_id, query)
        projects, _ = self.project_repo.list_for_user(user_id, str(org_id), page=1, per_page=1000)
        if project_id: projects = [p for p in projects if str(p.id) == str(project_id)]
        result=[]
        for project in projects:
            tasks = db.session.execute(db.select(Task).where(Task.project_id == project.id, Task.deleted_at.is_(None))).scalars().all(); total=len(tasks); done=sum(t.status=="DONE" for t in tasks); overdue=sum(bool(t.due_date and t.due_date < date.today() and t.status != "DONE") for t in tasks)
            result.append({"project_id":str(project.id),"name":project.name,"total_tasks":total,"completed_tasks":done,"completion_rate":round(done*100/total,1) if total else 0,"overdue_tasks":overdue})
        return {"items": result}

    def get_team_analytics(self, user_id, query):
        org_id, _ = self._scope(user_id, query); teams=db.session.execute(db.select(Team).where(Team.organization_id==org_id,Team.deleted_at.is_(None))).scalars().all(); result=[]
        for team in teams:
            tasks=db.session.execute(db.select(Task).where(Task.team_id==team.id,Task.deleted_at.is_(None))).scalars().all()
            result.append({"team_id":str(team.id),"name":team.name,"members":db.session.execute(db.select(func.count(TeamMembership.id)).where(TeamMembership.team_id==team.id)).scalar() or 0,"assigned_tasks":len(tasks),"completed_tasks":sum(t.status=="DONE" for t in tasks),"in_progress_tasks":sum(t.status=="IN_PROGRESS" for t in tasks),"overdue_tasks":sum(bool(t.due_date and t.due_date<date.today() and t.status!="DONE") for t in tasks)})
        return {"items":result}

    def get_productivity(self, user_id, query):
        metrics=self.get_task_analytics(user_id, query); org_id,_=self._scope(user_id,query); now=datetime.now().astimezone(); today=now.date(); week=today-timedelta(days=today.weekday()); month=today.replace(day=1)
        tasks=db.session.execute(db.select(Task).where(Task.organization_id==org_id,Task.status=="DONE",Task.deleted_at.is_(None))).scalars().all()
        return {"completion_rate":metrics["completion_rate"],"overdue_rate":round(metrics["overdue_count"]*100/(metrics["completed"]+metrics["incomplete"]),1) if metrics["completed"]+metrics["incomplete"] else 0,"tasks_completed_today":sum(t.updated_at.date()==today for t in tasks),"tasks_completed_this_week":sum(t.updated_at.date()>=week for t in tasks),"tasks_completed_this_month":sum(t.updated_at.date()>=month for t in tasks)}
