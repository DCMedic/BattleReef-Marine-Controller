from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.auth_service import AuthService

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    username: str
    role: str


def current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> Principal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication_required")
    try:
        claims = AuthService.decode_token(credentials.credentials)
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_or_expired_token") from exc
    username = claims.get("sub")
    role = claims.get("role")
    user = AuthService(db).get_user(str(username)) if username else None
    if user is None or not user.active or user.role != role:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="principal_inactive_or_changed")
    return Principal(username=user.username, role=user.role)


def require_role(required: str):
    def dependency(principal: Principal = Depends(current_principal)) -> Principal:
        if not AuthService.role_allows(principal.role, required):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"role_{required}_required")
        return principal
    return dependency
