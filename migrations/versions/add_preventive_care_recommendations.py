"""Add preventive care recommendations table

Revision ID: add_preventive_care_recommendations
Create Date: 2025-01-22 21:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = 'add_preventive_care_recommendations'
down_revision = 'add_messages_table'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'preventive_care_recommendations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('category', sa.String(20), nullable=False),
        sa.Column('priority', sa.String(20), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('reasoning', sa.Text(), nullable=False),
        sa.Column('suggested_timeline', sa.Text(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('ai_confidence_score', sa.Integer(), nullable=False),
        sa.Column('data_points', JSONB(), nullable=False),
        sa.Column('source_references', JSONB(), nullable=True),
        sa.ForeignKeyConstraint(['patient_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('preventive_care_recommendations')
