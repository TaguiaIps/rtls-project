from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from rtls_api.audit import write_audit_event
from rtls_api.config import Settings
from rtls_api.db import get_db
from rtls_api.models import RefreshSession, User, UserRole, UserStatus
from rtls_api.schemas import (
    CurrentUserResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
)
from rtls_api.security import (
    TokenError,
    decode_token,
    hash_password,
    hash_token,
    issue_access_token,
    issue_refresh_token,
    verify_password,
)
from rtls_api.session_store import RefreshSessionStore

AUTH_ROUTER = APIRouter(prefix="/api/auth", tags=["auth"])
USER_ROUTER = APIRouter(prefix="/api", tags=["users"])
bearer_scheme = HTTPBearer(auto_error=False)


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_session_store(request: Request) -> RefreshSessionStore:
    return request.app.state.session_store


def normalize_email(email: str) -> str:
    return email.strip().lower()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    try:
        payload = decode_token(credentials.credentials, settings, expected_type="access")
    except TokenError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error)) from error

    user_id = str(payload["sub"])
    user = db.get(User, user_id)
    if user is None or user.status != UserStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    return user


def require_role(required_role: UserRole):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role != required_role.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{required_role.value} access required",
            )
        return user

    return dependency


def _issue_tokens_for_session(
    *,
    user: User,
    refresh_session: RefreshSession,
    settings: Settings,
    session_store: RefreshSessionStore,
) -> TokenResponse:
    access_token, access_expires_at = issue_access_token(settings, user)
    refresh_token, refresh_expires_at = issue_refresh_token(settings, user, refresh_session.id)
    refresh_session.expires_at = refresh_expires_at
    ttl_seconds = max(1, int((refresh_expires_at - datetime.now(timezone.utc)).total_seconds()))
    session_store.set_token_hash(refresh_session.id, hash_token(refresh_token), ttl_seconds)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in_seconds=max(
            1,
            int((access_expires_at - datetime.now(timezone.utc)).total_seconds()),
        ),
        role=user.role,
    )


def _revoke_refresh_session(
    *,
    refresh_session: RefreshSession,
    session_store: RefreshSessionStore,
) -> None:
    refresh_session.revoked_at = datetime.now(timezone.utc)
    session_store.delete_session(refresh_session.id)


@AUTH_ROUTER.post("/token", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    session_store: RefreshSessionStore = Depends(get_session_store),
) -> TokenResponse:
    email = normalize_email(payload.email)
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(payload.password, user.password_hash):
        write_audit_event(
            db,
            action_category="authentication",
            action_type="auth.login.failure",
            actor_email=email,
            details={"reason": "invalid_credentials"},
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if user.status != UserStatus.ACTIVE.value:
        write_audit_event(
            db,
            action_category="authentication",
            action_type="auth.login.failure",
            actor=user,
            details={"reason": "disabled_account"},
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    refresh_session = RefreshSession(
        user_id=user.id,
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        expires_at=datetime.now(timezone.utc),
    )
    db.add(refresh_session)
    user.last_login_at = datetime.now(timezone.utc)
    db.flush()
    write_audit_event(
        db,
        action_category="authentication",
        action_type="auth.login.success",
        actor=user,
        target_type="refresh_session",
        target_id=refresh_session.id,
    )
    tokens = _issue_tokens_for_session(
        user=user,
        refresh_session=refresh_session,
        settings=settings,
        session_store=session_store,
    )
    db.commit()
    return tokens


@AUTH_ROUTER.post("/refresh", response_model=TokenResponse)
def refresh_token(
    payload: RefreshRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    session_store: RefreshSessionStore = Depends(get_session_store),
) -> TokenResponse:
    try:
        token_payload = decode_token(payload.refresh_token, settings, expected_type="refresh")
    except TokenError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error)) from error

    session_id = str(token_payload["sid"])
    refresh_session = db.get(RefreshSession, session_id)
    if refresh_session is None or refresh_session.revoked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh session",
        )

    expected_hash = session_store.get_token_hash(session_id)
    presented_hash = hash_token(payload.refresh_token)
    if expected_hash is None or presented_hash != expected_hash:
        _revoke_refresh_session(refresh_session=refresh_session, session_store=session_store)
        write_audit_event(
            db,
            action_category="authentication",
            action_type="auth.refresh.rejected",
            actor=refresh_session.user,
            target_type="refresh_session",
            target_id=refresh_session.id,
            details={"reason": "rotated_or_replayed"},
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh session",
        )

    user = refresh_session.user
    if user.status != UserStatus.ACTIVE.value:
        _revoke_refresh_session(refresh_session=refresh_session, session_store=session_store)
        write_audit_event(
            db,
            action_category="authentication",
            action_type="auth.refresh.rejected",
            actor=user,
            target_type="refresh_session",
            target_id=refresh_session.id,
            details={"reason": "disabled_account"},
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh session",
        )

    tokens = _issue_tokens_for_session(
        user=user,
        refresh_session=refresh_session,
        settings=settings,
        session_store=session_store,
    )
    write_audit_event(
        db,
        action_category="authentication",
        action_type="auth.refresh.success",
        actor=user,
        target_type="refresh_session",
        target_id=refresh_session.id,
    )
    db.commit()
    return tokens


@AUTH_ROUTER.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    payload: LogoutRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    session_store: RefreshSessionStore = Depends(get_session_store),
) -> None:
    try:
        token_payload = decode_token(payload.refresh_token, settings, expected_type="refresh")
    except TokenError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error)) from error

    refresh_session = db.get(RefreshSession, str(token_payload["sid"]))
    if refresh_session is None or refresh_session.revoked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh session",
        )

    expected_hash = session_store.get_token_hash(refresh_session.id)
    presented_hash = hash_token(payload.refresh_token)
    if expected_hash is None or presented_hash != expected_hash:
        # A stale rotated token must not revoke the active session during logout.
        write_audit_event(
            db,
            action_category="authentication",
            action_type="auth.logout.rejected",
            actor=refresh_session.user,
            target_type="refresh_session",
            target_id=refresh_session.id,
            details={"reason": "rotated_or_replayed"},
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh session",
        )

    if refresh_session.revoked_at is None:
        _revoke_refresh_session(refresh_session=refresh_session, session_store=session_store)
        write_audit_event(
            db,
            action_category="authentication",
            action_type="auth.logout",
            actor=refresh_session.user,
            target_type="refresh_session",
            target_id=refresh_session.id,
        )
        db.commit()


@USER_ROUTER.get("/me", response_model=CurrentUserResponse)
def read_current_user(user: User = Depends(get_current_user)) -> CurrentUserResponse:
    return CurrentUserResponse.model_validate(user)


def create_user(
    db: Session,
    *,
    email: str,
    password: str,
    role: UserRole,
    display_name: str | None = None,
    status_value: UserStatus = UserStatus.ACTIVE,
) -> User:
    user = User(
        email=normalize_email(email),
        display_name=display_name,
        password_hash=hash_password(password),
        role=role.value,
        status=status_value.value,
    )
    db.add(user)
    db.flush()
    return user
