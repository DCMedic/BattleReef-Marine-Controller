from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models.user import UserRecord

ROLE_LEVEL = {"viewer": 10, "operator": 20, "engineer": 30, "administrator": 40}
DEV_JWT_SECRET = "development-only-change-me-development-only"
DEV_BOOTSTRAP_PASSWORD = "ChangeThisAdminPassword123!"
_password_hash = PasswordHash.recommended()
_dummy_hash = _password_hash.hash("BattleReef-dummy-authentication-secret")
settings = get_settings()


class AuthService:
    def __init__(self, db: Session | None):
        self.db = db

    @staticmethod
    def validate_security_config() -> None:
        if settings.app_env.lower() not in {"development", "test"}:
            if settings.auth_jwt_secret == DEV_JWT_SECRET or len(settings.auth_jwt_secret) < 32:
                raise RuntimeError("AUTH_JWT_SECRET must be replaced with a strong secret outside development")

    @staticmethod
    def hash_password(password: str) -> str:
        return _password_hash.hash(password)

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        return _password_hash.verify(password, password_hash)

    def get_user(self, username: str) -> UserRecord | None:
        if self.db is None:
            raise RuntimeError("database_session_required")
        return self.db.scalar(select(UserRecord).where(UserRecord.username == username))

    def authenticate(self, username: str, password: str) -> UserRecord | None:
        if self.db is None:
            raise RuntimeError("database_session_required")
        user = self.get_user(username)
        now = datetime.now(timezone.utc)

        if user is None:
            self.verify_password(password, _dummy_hash)
            return None

        if not user.active:
            self.verify_password(password, user.password_hash)
            return None

        if user.locked_until is not None and user.locked_until > now:
            self.verify_password(password, user.password_hash)
            return None

        if not self.verify_password(password, user.password_hash):
            attempts = int(user.failed_login_attempts or 0) + 1
            user.failed_login_attempts = attempts
            if attempts >= max(1, int(settings.auth_max_failed_attempts)):
                user.locked_until = now + timedelta(minutes=max(1, int(settings.auth_lockout_minutes)))
                user.failed_login_attempts = 0
            self.db.commit()
            return None

        if user.failed_login_attempts or user.locked_until is not None:
            user.failed_login_attempts = 0
            user.locked_until = None
            self.db.commit()
            self.db.refresh(user)
        return user

    def issue_token(self, user: UserRecord) -> tuple[str, int]:
        ttl = int(settings.auth_token_ttl_minutes) * 60
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user.username,
            "role": user.role,
            "principal_type": user.principal_type,
            "ver": user.token_version,
            "iat": now,
            "exp": now + timedelta(seconds=ttl),
            "iss": settings.auth_token_issuer,
            "aud": settings.auth_token_audience,
        }
        return jwt.encode(payload, settings.auth_jwt_secret, algorithm="HS256"), ttl

    @staticmethod
    def decode_token(token: str) -> dict:
        return jwt.decode(token, settings.auth_jwt_secret, algorithms=["HS256"], issuer=settings.auth_token_issuer, audience=settings.auth_token_audience)

    @staticmethod
    def role_allows(actual: str, required: str) -> bool:
        return ROLE_LEVEL.get(actual, -1) >= ROLE_LEVEL[required]

    def create_user(self, username: str, password: str, role: str, principal_type: str = "user") -> UserRecord:
        if self.db is None:
            raise RuntimeError("database_session_required")
        if self.get_user(username) is not None:
            raise ValueError("username_already_exists")
        record = UserRecord(
            username=username,
            password_hash=self.hash_password(password),
            role=role,
            principal_type=principal_type,
            token_version=1,
            failed_login_attempts=0,
            locked_until=None,
            active=True,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def list_users(self) -> list[UserRecord]:
        if self.db is None:
            raise RuntimeError("database_session_required")
        return list(self.db.scalars(select(UserRecord).order_by(UserRecord.username.asc())).all())

    def update_user(self, username: str, *, role: str | None, active: bool | None, password: str | None) -> UserRecord | None:
        if self.db is None:
            raise RuntimeError("database_session_required")
        user = self.get_user(username)
        if user is None:
            return None
        security_state_changed = False
        if role is not None and role != user.role:
            user.role = role
            security_state_changed = True
        if active is not None and active != user.active:
            user.active = active
            security_state_changed = True
        if password is not None:
            user.password_hash = self.hash_password(password)
            security_state_changed = True
        if password is not None or active is True:
            user.failed_login_attempts = 0
            user.locked_until = None
        if security_state_changed:
            user.token_version = int(user.token_version or 0) + 1
        self.db.commit()
        self.db.refresh(user)
        return user

    def ensure_bootstrap_admin(self) -> None:
        if self.db is None:
            raise RuntimeError("database_session_required")

        existing_admin = self.db.scalar(
            select(UserRecord)
            .where(UserRecord.role == "administrator", UserRecord.active.is_(True))
            .limit(1)
        )
        if existing_admin is not None:
            return

        username = settings.auth_bootstrap_admin_username.strip()
        password = settings.auth_bootstrap_admin_password
        if not username or not password:
            raise RuntimeError("No active administrator exists; configure bootstrap administrator credentials")
        if settings.app_env.lower() not in {"development", "test"}:
            if len(password) < 12 or password == DEV_BOOTSTRAP_PASSWORD:
                raise RuntimeError("Bootstrap administrator password must be replaced outside development")

        existing = self.get_user(username)
        if existing is not None:
            raise RuntimeError("Bootstrap username already exists but is not an active administrator")
        self.create_user(username, password, "administrator", "user")
