"""add organization invitations

Revision ID: d2e9f6a4b7c1
Revises: c91e7a4b2f10
Create Date: 2026-08-14
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "d2e9f6a4b7c1"
down_revision = "c91e7a4b2f10"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "organization_invitations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("inviter_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["inviter_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "email", "status", name="uq_organization_invitation_active"),
        sa.UniqueConstraint("token"),
    )
    op.create_index("ix_organization_invitations_organization_id", "organization_invitations", ["organization_id"])
    op.create_index("ix_organization_invitations_token", "organization_invitations", ["token"])


def downgrade():
    op.drop_index("ix_organization_invitations_token", table_name="organization_invitations")
    op.drop_index("ix_organization_invitations_organization_id", table_name="organization_invitations")
    op.drop_table("organization_invitations")
