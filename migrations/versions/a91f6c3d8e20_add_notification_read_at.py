"""add notification read timestamp

Revision ID: a91f6c3d8e20
Revises: 3d674fd1e4b2
Create Date: 2026-08-14
"""

from alembic import op
import sqlalchemy as sa


revision = "a91f6c3d8e20"
down_revision = "3d674fd1e4b2"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("notifications", sa.Column("read_at", sa.DateTime(timezone=True), nullable=True))


def downgrade():
    op.drop_column("notifications", "read_at")
