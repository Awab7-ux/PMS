import uuid
from typing import Any

from backend.app import db
from backend.app.models.organization import Organization, OrganizationMembership, Permission, Role, RolePermission
from backend.app.models.team import Team, TeamMembership
from backend.app.models.user import User
from backend.app.repositories.organization_repository import OrganizationRepository, TeamRepository
from backend.app.repositories.user_repository import UserRepository


class OrganizationService:
    def __init__(self, organization_repository: OrganizationRepository | None = None, team_repository: TeamRepository | None = None, user_repository: UserRepository | None = None):
        self.organization_repository = organization_repository or OrganizationRepository()
        self.team_repository = team_repository or TeamRepository()
        self.user_repository = user_repository or UserRepository()

    def _get_user(self, user_id: str | uuid.UUID) -> User | None:
        return self.user_repository.get_by_id(str(user_id))

    @staticmethod
    def _normalize_role_name(role_name: str | None) -> str | None:
        if not role_name:
            return None
        normalized = role_name.strip().lower().replace("-", "_")
        aliases = {
            "organization_owner": "Organization Owner",
            "organization-owner": "Organization Owner",
            "project_manager": "Project Manager",
            "project-manager": "Project Manager",
            "team_member": "Team Member",
            "team-member": "Team Member",
            "client": "Client",
        }
        return aliases.get(normalized, role_name.strip())

    def _get_role(self, organization_id: str | uuid.UUID, role_name: str | None) -> Role | None:
        normalized_name = self._normalize_role_name(role_name)
        if not normalized_name:
            return None
        return self.organization_repository.get_role_by_name(organization_id, normalized_name)

    def _ensure_default_roles(self, organization: Organization) -> tuple[Role, Role, Role, Role]:
        owner_role = self._get_role(organization.id, "Organization Owner")
        if not owner_role:
            owner_role = Role(organization_id=organization.id, name="Organization Owner", description="Organization owner", is_system_default=True)
            self.organization_repository.create_role(owner_role)

        project_manager_role = self._get_role(organization.id, "Project Manager")
        if not project_manager_role:
            project_manager_role = Role(organization_id=organization.id, name="Project Manager", description="Project manager", is_system_default=True)
            self.organization_repository.create_role(project_manager_role)

        team_member_role = self._get_role(organization.id, "Team Member")
        if not team_member_role:
            team_member_role = Role(organization_id=organization.id, name="Team Member", description="Team member", is_system_default=True)
            self.organization_repository.create_role(team_member_role)

        client_role = self._get_role(organization.id, "Client")
        if not client_role:
            client_role = Role(organization_id=organization.id, name="Client", description="Client", is_system_default=True)
            self.organization_repository.create_role(client_role)

        return owner_role, project_manager_role, team_member_role, client_role

    def _ensure_permissions(self, role: Role) -> None:
        permission_codes = [
            "organization:create",
            "organization:read",
            "organization:update",
            "organization:delete",
            "organization:member:create",
            "organization:member:read",
            "organization:member:update",
            "organization:member:delete",
            "team:create",
            "team:read",
            "team:update",
            "team:delete",
            "team:member:create",
            "team:member:delete",
        ]
        for code in permission_codes:
            permission = self.organization_repository.get_permission(code)
            if not permission:
                permission = Permission(code=code, description=code)
                self.organization_repository.create_permission(permission)
            if not self.organization_repository.get_role_permission(role.id, permission.id):
                self.organization_repository.create_role_permission(RolePermission(role_id=role.id, permission_id=permission.id))

    def create_organization(self, creator_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        name = (payload.get("name") or "").strip()
        slug = (payload.get("slug") or "").strip().lower()
        description = (payload.get("description") or "").strip() or None
        industry = (payload.get("industry") or "").strip() or None
        if not name or not slug:
            raise ValueError("Name and slug are required")
        if self.organization_repository.get_by_slug(slug):
            raise ValueError("Slug already in use")
        creator = self._get_user(creator_id)
        if not creator:
            raise ValueError("User not found")

        organization = Organization(name=name, slug=slug, description=description, industry=industry)
        self.organization_repository.create(organization)
        owner_role, _, _, _ = self._ensure_default_roles(organization)
        self._ensure_permissions(owner_role)
        membership = OrganizationMembership(
            organization_id=organization.id,
            user_id=creator.id,
            role_id=owner_role.id,
            status="active",
            is_owner=True,
            invited_by=None,
        )
        self.organization_repository.create_membership(membership)
        db.session.commit()
        return organization.to_dict()

    def list_organizations(self, user_id: str) -> list[dict[str, Any]]:
        organizations = self.organization_repository.list_for_user(user_id)
        return [organization.to_dict() for organization in organizations]

    def get_organization(self, user_id: str, organization_id: str) -> dict[str, Any]:
        organization = self.organization_repository.get_by_id(organization_id)
        if not organization or not organization.is_active:
            raise ValueError("Organization not found")
        membership = self.organization_repository.get_membership(organization_id, user_id)
        if not membership or membership.status != "active":
            raise PermissionError("Access denied")
        return organization.to_dict()

    def update_organization(self, user_id: str, organization_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        membership = self.organization_repository.get_membership(organization_id, user_id)
        if not membership or membership.status != "active":
            raise PermissionError("Access denied")
        if membership.role.name != "Organization Owner":
            raise PermissionError("Insufficient permissions")
        organization = self.organization_repository.get_by_id(organization_id)
        if not organization or not organization.is_active:
            raise ValueError("Organization not found")
        if "name" in payload and payload.get("name"):
            organization.name = payload.get("name")
        if "description" in payload:
            organization.description = payload.get("description")
        if "industry" in payload:
            organization.industry = payload.get("industry")
        if "slug" in payload and payload.get("slug"):
            organization.slug = payload.get("slug")
        self.organization_repository.update(organization)
        return organization.to_dict()

    def delete_organization(self, user_id: str, organization_id: str) -> dict[str, Any]:
        membership = self.organization_repository.get_membership(organization_id, user_id)
        if not membership or membership.status != "active":
            raise PermissionError("Access denied")
        if membership.role.name != "Organization Owner":
            raise PermissionError("Insufficient permissions")
        organization = self.organization_repository.get_by_id(organization_id)
        if not organization or not organization.is_active:
            raise ValueError("Organization not found")
        self.organization_repository.delete(organization)
        return {"message": "Organization archived"}

    def list_members(self, user_id: str, organization_id: str) -> list[dict[str, Any]]:
        membership = self.organization_repository.get_membership(organization_id, user_id)
        if not membership or membership.status != "active":
            raise PermissionError("Access denied")
        memberships = self.organization_repository.list_memberships(organization_id)
        return [m.to_dict() for m in memberships]

    def add_member(self, acting_user_id: str, organization_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        acting_membership = self.organization_repository.get_membership(organization_id, acting_user_id)
        if not acting_membership or acting_membership.status != "active":
            raise PermissionError("Access denied")
        if acting_membership.role.name != "Organization Owner":
            raise PermissionError("Insufficient permissions")
        target_identifier = (payload.get("user_id") or "").strip()
        target_user = None
        if "@" in target_identifier:
            target_user = self.user_repository.get_by_email(target_identifier.lower())
        else:
            target_user = self.user_repository.get_by_id(target_identifier)
        if not target_user:
            raise ValueError("User not found")
        if self.organization_repository.get_membership(organization_id, target_user.id):
            raise ValueError("Member already exists")
        role_name = (payload.get("role") or "Team Member").strip()
        role = self._get_role(organization_id, role_name)
        if not role:
            raise ValueError("Role not found")
        if self._normalize_role_name(role_name) == "Organization Owner":
            raise ValueError("Cannot assign organization owner")
        membership = OrganizationMembership(organization_id=organization_id, user_id=target_user.id, role_id=role.id, status="active", invited_by=acting_user_id)
        self.organization_repository.create_membership(membership)
        db.session.commit()
        return membership.to_dict()

    def update_member(self, acting_user_id: str, organization_id: str, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        acting_membership = self.organization_repository.get_membership(organization_id, acting_user_id)
        if not acting_membership or acting_membership.status != "active":
            raise PermissionError("Access denied")
        if acting_membership.role.name != "Organization Owner":
            raise PermissionError("Insufficient permissions")
        target_membership = self.organization_repository.get_membership(organization_id, user_id)
        if not target_membership:
            raise ValueError("Member not found")
        if self._normalize_role_name(payload.get("role")) == "Organization Owner":
            raise ValueError("Cannot assign organization owner")
        role = self._get_role(organization_id, payload.get("role"))
        if not role:
            raise ValueError("Role not found")
        target_membership.role_id = role.id
        target_membership.role = role
        self.organization_repository.update_membership(target_membership)
        return target_membership.to_dict()

    def remove_member(self, acting_user_id: str, organization_id: str, user_id: str) -> dict[str, Any]:
        acting_membership = self.organization_repository.get_membership(organization_id, acting_user_id)
        if not acting_membership or acting_membership.status != "active":
            raise PermissionError("Access denied")
        if acting_membership.role.name != "Organization Owner":
            raise PermissionError("Insufficient permissions")
        target_membership = self.organization_repository.get_membership(organization_id, user_id)
        if not target_membership:
            raise ValueError("Member not found")
        if target_membership.is_owner:
            raise ValueError("Cannot remove organization owner")
        self.organization_repository.remove_membership(target_membership)
        return {"message": "Member removed"}

    def create_team(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        organization_id = payload.get("organization_id")
        organization = self.organization_repository.get_by_id(organization_id)
        if not organization or not organization.is_active:
            raise ValueError("Organization not found")
        membership = self.organization_repository.get_membership(organization_id, user_id)
        if not membership or membership.status != "active":
            raise PermissionError("Access denied")
        if membership.role.name not in {"Organization Owner", "Project Manager"}:
            raise PermissionError("Insufficient permissions")
        name = (payload.get("name") or "").strip()
        if not name:
            raise ValueError("Name is required")
        team = Team(organization_id=organization.id, name=name, description=(payload.get("description") or "").strip() or None, lead_user_id=payload.get("lead_user_id") or None)
        self.team_repository.create(team)
        db.session.commit()
        return team.to_dict()

    def list_teams(self, user_id: str) -> list[dict[str, Any]]:
        organizations = self.organization_repository.list_for_user(user_id)
        teams: list[Team] = []
        for organization in organizations:
            teams.extend([team for team in organization.teams if team.is_active])
        return [team.to_dict() for team in teams]

    def get_team(self, user_id: str, team_id: str) -> dict[str, Any]:
        team = self.team_repository.get_by_id(team_id)
        if not team or not team.is_active:
            raise ValueError("Team not found")
        membership = self.organization_repository.get_membership(team.organization_id, user_id)
        if not membership or membership.status != "active":
            raise PermissionError("Access denied")
        return team.to_dict()

    def update_team(self, user_id: str, team_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        team = self.team_repository.get_by_id(team_id)
        if not team or not team.is_active:
            raise ValueError("Team not found")
        membership = self.organization_repository.get_membership(team.organization_id, user_id)
        if not membership or membership.status != "active":
            raise PermissionError("Access denied")
        if membership.role.name not in {"Organization Owner", "Project Manager"}:
            raise PermissionError("Insufficient permissions")
        if "name" in payload and payload.get("name"):
            team.name = payload.get("name")
        if "description" in payload:
            team.description = payload.get("description")
        if "lead_user_id" in payload:
            team.lead_user_id = payload.get("lead_user_id")
        self.team_repository.update(team)
        return team.to_dict()

    def delete_team(self, user_id: str, team_id: str) -> dict[str, Any]:
        team = self.team_repository.get_by_id(team_id)
        if not team or not team.is_active:
            raise ValueError("Team not found")
        membership = self.organization_repository.get_membership(team.organization_id, user_id)
        if not membership or membership.status != "active":
            raise PermissionError("Access denied")
        if membership.role.name not in {"Organization Owner", "Project Manager"}:
            raise PermissionError("Insufficient permissions")
        self.team_repository.delete(team)
        return {"message": "Team archived"}

    def add_team_member(self, acting_user_id: str, team_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        team = self.team_repository.get_by_id(team_id)
        if not team or not team.is_active:
            raise ValueError("Team not found")
        acting_membership = self.organization_repository.get_membership(team.organization_id, acting_user_id)
        if not acting_membership or acting_membership.status != "active":
            raise PermissionError("Access denied")
        if acting_membership.role.name not in {"Organization Owner", "Project Manager"}:
            raise PermissionError("Insufficient permissions")
        target_identifier = (payload.get("user_id") or "").strip()
        target_user = None
        if "@" in target_identifier:
            target_user = self.user_repository.get_by_email(target_identifier.lower())
        else:
            target_user = self.user_repository.get_by_id(target_identifier)
        if not target_user:
            raise ValueError("User not found")
        org_membership = self.organization_repository.get_membership(team.organization_id, target_user.id)
        if not org_membership or org_membership.status != "active":
            raise ValueError("User is not a member of the organization")
        if self.team_repository.get_membership(team.id, target_user.id):
            raise ValueError("Member already exists")
        membership = TeamMembership(team_id=team.id, user_id=target_user.id, role_in_team="member")
        self.team_repository.create_membership(membership)
        db.session.commit()
        return membership.to_dict()

    def remove_team_member(self, acting_user_id: str, team_id: str, user_id: str) -> dict[str, Any]:
        team = self.team_repository.get_by_id(team_id)
        if not team or not team.is_active:
            raise ValueError("Team not found")
        acting_membership = self.organization_repository.get_membership(team.organization_id, acting_user_id)
        if not acting_membership or acting_membership.status != "active":
            raise PermissionError("Access denied")
        if acting_membership.role.name not in {"Organization Owner", "Project Manager"}:
            raise PermissionError("Insufficient permissions")
        membership = self.team_repository.get_membership(team.id, user_id)
        if not membership:
            raise ValueError("Member not found")
        self.team_repository.remove_membership(membership)
        return {"message": "Member removed"}
