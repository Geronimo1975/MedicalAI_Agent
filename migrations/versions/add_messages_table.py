"""Add messages table

Revision ID: add_messages_table
Create Date: 2025-01-22 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'add_messages_table'
down_revision = 'add_chat_sessions'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.Column('recipient_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('subject', sa.Text(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='unread'),
        sa.Column('category', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('attachment_url', sa.Text(), nullable=True),
        sa.Column('is_encrypted', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['recipient_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('messages')
