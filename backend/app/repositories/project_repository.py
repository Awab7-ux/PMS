import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import or_, select

from backend.app import db
from backend.app.models.project import Project, ProjectMembership
from backend.app.utils.uuid_helpers import parse_uuid


class ProjectRepository:
    def create(self, project: Project) -> Project:
        db.session.add(project)
        db.session.flush()
        return project

    def update(self, project: Project) -> Project:
        db.session.flush()
        return project

    def delete(self, project: Project) -> None:
        project.deleted_at = datetime.now(timezone.utc)
        db.session.flush()

    def get_by_id(self, project_id: str | uuid.UUID | None) -> Optional[Project]:
        parsed = parse_uuid(project_id)
        if not parsed:
            return None
        return db.session.get(Project, parsed)

    def get_by_code(self, organization_id: str | uuid.UUID, code: str) -> Optional[Project]:
        parsed_org = parse_uuid(organization_id)
        if not parsed_org or not code:
            return None
        return db.session.execute(
            select(Project).where(
                Project.organization_id == parsed_org,
                Project.code == code,
                Project.deleted_at.is_(None),
            )
        ).scalar_one_or_none()

    def list_for_user(
        self,
        user_id: str | uuid.UUID,
        organization_id: str | uuid.UUID | None = None,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Project], int]:
        parsed_user = parse_uuid(user_id)
        if not parsed_user:
            return [], 0

        query = (
            select(Project)
            .join(ProjectMembership, ProjectMembership.project_id == Project.id)
            .where(
                ProjectMembership.user_id == parsed_user,
                Project.deleted_at.is_(None),
            )
        )

        parsed_org = parse_uuid(organization_id) if organization_id else None
        if parsed_org:
            query = query.where(Project.organization_id == parsed_org)
        if status:
            query = query.where(Project.status == status)
        if search:
            term = f"%{search.strip()}%"
            query = query.where(or_(Project.name.ilike(term), Project.code.ilike(term)))

        query = query.order_by(Project.updated_at.desc())
        total = db.session.execute(select(db.func.count()).select_from(query.subquery())).scalar_one()
        offset = max(page - 1, 0) * per_page
        projects = db.session.execute(query.offset(offset).limit(per_page)).scalars().all()
        return list(projects), total

    def list_for_organization(self, organization_id: str | uuid.UUID) -> list[Project]:
        parsed_org = parse_uuid(organization_id)
        if not parsed_org:
            return []
        return db.session.execute(
            select(Project).where(
                Project.organization_id == parsed_org,
                Project.deleted_at.is_(None),
            )
        ).scalars().all()

    def create_membership(self, membership: ProjectMembership) -> ProjectMembership:
        db.session.add(membership)
        db.session.flush()
        return membership

    def get_membership(self, project_id: str | uuid.UUID, user_id: str | uuid.UUID) -> Optional[ProjectMembership]:
        parsed_project = parse_uuid(project_id)
        parsed_user = parse_uuid(user_id)
        if not parsed_project or not parsed_user:
            return None
        return db.session.execute(
            select(ProjectMembership).where(
                ProjectMembership.project_id == parsed_project,
                ProjectMembership.user_id == parsed_user,
            )
        ).scalar_one_or_none()

    def list_memberships(self, project_id: str | uuid.UUID) -> list[ProjectMembership]:
        parsed_project = parse_uuid(project_id)
        if not parsed_project:
            return []
        return db.session.execute(
            select(ProjectMembership).where(ProjectMembership.project_id == parsed_project)
        ).scalars().all()

    def remove_membership(self, membership: ProjectMembership) -> None:
        db.session.delete(membership)
        db.session.flush()
