from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.authz import Principal, require_role
from app.services.auth_service import AuthService


class FakeSession:
    def __init__(self, user):
        self.user = user
        self.commits = 0

    def scalar(self, _stmt):
        return self.user

    def commit(self):
        self.commits += 1

    def refresh(self, _record):
        return None


def test_role_dependency_denies_insufficient_role() -> None:
    engineer_only = require_role("engineer")
    engineer = Principal(username="eng", role="engineer", principal_type="user")
    viewer = Principal(username="view", role="viewer", principal_type="user")

    assert engineer_only(engineer) == engineer
    with pytest.raises(HTTPException) as exc_info:
        engineer_only(viewer)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "role_engineer_required"


def test_failed_password_attempts_lock_account() -> None:
    password = "Correct-password-for-lockout-123!"
    user = SimpleNamespace(
        username="operator",
        password_hash=AuthService.hash_password(password),
        role="operator",
        principal_type="user",
        token_version=1,
        active=True,
        failed_login_attempts=0,
        locked_until=None,
    )
    session = FakeSession(user)
    service = AuthService(session)

    for _ in range(5):
        assert service.authenticate("operator", "wrong-password") is None

    assert user.locked_until is not None
    assert service.authenticate("operator", password) is None


def test_unknown_username_fails_without_account_object() -> None:
    service = AuthService(FakeSession(None))
    assert service.authenticate("does-not-exist", "arbitrary-password") is None
