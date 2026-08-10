import uuid
from typing import Optional

from backend.app import db
from backend.app.models.user import User


class UserRepository:
    def get_by_email(self, email: str) -> Optional[User]:
        return db.session.execute(db.select(User).where(User.email == email)).scalar_one_or_none()

    def get_by_username(self, username: str) -> Optional[User]:
        return db.session.execute(db.select(User).where(User.username == username)).scalar_one_or_none()

    def get_by_id(self, user_id: str) -> Optional[User]:
        try:
            parsed = uuid.UUID(str(user_id))
        except (ValueError, TypeError):
            return None
        return db.session.get(User, parsed)

    def create(self, user: User) -> User:
        db.session.add(user)
        db.session.commit()
        return user

    def update(self, user: User) -> User:
        db.session.commit()
        return user

    def list_all(self) -> list[User]:
        return db.session.execute(db.select(User).where(User.deleted_at.is_(None))).scalars().all()
