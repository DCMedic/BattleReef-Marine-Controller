from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=256)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    username: str
    role: str


class PrincipalResponse(BaseModel):
    username: str
    role: str


class UserCreateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=12, max_length=256)
    role: str = Field(pattern=r"^(viewer|operator|engineer|administrator)$")


class UserUpdateRequest(BaseModel):
    role: str | None = Field(default=None, pattern=r"^(viewer|operator|engineer|administrator)$")
    active: bool | None = None
    password: str | None = Field(default=None, min_length=12, max_length=256)


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    active: bool
