"""Add language support columns

Revision ID: add_language_support
Create Date: 2025-01-22 20:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'add_language_support'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add language columns to all relevant tables
    op.add_column('user', sa.Column('preferred_language', sa.String(10), nullable=False, server_default='en'))
    op.add_column('medical_record', sa.Column('language', sa.String(10), nullable=False, server_default='en'))
    op.add_column('prescription', sa.Column('language', sa.String(10), nullable=False, server_default='en'))
    op.add_column('medical_document', sa.Column('language', sa.String(10), nullable=False, server_default='en'))
    op.add_column('chat_session', sa.Column('preferred_language', sa.String(10), nullable=False, server_default='en'))
    op.add_column('chat_message', sa.Column('language', sa.String(10), nullable=False, server_default='en'))

def downgrade():
    # Remove language columns from all tables
    op.drop_column('user', 'preferred_language')
    op.drop_column('medical_record', 'language')
    op.drop_column('prescription', 'language')
    op.drop_column('medical_document', 'language')
    op.drop_column('chat_session', 'preferred_language')
    op.drop_column('chat_message', 'language')
