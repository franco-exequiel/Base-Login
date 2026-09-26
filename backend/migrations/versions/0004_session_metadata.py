"""add session metadata"""
from alembic import op
import sqlalchemy as sa

revision = "0004_session_metadata"
down_revision = "0003_auth_hardening"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("refresh_tokens", sa.Column("user_agent", sa.String(length=512), nullable=True))
    op.add_column("refresh_tokens", sa.Column("ip_address", sa.String(length=45), nullable=True))
    op.add_column("refresh_tokens", sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("refresh_tokens", "last_used_at")
    op.drop_column("refresh_tokens", "ip_address")
    op.drop_column("refresh_tokens", "user_agent")
