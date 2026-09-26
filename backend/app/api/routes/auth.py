import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.api.dependencies_security import DbSession, get_current_user, require_csrf
from app.core.config import settings
from app.email_service import send_password_reset_email, send_verification_email
from app.models import EmailVerificationToken, PasswordResetToken, RefreshToken, User
from app.rate_limit import enforce_rate_limit
from app.schemas.auth_security import ChangeEmailRequest, ChangePasswordRequest, DeleteAccountRequest, PasswordResetConfirm, PasswordResetRequest, RefreshTokenRequest, SessionRead, UserCreate, UserRead
from app.schemas.email_verification import EmailVerificationRequest, MessageResponse
from app.security import create_access_token, create_opaque_token, hash_opaque_token, hash_password, verify_password
from app.token_cleanup import cleanup_expired_tokens

router = APIRouter(prefix="/auth", tags=["auth"])
Csrf = Annotated[None, Depends(require_csrf)]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _client_key(request: Request, action: str) -> str:
    host = request.client.host if request.client else "unknown"
    return f"{action}:{host}"


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    csrf_token = secrets.token_urlsafe(32)
    common = {"secure": settings.cookie_secure, "samesite": settings.cookie_samesite, "path": "/"}
    response.set_cookie("access_token", access_token, httponly=True, max_age=settings.access_token_minutes * 60, **common)
    response.set_cookie("refresh_token", refresh_token, httponly=True, max_age=settings.refresh_token_days * 86400, **common)
    response.set_cookie("csrf_token", csrf_token, httponly=False, max_age=settings.refresh_token_days * 86400, **common)


def _clear_auth_cookies(response: Response) -> None:
    for name in ("access_token", "refresh_token", "csrf_token"):
        response.delete_cookie(name, path="/")


def _create_email_verification_token(user_id: int, db: DbSession) -> str:
    raw_token, token_hash = create_opaque_token()
    now = _now()
    db.add(EmailVerificationToken(user_id=user_id, token_hash=token_hash, expires_at=now + timedelta(minutes=settings.email_verification_minutes), created_at=now))
    db.commit()
    return raw_token


def _create_refresh_token(user_id: int, request: Request, db: DbSession) -> str:
    raw_token, token_hash = create_opaque_token()
    now = _now()
    db.add(RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=now + timedelta(days=settings.refresh_token_days), user_agent=request.headers.get("user-agent"), ip_address=request.client.host if request.client else None, created_at=now))
    db.commit()
    return raw_token


def _revoke_user_sessions(user_id: int, db: DbSession) -> None:
    now = _now()
    for session in db.scalars(select(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))):
        session.revoked_at = now


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: DbSession) -> User:
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=400, detail="Could not create account")
    user = User(email=email, hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    raw_token = _create_email_verification_token(user.id, db)
    try:
        send_verification_email(user.email, raw_token)
    except Exception as error:
        raise HTTPException(status_code=503, detail="Could not send verification email") from error
    return user


@router.get("/verify-email", response_model=MessageResponse)
def verify_email(token: str, db: DbSession) -> MessageResponse:
    record = db.scalar(select(EmailVerificationToken).where(EmailVerificationToken.token_hash == hash_opaque_token(token)))
    now = _now()
    if record is None or record.used_at is not None or record.expires_at < now:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link")
    user = db.get(User, record.user_id)
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid verification link")
    user.is_email_verified = True
    user.email_verified_at = now
    record.used_at = now
    db.commit()
    return MessageResponse(message="Email verified successfully")


@router.post("/resend-verification", response_model=MessageResponse)
def resend_verification(payload: EmailVerificationRequest, request: Request, db: DbSession) -> MessageResponse:
    enforce_rate_limit(_client_key(request, "resend-verification"), 3, 900)
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or user.is_email_verified:
        return MessageResponse(message="If the account exists, a verification email was sent")
    raw_token = _create_email_verification_token(user.id, db)
    send_verification_email(user.email, raw_token)
    return MessageResponse(message="If the account exists, a verification email was sent")


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(payload: PasswordResetRequest, request: Request, db: DbSession) -> MessageResponse:
    enforce_rate_limit(_client_key(request, "forgot-password"), 3, 900)
    cleanup_expired_tokens(db)
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None:
        return MessageResponse(message="If the account exists, a password reset email was sent")
    raw_token, token_hash = create_opaque_token()
    now = _now()
    db.add(PasswordResetToken(user_id=user.id, token_hash=token_hash, expires_at=now + timedelta(minutes=settings.password_reset_minutes), created_at=now))
    db.commit()
    try:
        send_password_reset_email(user.email, raw_token)
    except Exception as error:
        raise HTTPException(status_code=503, detail="Could not send password reset email") from error
    return MessageResponse(message="If the account exists, a password reset email was sent")


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(payload: PasswordResetConfirm, db: DbSession) -> MessageResponse:
    record = db.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash == hash_opaque_token(payload.token)))
    now = _now()
    if record is None or record.used_at is not None or record.expires_at < now:
        raise HTTPException(status_code=400, detail="Invalid or expired password reset link")
    user = db.get(User, record.user_id)
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid password reset link")
    user.hashed_password = hash_password(payload.password)
    record.used_at = now
    _revoke_user_sessions(user.id, db)
    db.commit()
    return MessageResponse(message="Password reset successfully")


@router.post("/login", response_model=MessageResponse)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], request: Request, response: Response, db: DbSession) -> MessageResponse:
    enforce_rate_limit(_client_key(request, f"login:{form.username.lower()}"), 5, 60)
    cleanup_expired_tokens(db)
    user = db.scalar(select(User).where(User.email == form.username.lower()))
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if not user.is_email_verified:
        raise HTTPException(status_code=403, detail="Please verify your email before logging in")
    _set_auth_cookies(response, create_access_token(user.id), _create_refresh_token(user.id, request, db))
    return MessageResponse(message="Logged in successfully")


@router.post("/refresh", response_model=MessageResponse)
def refresh(payload: RefreshTokenRequest, request: Request, response: Response, _csrf: Csrf, db: DbSession, refresh_cookie: Annotated[str | None, Cookie(alias="refresh_token")] = None) -> MessageResponse:
    enforce_rate_limit(_client_key(request, "refresh"), 20, 60)
    raw_refresh_token = refresh_cookie or payload.refresh_token
    if not raw_refresh_token:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    record = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_opaque_token(raw_refresh_token)))
    now = _now()
    if record is None or record.revoked_at is not None or record.expires_at < now:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    user = db.get(User, record.user_id)
    if user is None or not user.is_email_verified:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    record.revoked_at = now
    record.last_used_at = now
    db.commit()
    _set_auth_cookies(response, create_access_token(user.id), _create_refresh_token(user.id, request, db))
    return MessageResponse(message="Token refreshed successfully")


@router.post("/logout", response_model=MessageResponse)
def logout(payload: RefreshTokenRequest, response: Response, _csrf: Csrf, db: DbSession, refresh_cookie: Annotated[str | None, Cookie(alias="refresh_token")] = None) -> MessageResponse:
    raw_refresh_token = refresh_cookie or payload.refresh_token
    if raw_refresh_token:
        record = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_opaque_token(raw_refresh_token)))
        if record is not None and record.revoked_at is None:
            record.revoked_at = _now()
            db.commit()
    _clear_auth_cookies(response)
    return MessageResponse(message="Logged out successfully")


@router.post("/change-password", response_model=MessageResponse)
def change_password(payload: ChangePasswordRequest, response: Response, _csrf: Csrf, current_user: Annotated[User, Depends(get_current_user)], db: DbSession) -> MessageResponse:
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.hashed_password = hash_password(payload.new_password)
    _revoke_user_sessions(current_user.id, db)
    db.commit()
    _clear_auth_cookies(response)
    return MessageResponse(message="Password changed successfully. Please log in again")


@router.post("/change-email", response_model=MessageResponse)
def change_email(payload: ChangeEmailRequest, response: Response, _csrf: Csrf, current_user: Annotated[User, Depends(get_current_user)], db: DbSession) -> MessageResponse:
    new_email = payload.new_email.lower()
    if not verify_password(payload.password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Password is incorrect")
    if db.scalar(select(User).where(User.email == new_email, User.id != current_user.id)):
        raise HTTPException(status_code=400, detail="Could not change email")
    current_user.email = new_email
    current_user.is_email_verified = False
    current_user.email_verified_at = None
    _revoke_user_sessions(current_user.id, db)
    db.commit()
    raw_token = _create_email_verification_token(current_user.id, db)
    send_verification_email(new_email, raw_token)
    _clear_auth_cookies(response)
    return MessageResponse(message="Email changed. Check your new email to verify it")


@router.delete("/account", response_model=MessageResponse)
def delete_account(payload: DeleteAccountRequest, response: Response, _csrf: Csrf, current_user: Annotated[User, Depends(get_current_user)], db: DbSession) -> MessageResponse:
    if not verify_password(payload.password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Password is incorrect")
    db.delete(current_user)
    db.commit()
    _clear_auth_cookies(response)
    return MessageResponse(message="Account deleted successfully")


@router.get("/sessions", response_model=list[SessionRead])
def list_sessions(current_user: Annotated[User, Depends(get_current_user)], db: DbSession) -> list[RefreshToken]:
    return list(db.scalars(select(RefreshToken).where(RefreshToken.user_id == current_user.id, RefreshToken.revoked_at.is_(None), RefreshToken.expires_at > _now()).order_by(RefreshToken.created_at.desc())))


@router.delete("/sessions/{session_id}", response_model=MessageResponse)
def revoke_session(session_id: int, _csrf: Csrf, current_user: Annotated[User, Depends(get_current_user)], db: DbSession) -> MessageResponse:
    session = db.scalar(select(RefreshToken).where(RefreshToken.id == session_id, RefreshToken.user_id == current_user.id, RefreshToken.revoked_at.is_(None)))
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    session.revoked_at = _now()
    db.commit()
    return MessageResponse(message="Session revoked successfully")


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user
