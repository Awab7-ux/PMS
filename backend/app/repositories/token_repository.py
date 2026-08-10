import uuid
from datetime import datetime, timezone
from typing import Optional

from backend.app import db
from backend.app.models.token import AuthToken


class TokenRepository:
    def create(self, token: AuthToken) -> AuthToken:
        db.session.add(token)
        db.session.flush()
        return token

    def get_by_token(self, token_value: str, token_type: str) -> Optional[AuthToken]:
        return db.session.execute(
            db.select(AuthToken).where(
                AuthToken.token == token_value,
                AuthToken.token_type == token_type,
                AuthToken.used_at.is_(None),
            )
        ).scalar_one_or_none()

    def mark_used(self, token: AuthToken) -> None:
        token.used_at = datetime.now(timezone.utc)
        db.session.flush()

    def delete_expired(self) -> None:
        now = datetime.now(timezone.utc)
        expired = db.session.execute(
            db.select(AuthToken).where(AuthToken.expires_at < now)
        ).scalars().all()
        for t in expired:
            db.session.delete(t)
        db.session.flush()
