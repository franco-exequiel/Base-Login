from datetime import datetime, timezone

from sqlalchemy import delete, or_
from sqlalchemy.orm import Session

from app.models import EmailVerificationToken, PasswordResetToken, RefreshToken


def cleanup_expired_tokens(db: Session) -> None:
    now = datetime.now(timezone.utc)
    db.execute(delete(EmailVerificationToken).where(EmailVerificationToken.expires_at < now))
    db.execute(delete(PasswordResetToken).where(PasswordResetToken.expires_at < now))
    db.execute(delete(RefreshToken).where(or_(RefreshToken.expires_at < now, RefreshToken.revoked_at < now)))
    db.commit()
