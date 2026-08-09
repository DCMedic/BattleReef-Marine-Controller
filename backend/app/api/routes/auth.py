from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.authz import Principal, current_principal, require_role
from app.db.session import get_db
from app.schemas.auth import LoginRequest, PrincipalResponse, TokenResponse, UserCreateRequest, UserResponse, UserUpdateRequest
from app.schemas.audit import AuditEventCreate
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    service = AuthService(db)
    user = service.authenticate(payload.username, payload.password)
    if user is None:
        AuditService(db).append(AuditEventCreate(event_type="auth.login_failed", severity="warning", outcome="denied", source="http_auth", actor_type="principal", actor_id=payload.username, message="Authentication failed", details={}))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")
    token, ttl = service.issue_token(user)
    AuditService(db).append(AuditEventCreate(event_type="auth.login_succeeded", severity="info", outcome="success", source="http_auth", actor_type=user.principal_type, actor_id=user.username, message="Authentication succeeded", details={"role": user.role, "principal_type": user.principal_type}))
    return TokenResponse(access_token=token, expires_in=ttl, username=user.username, role=user.role, principal_type=user.principal_type)


@router.get("/me", response_model=PrincipalResponse)
def me(principal: Principal = Depends(current_principal)) -> PrincipalResponse:
    return PrincipalResponse(username=principal.username, role=principal.role, principal_type=principal.principal_type)


@router.get("/users", response_model=list[UserResponse])
def list_users(_: Principal = Depends(require_role("administrator")), db: Session = Depends(get_db)):
    return [UserResponse(id=u.id, username=u.username, role=u.role, principal_type=u.principal_type, active=u.active) for u in AuthService(db).list_users()]


@router.post("/users", response_model=UserResponse)
def create_user(payload: UserCreateRequest, principal: Principal = Depends(require_role("administrator")), db: Session = Depends(get_db)):
    try:
        user = AuthService(db).create_user(payload.username, payload.password, payload.role, payload.principal_type)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    AuditService(db).append(AuditEventCreate(event_type="auth.principal_created", severity="info", outcome="success", source="http_auth", actor_type=principal.principal_type, actor_id=principal.username, entity_type="principal", entity_id=user.username, message="Authenticated principal created", details={"role": user.role, "principal_type": user.principal_type}))
    return UserResponse(id=user.id, username=user.username, role=user.role, principal_type=user.principal_type, active=user.active)


@router.put("/users/{username}", response_model=UserResponse)
def update_user(username: str, payload: UserUpdateRequest, principal: Principal = Depends(require_role("administrator")), db: Session = Depends(get_db)):
    if username == principal.username and payload.active is False:
        raise HTTPException(status_code=400, detail="cannot_disable_current_administrator")
    user = AuthService(db).update_user(username, role=payload.role, active=payload.active, password=payload.password)
    if user is None:
        raise HTTPException(status_code=404, detail="user_not_found")
    AuditService(db).append(AuditEventCreate(event_type="auth.principal_updated", severity="warning", outcome="success", source="http_auth", actor_type=principal.principal_type, actor_id=principal.username, entity_type="principal", entity_id=user.username, message="Authenticated principal updated", details={"role": user.role, "principal_type": user.principal_type, "active": user.active, "password_changed": payload.password is not None}))
    return UserResponse(id=user.id, username=user.username, role=user.role, principal_type=user.principal_type, active=user.active)
