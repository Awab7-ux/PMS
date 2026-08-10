from typing import Any

from sqlalchemy import func, or_

from backend.app import db
from backend.app.models.project import Project
from backend.app.models.task import Task
from backend.app.models.team import Team
from backend.app.models.user import User
from backend.app.repositories.organization_repository import OrganizationRepository
from backend.app.services.rbac_service import RBACService


class SearchService:
    def __init__(self):
        self.org_repo = OrganizationRepository()
        self.rbac = RBACService()

    def global_search(self, user_id: str, query_params: dict[str, Any]) -> dict[str, Any]:
        organization_id = query_params.get("organization_id")
        if not organization_id:
            raise ValueError("organization_id is required")
        self.rbac.require_org_membership(user_id, organization_id)

        q = (query_params.get("q") or "").strip()
        if not q:
            return {"projects": [], "tasks": [], "users": [], "teams": []}

        page = max(int(query_params.get("page") or 1), 1)
        per_page = min(max(int(query_params.get("per_page") or 10), 1), 50)
        term = f"%{q}%"

        import uuid
        try:
            parsed = uuid.UUID(str(organization_id))
        except (ValueError, TypeError):
            raise ValueError("Invalid organization")

        projects = db.session.execute(
            db.select(Project).where(
                Project.organization_id == parsed,
                Project.deleted_at.is_(None),
                or_(Project.name.ilike(term), Project.code.ilike(term)),
            ).limit(per_page)
        ).scalars().all()

        tasks = db.session.execute(
            db.select(Task).where(
                Task.organization_id == parsed,
                Task.deleted_at.is_(None),
                or_(Task.title.ilike(term), Task.description.ilike(term)),
            ).limit(per_page)
        ).scalars().all()

        memberships = self.org_repo.list_memberships(organization_id)
        user_ids = [m.user_id for m in memberships if m.status == "active"]
        users = []
        if user_ids:
            users = db.session.execute(
                db.select(User).where(
                    User.id.in_(user_ids),
                    or_(User.full_name.ilike(term), User.email.ilike(term), User.username.ilike(term)),
                ).limit(per_page)
            ).scalars().all()

        teams = db.session.execute(
            db.select(Team).where(
                Team.organization_id == parsed,
                Team.is_active.is_(True),
                Team.name.ilike(term),
            ).limit(per_page)
        ).scalars().all()

        return {
            "projects": [p.to_dict() for p in projects],
            "tasks": [t.to_dict() for t in tasks],
            "users": [u.to_dict() for u in users],
            "teams": [t.to_dict() for t in teams],
            "query": q,
        }
