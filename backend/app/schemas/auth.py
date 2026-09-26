import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def validate_password(value: str) -> str:
    if len(value) < 8 or not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value) or not re.search(r"[^A-Za-z\d]", value):
        raise ValueError("Password must have 8+ characters, a letter, a number and a special character")
    return value


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    _validate_password = field_validator("password")(validate_password)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    is_email_verified: bool
    email_verified_at: datetime | None
    created_at: datetime


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str = Field(min_length=20)
    password: str = Field(min_length=8, max_length=128)

    _validate_password = field_validator("password")(validate_password)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)

    _validate_password = field_validator("new_password")(validate_password)


class ChangeEmailRequest(BaseModel):
    new_email: EmailStr
    password: str


class DeleteAccountRequest(BaseModel):
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str | None = Field(default=None, min_length=20)


class SessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    expires_at: datetime
    last_used_at: datetime | None


class MessageResponse(BaseModel):
    message: str
