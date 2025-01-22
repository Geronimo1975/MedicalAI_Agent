"""Add appointment optimizer tables

Revision ID: add_appointment_optimizer_tables
Create Date: 2025-01-22 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, ARRAY

revision = 'add_appointment_optimizer_tables'
down_revision = 'add_preventive_care_recommendations'
branch_labels = None
depends_on = None

def upgrade():
    # Modify existing appointments table
    with op.batch_alter_table('appointments') as batch_op:
        batch_op.add_column(sa.Column('end_time', sa.DateTime(), nullable=False))
        batch_op.add_column(sa.Column('type', sa.String(20), nullable=False))
        batch_op.add_column(sa.Column('priority', sa.String(20), nullable=False, server_default='medium'))
        batch_op.add_column(sa.Column('duration', sa.Integer(), nullable=False, server_default='30'))
        batch_op.add_column(sa.Column('symptoms', ARRAY(sa.String()), nullable=True))
        batch_op.add_column(sa.Column('preferred_time_slots', JSONB(), nullable=True))
        batch_op.add_column(sa.Column('required_equipment', ARRAY(sa.String()), nullable=True))
        batch_op.add_column(sa.Column('scheduling_score', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('last_rescheduled', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('cancellation_reason', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('reminder_sent', sa.Boolean(), nullable=False, server_default='false'))
        
        # Modify status enum
        batch_op.alter_column('status',
                            type_=sa.String(20),
                            existing_type=sa.String(20),
                            postgresql_using="status::text::varchar(20)")

    # Create doctor_schedule table
    op.create_table(
        'doctor_schedule',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('doctor_id', sa.Integer(), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.String(5), nullable=False),
        sa.Column('end_time', sa.String(5), nullable=False),
        sa.Column('is_available', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('break_start', sa.String(5), nullable=True),
        sa.Column('break_end', sa.String(5), nullable=True),
        sa.Column('max_appointments_per_day', sa.Integer(), nullable=True),
        sa.Column('specialty_equipment', ARRAY(sa.String()), nullable=True),
        sa.ForeignKeyConstraint(['doctor_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    # Drop doctor_schedule table
    op.drop_table('doctor_schedule')

    # Revert appointments table changes
    with op.batch_alter_table('appointments') as batch_op:
        batch_op.drop_column('end_time')
        batch_op.drop_column('type')
        batch_op.drop_column('priority')
        batch_op.drop_column('duration')
        batch_op.drop_column('symptoms')
        batch_op.drop_column('preferred_time_slots')
        batch_op.drop_column('required_equipment')
        batch_op.drop_column('scheduling_score')
        batch_op.drop_column('last_rescheduled')
        batch_op.drop_column('cancellation_reason')
        batch_op.drop_column('reminder_sent')
        
        # Revert status enum
        batch_op.alter_column('status',
                            type_=sa.String(20),
                            existing_type=sa.String(20),
                            postgresql_using="status::text::varchar(20)")
