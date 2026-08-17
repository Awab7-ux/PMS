"""add chat system tables

Revision ID: e5f8a2c1d4e9
Revises: d2e9f6a4b7c1
Create Date: 2026-08-17 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'e5f8a2c1d4e9'
down_revision = 'd2e9f6a4b7c1'
branch_labels = None
depends_on = None


def upgrade():
    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('organization_id', postgresql.UUID(), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('created_by', postgresql.UUID(), nullable=False),
        sa.Column('project_id', postgresql.UUID(), nullable=True),
        sa.Column('team_id', postgresql.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("type IN ('direct', 'group', 'project', 'team')", name='ck_conversation_type'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversations_organization_id'), 'conversations', ['organization_id'], unique=False)
    op.create_index(op.f('ix_conversations_project_id'), 'conversations', ['project_id'], unique=False)
    op.create_index(op.f('ix_conversations_team_id'), 'conversations', ['team_id'], unique=False)

    # Create conversation_members table
    op.create_table(
        'conversation_members',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(), nullable=False),
        sa.Column('user_id', postgresql.UUID(), nullable=False),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_read_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('conversation_id', 'user_id', name='uq_conversation_member')
    )
    op.create_index(op.f('ix_conversation_members_conversation_id'), 'conversation_members', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_conversation_members_user_id'), 'conversation_members', ['user_id'], unique=False)

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(), nullable=False),
        sa.Column('sender_id', postgresql.UUID(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_messages_conversation_id'), 'messages', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_messages_sender_id'), 'messages', ['sender_id'], unique=False)
    op.create_index(op.f('ix_messages_created_at'), 'messages', ['created_at'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index(op.f('ix_messages_created_at'), table_name='messages')
    op.drop_index(op.f('ix_messages_sender_id'), table_name='messages')
    op.drop_index(op.f('ix_messages_conversation_id'), table_name='messages')

    # Drop messages table
    op.drop_table('messages')

    # Drop indexes
    op.drop_index(op.f('ix_conversation_members_user_id'), table_name='conversation_members')
    op.drop_index(op.f('ix_conversation_members_conversation_id'), table_name='conversation_members')

    # Drop conversation_members table
    op.drop_table('conversation_members')

    # Drop indexes
    op.drop_index(op.f('ix_conversations_team_id'), table_name='conversations')
    op.drop_index(op.f('ix_conversations_project_id'), table_name='conversations')
    op.drop_index(op.f('ix_conversations_organization_id'), table_name='conversations')

    # Drop conversations table
    op.drop_table('conversations')
