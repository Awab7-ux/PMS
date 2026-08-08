import uuid
from datetime import datetime, timezone
from typing import Optional

from backend.app import db
from backend.app.models.organization import Organization, OrganizationMembership, Role, RolePermission, Permission
from backend.app.models.team import Team, TeamMembership
from backend.app.models.user import User


class OrganizationRepository:
    def create(self, organization: Organization) -> Organization:
        db.session.add(organization)
        db.session.flush()
        return organization

    def update(self, organization: Organization) -> Organization:
        db.session.flush()
        return organization

    def delete(self, organization: Organization) -> None:
        organization.is_active = False
        organization.deleted_at = datetime.now(timezone.utc)
        db.session.flush()

    def get_by_id(self, organization_id: str | uuid.UUID | None) -> Optional[Organization]:
        if not organization_id:
            return None
        try:
            parsed = uuid.UUID(str(organization_id))
        except (ValueError, TypeError):
            return None
        return db.session.get(Organization, parsed)

    def get_by_slug(self, slug: str) -> Optional[Organization]:
        return db.session.execute(db.select(Organization).where(Organization.slug == slug)).scalar_one_or_none()

    def list_for_user(self, user_id: str | uuid.UUID) -> list[Organization]:
        try:
            parsed = uuid.UUID(str(user_id))
        except (ValueError, TypeError):
            return []
        memberships = db.session.execute(
            db.select(OrganizationMembership).where(OrganizationMembership.user_id == parsed, OrganizationMembership.status == "active")
        ).scalars().all()
        return [m.organization for m in memberships if m.organization]

    def create_role(self, role: Role) -> Role:
        db.session.add(role)
        db.session.flush()
        return role

    def get_role_by_name(self, organization_id: str | uuid.UUID, name: str) -> Optional[Role]:
        try:
            parsed_org = uuid.UUID(str(organization_id))
        except (ValueError, TypeError):
            return None
        return db.session.execute(
            db.select(Role).where(Role.organization_id == parsed_org, Role.name == name)
        ).scalar_one_or_none()

    def create_membership(self, membership: OrganizationMembership) -> OrganizationMembership:
        db.session.add(membership)
        db.session.flush()
        return membership

    def get_membership(self, organization_id: str | uuid.UUID, user_id: str | uuid.UUID) -> Optional[OrganizationMembership]:
        try:
            parsed_org = uuid.UUID(str(organization_id))
            parsed_user = uuid.UUID(str(user_id))
        except (ValueError, TypeError):
            return None
        return db.session.execute(
            db.select(OrganizationMembership).where(
                OrganizationMembership.organization_id == parsed_org,
                OrganizationMembership.user_id == parsed_user,
            )
        ).scalar_one_or_none()

    def list_memberships(self, organization_id: str | uuid.UUID) -> list[OrganizationMembership]:
        try:
            parsed = uuid.UUID(str(organization_id))
        except (ValueError, TypeError):
            return []
        return db.session.execute(
            db.select(OrganizationMembership).where(OrganizationMembership.organization_id == parsed)
        ).scalars().all()

    def update_membership(self, membership: OrganizationMembership) -> OrganizationMembership:
        db.session.flush()
        return membership

    def remove_membership(self, membership: OrganizationMembership) -> None:
        membership.status = "removed"
        membership.left_at = datetime.now(timezone.utc)
        db.session.flush()

    def create_permission(self, permission: Permission) -> Permission:
        db.session.add(permission)
        db.session.flush()
        return permission

    def create_role_permission(self, role_permission: RolePermission) -> RolePermission:
        db.session.add(role_permission)
        db.session.flush()
        return role_permission

    def get_permission(self, code: str) -> Optional[Permission]:
        return db.session.execute(db.select(Permission).where(Permission.code == code)).scalar_one_or_none()

    def get_role_permission(self, role_id: str | uuid.UUID, permission_id: str | uuid.UUID) -> Optional[RolePermission]:
        try:
            parsed_role = uuid.UUID(str(role_id))
            parsed_permission = uuid.UUID(str(permission_id))
        except (ValueError, TypeError):
            return None
        return db.session.execute(
            db.select(RolePermission).where(
                RolePermission.role_id == parsed_role,
                RolePermission.permission_id == parsed_permission,
            )
        ).scalar_one_or_none()


class TeamRepository:
    def create(self, team: Team) -> Team:
        db.session.add(team)
        db.session.flush()
        return team

    def update(self, team: Team) -> Team:
        db.session.flush()
        return team

    def delete(self, team: Team) -> None:
        team.is_active = False
        team.deleted_at = datetime.now(timezone.utc)
        db.session.flush()

    def get_by_id(self, team_id: str | uuid.UUID | None) -> Optional[Team]:
        if not team_id:
            return None
        try:
            parsed = uuid.UUID(str(team_id))
        except (ValueError, TypeError):
            return None
        return db.session.get(Team, parsed)

    def list_for_user(self, user_id: str | uuid.UUID) -> list[Team]:
        try:
            parsed = uuid.UUID(str(user_id))
        except (ValueError, TypeError):
            return []
        memberships = db.session.execute(
            db.select(TeamMembership).where(TeamMembership.user_id == parsed)
        ).scalars().all()
        return [m.team for m in memberships if m.team]

    def create_membership(self, membership: TeamMembership) -> TeamMembership:
        db.session.add(membership)
        db.session.flush()
        return membership

    def get_membership(self, team_id: str | uuid.UUID, user_id: str | uuid.UUID) -> Optional[TeamMembership]:
        try:
            parsed_team = uuid.UUID(str(team_id))
            parsed_user = uuid.UUID(str(user_id))
        except (ValueError, TypeError):
            return None
        return db.session.execute(
            db.select(TeamMembership).where(
                TeamMembership.team_id == parsed_team,
                TeamMembership.user_id == parsed_user,
            )
        ).scalar_one_or_none()

    def list_memberships(self, team_id: str | uuid.UUID) -> list[TeamMembership]:
        try:
            parsed = uuid.UUID(str(team_id))
        except (ValueError, TypeError):
            return []
        return db.session.execute(
            db.select(TeamMembership).where(TeamMembership.team_id == parsed)
        ).scalars().all()

    def remove_membership(self, membership: TeamMembership) -> None:
        db.session.delete(membership)
        db.session.flush()
