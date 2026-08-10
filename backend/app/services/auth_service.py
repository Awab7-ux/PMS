import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token, decode_token
from werkzeug.security import check_password_hash, generate_password_hash

from backend.app import db
from backend.app.models.token import AuthToken
from backend.app.models.user import User
from backend.app.repositories.token_repository import TokenRepository
from backend.app.repositories.user_repository import UserRepository
from backend.app.utils.uuid_helpers import parse_uuid


class AuthService:
    def __init__(self, repository: UserRepository | None = None, token_repository: TokenRepository | None = None):
        self.repository = repository or UserRepository()
        self.token_repository = token_repository or TokenRepository()
        self._revoked_tokens: set[str] = set()

    @staticmethod
    def validate_password(password: str) -> None:
        if len(password) < 12:
            raise ValueError("Password must be at least 12 characters long")
        if not re.search(r"[A-Z]", password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", password):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[^A-Za-z0-9]", password):
            raise ValueError("Password must contain at least one special character")

    @staticmethod
    def validate_email(email: str) -> None:
        if "@" not in email or "." not in email:
            raise ValueError("Invalid email address")

    def _create_token(self, user_id: str, token_type: str, expires_delta: timedelta) -> str:
        token_value = secrets.token_urlsafe(32)
        auth_token = AuthToken(
            user_id=parse_uuid(user_id),
            token=token_value,
            token_type=token_type,
            expires_at=datetime.now(timezone.utc) + expires_delta,
        )
        self.token_repository.create(auth_token)
        db.session.commit()
        return token_value

    def _consume_token(self, token_value: str, token_type: str) -> str | None:
        entry = self.token_repository.get_by_token(token_value, token_type)
        if not entry:
            return None
        expires_at = entry.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            return None
        self.token_repository.mark_used(entry)
        db.session.commit()
        return str(entry.user_id)

    def register(self, payload: dict[str, Any]) -> dict[str, Any]:
        email = (payload.get("email") or "").strip().lower()
        username = (payload.get("username") or "").strip()
        full_name = (payload.get("full_name") or "").strip()
        password = payload.get("password") or ""

        if not email or not username or not full_name or not password:
            raise ValueError("Missing required fields")

        self.validate_email(email)
        self.validate_password(password)
        if self.repository.get_by_email(email):
            raise ValueError("Email already registered")
        if self.repository.get_by_username(username):
            raise ValueError("Username already registered")

        user = User(
            email=email,
            username=username,
            full_name=full_name,
            password_hash=generate_password_hash(password),
            is_active=True,
        )
        self.repository.create(user)

        token = self._create_token(str(user.id), "email_verification", timedelta(hours=24))
        return {"user": user.to_dict(), "verification_token": token}

    def login(self, payload: dict[str, Any]) -> dict[str, Any]:
        email = (payload.get("email") or "").strip().lower()
        password = payload.get("password") or ""
        if not email or not password:
            raise ValueError("Email and password are required")

        user = self.repository.get_by_email(email)
        if not user or not check_password_hash(user.password_hash, password):
            raise ValueError("Invalid credentials")
        if not user.is_active:
            raise PermissionError("Account is inactive")

        user.last_login_at = datetime.now(timezone.utc)
        self.repository.update(user)

        access_token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(seconds=current_app.config["JWT_ACCESS_TOKEN_EXPIRES"]),
        )
        refresh_token = create_refresh_token(identity=str(user.id), expires_delta=timedelta(days=30))
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": current_app.config["JWT_ACCESS_TOKEN_EXPIRES"],
        }

    def refresh(self, refresh_token: str) -> dict[str, Any]:
        if not refresh_token:
            raise ValueError("Refresh token is required")
        if refresh_token in self._revoked_tokens:
            raise ValueError("Refresh token revoked")

        try:
            decoded = decode_token(refresh_token)
        except Exception as exc:
            raise ValueError("Invalid refresh token") from exc

        if decoded.get("type") != "refresh":
            raise ValueError("Invalid refresh token")

        identity = decoded.get("sub")
        access_token = create_access_token(
            identity=identity,
            expires_delta=timedelta(seconds=current_app.config["JWT_ACCESS_TOKEN_EXPIRES"]),
        )
        return {"access_token": access_token, "token_type": "bearer", "expires_in": current_app.config["JWT_ACCESS_TOKEN_EXPIRES"]}

    def logout(self, identity: str) -> dict[str, Any]:
        return {}

    def forgot_password(self, email: str) -> dict[str, Any]:
        user = self.repository.get_by_email(email.lower())
        if not user:
            return {"message": "If an account exists, a reset link has been sent."}

        token = self._create_token(str(user.id), "password_reset", timedelta(minutes=15))
        return {"message": "If an account exists, a reset link has been sent.", "reset_token": token}

    def reset_password(self, token: str, new_password: str) -> dict[str, Any]:
        self.validate_password(new_password)

        user_id = self._consume_token(token, "password_reset")
        if not user_id:
            raise ValueError("Invalid or expired reset token")

        user = self.repository.get_by_id(user_id)
        if not user:
            raise ValueError("Invalid or expired reset token")

        user.password_hash = generate_password_hash(new_password)
        self.repository.update(user)
        return {"message": "Password reset successful."}

    def verify_email(self, token: str) -> dict[str, Any]:
        user_id = self._consume_token(token, "email_verification")
        if not user_id:
            raise ValueError("Invalid or expired verification token")

        user = self.repository.get_by_id(user_id)
        if not user:
            raise ValueError("Invalid or expired verification token")

        user.is_active = True
        self.repository.update(user)
        return {"message": "Email verified successfully."}

    def get_current_user(self, user_id: str) -> dict[str, Any]:
        user = self.repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        return user.to_dict()
