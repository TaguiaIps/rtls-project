from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from rtls_api.models import UserRole, UserStatus


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    role: str


class CurrentUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    display_name: str | None
    role: str
    status: str


class AdminUserUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, max_length=120)
    role: UserRole | None = None
    status: UserStatus | None = None


class AdminSummaryResponse(BaseModel):
    current_user: CurrentUserResponse
    managed_roles: list[str]
