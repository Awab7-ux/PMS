import re
from typing import Any

from werkzeug.security import check_password_hash, generate_password_hash

from backend.app import db
from backend.app.repositories.user_repository import UserRepository
from backend.app.services.rbac_service import RBACService


class UserService:
    def __init__(self):
        self.repository = UserRepository()
        self.rbac = RBACService()

    def get_profile(self, user_id: str) -> dict[str, Any]:
        user = self.repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        return user.to_dict()

    def update_profile(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        user = self.repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        if "full_name" in payload and payload.get("full_name"):
            user.full_name = payload["full_name"].strip()
        if "username" in payload and payload.get("username"):
            existing = self.repository.get_by_username(payload["username"].strip())
            if existing and str(existing.id) != str(user.id):
                raise ValueError("Username already taken")
            user.username = payload["username"].strip()
        if "email" in payload and payload.get("email"):
            email = payload["email"].strip().lower()
            existing = self.repository.get_by_email(email)
            if existing and str(existing.id) != str(user.id):
                raise ValueError("Email already registered")
            user.email = email
        if "avatar_url" in payload:
            user.avatar_url = payload.get("avatar_url")
        self.repository.update(user)
        db.session.commit()
        return user.to_dict()

    def change_password(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        from backend.app.services.auth_service import AuthService

        user = self.repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        current = payload.get("current_password") or ""
        new_password = payload.get("new_password") or ""
        if not current or not new_password:
            raise ValueError("Current and new password are required")
        if not check_password_hash(user.password_hash, current):
            raise ValueError("Current password is incorrect")
        AuthService.validate_password(new_password)
        user.password_hash = generate_password_hash(new_password)
        self.repository.update(user)
        db.session.commit()
        return {"message": "Password changed successfully"}

    def list_users(
        self,
        acting_user_id: str,
        organization_id: str | None = None,
        search: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        if organization_id:
            self.rbac.require_org_membership(acting_user_id, organization_id)
            perms = self.rbac.get_user_permissions(acting_user_id, organization_id)
            if "admin.manage_users" not in perms and "member.invite" not in perms:
                acting = self.repository.get_by_id(acting_user_id)
                if not acting or not acting.is_superuser:
                    raise PermissionError("Insufficient permissions")

        from backend.app.repositories.organization_repository import OrganizationRepository
        org_repo = OrganizationRepository()

        if organization_id:
            memberships = org_repo.list_memberships(organization_id)
            users = [m.user for m in memberships if m.user and m.status == "active"]
        else:
            acting = self.repository.get_by_id(acting_user_id)
            if not acting or not acting.is_superuser:
                raise PermissionError("Insufficient permissions")
            users = self.repository.list_all()

        if search:
            term = search.strip().lower()
            users = [
                u for u in users
                if term in u.full_name.lower() or term in u.email.lower() or term in u.username.lower()
            ]

        total = len(users)
        offset = (page - 1) * per_page
        page_users = users[offset : offset + per_page]
        return {
            "items": [u.to_dict() for u in page_users],
            "pagination": {"page": page, "per_page": per_page, "total": total, "pages": (total + per_page - 1) // per_page if total else 0},
        }

    def get_user(self, acting_user_id: str, target_user_id: str, organization_id: str | None = None) -> dict[str, Any]:
        if organization_id:
            self.rbac.require_org_membership(acting_user_id, organization_id)
        user = self.repository.get_by_id(target_user_id)
        if not user:
            raise ValueError("User not found")
        return user.to_dict()
