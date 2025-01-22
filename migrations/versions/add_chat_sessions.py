"""Add chat sessions table

Revision ID: add_chat_sessions
Create Date: 2025-01-22 20:20:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'add_chat_sessions'
down_revision = 'add_language_support'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('triage_level', sa.String(20), nullable=True),
        sa.Column('total_risk', sa.Integer(), nullable=True),
        sa.Column('severity_score', sa.Integer(), nullable=True),
        sa.Column('correlation_score', sa.Integer(), nullable=True),
        sa.Column('risk_multiplier', sa.Integer(), nullable=True),
        sa.Column('symptoms', sa.ARRAY(sa.String()), nullable=True),
        sa.Column('recommendations', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('chat_sessions')
