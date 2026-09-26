import secrets
from typing import Annotated

import jwt
from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import get_db
from app.models import User
from app.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)
DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    header_token: Annotated[str | None, Depends(oauth2_scheme)],
    access_cookie: Annotated[str | None, Cookie(alias="access_token")] = None,
    db: DbSession = None,
) -> User:
    token = header_token or access_cookie
    credentials_error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    if not token:
        raise credentials_error
    try:
        user_id = decode_access_token(token)
    except (KeyError, TypeError, ValueError, jwt.InvalidTokenError) as error:
        raise credentials_error from error
    user = db.get(User, user_id)
    if user is None:
        raise credentials_error
    return user


def require_csrf(
    request: Request,
    csrf_cookie: Annotated[str | None, Cookie(alias="csrf_token")] = None,
    csrf_header: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> None:
    if not csrf_cookie or not csrf_header or not secrets.compare_digest(csrf_cookie, csrf_header):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed")
