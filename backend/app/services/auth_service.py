from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models.user import UserRecord

ROLE_LEVEL = {"viewer": 10, "operator": 20, "engineer": 30, "administrator": 40}
_password_hash = PasswordHash.recommended()
settings = get_settings()


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def hash_password(password: str) -> str:
        return _password_hash.hash(password)

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        return _password_hash.verify(password, password_hash)

    def get_user(self, username: str) -> UserRecord | None:
        return self.db.scalar(select(UserRecord).where(UserRecord.username == username))

    def authenticate(self, username: str, password: str) -> UserRecord | None:
        user = self.get_user(username)
        if user is None or not user.active or not self.verify_password(password, user.password_hash):
            return None
        return user

    def issue_token(self, user: UserRecord) -> tuple[str, int]:
        ttl = int(settings.auth_token_ttl_minutes) * 60
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user.username,
            "role": user.role,
            "iat": now,
            "exp": now + timedelta(seconds=ttl),
            "iss": settings.auth_token_issuer,
            "aud": settings.auth_token_audience,
        }
        token = jwt.encode(payload, settings.auth_jwt_secret, algorithm="HS256")
        return token, ttl

    @staticmethod
    def decode_token(token: str) -> dict:
        return jwt.decode(
            token,
            settings.auth_jwt_secret,
            algorithms=["HS256"],
            issuer=settings.auth_token_issuer,
            audience=settings.auth_token_audience,
        )

    @staticmethod
    def role_allows(actual: str, required: str) -> bool:
        return ROLE_LEVEL.get(actual, -1) >= ROLE_LEVEL[required]

    def create_user(self, username: str, password: str, role: str) -> UserRecord:
        if self.get_user(username) is not None:
            raise ValueError("username_already_exists")
        record = UserRecord(username=username, password_hash=self.hash_password(password), role=role, active=True)
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def list_users(self) -> list[UserRecord]:
        return list(self.db.scalars(select(UserRecord).order_by(UserRecord.username.asc())).all())

    def update_user(self, username: str, *, role: str | None, active: bool | None, password: str | None) -> UserRecord | None:
        user = self.get_user(username)
        if user is None:
            return None
        if role is not None:
            user.role = role
        if active is not None:
            user.active = active
        if password is not None:
            user.password_hash = self.hash_password(password)
        self.db.commit()
        self.db.refresh(user)
        return user

    def ensure_bootstrap_admin(self) -> None:
        username = settings.auth_bootstrap_admin_username.strip()
        password = settings.auth_bootstrap_admin_password
        if not username or not password:
            return
        if self.get_user(username) is None:
            self.create_user(username, password, "administrator")
