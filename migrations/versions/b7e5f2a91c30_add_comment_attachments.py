"""add comment attachments

Revision ID: b7e5f2a91c30
Revises: a91f6c3d8e20
"""
from alembic import op
import sqlalchemy as sa

revision = "b7e5f2a91c30"
down_revision = "a91f6c3d8e20"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("file_attachments", sa.Column("comment_id", sa.UUID(), nullable=True))
    op.create_foreign_key("fk_file_attachments_comment_id", "file_attachments", "comments", ["comment_id"], ["id"])
    op.create_index("ix_file_attachments_comment_id", "file_attachments", ["comment_id"])
    op.create_check_constraint("ck_file_attachment_one_parent", "file_attachments", "(task_id IS NOT NULL)::integer + (project_id IS NOT NULL)::integer + (comment_id IS NOT NULL)::integer = 1")

def downgrade():
    op.drop_constraint("ck_file_attachment_one_parent", "file_attachments", type_="check")
    op.drop_index("ix_file_attachments_comment_id", table_name="file_attachments")
    op.drop_constraint("fk_file_attachments_comment_id", "file_attachments", type_="foreignkey")
    op.drop_column("file_attachments", "comment_id")
