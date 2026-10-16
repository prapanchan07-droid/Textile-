"""machine details, sensors, employee details, customers, yarn lots, shift notes, schedule plans

Additive only: new nullable columns (or columns with a server default) and new tables. No data is changed.

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-15 18:44:39.845301
"""
from alembic import op
import sqlalchemy as sa


revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('wv_customers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=20), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('segment', sa.String(length=30), nullable=True),
    sa.Column('city', sa.String(length=60), nullable=True),
    sa.Column('tier', sa.String(length=1), nullable=False),
    sa.Column('data_origin', sa.String(length=10), server_default='LIVE', nullable=False),
    sa.CheckConstraint("data_origin IN ('DEMO', 'IMPORTED', 'LIVE')", name=op.f('ck_wv_customers_data_origin')),
    sa.CheckConstraint("tier IN ('A', 'B', 'C')", name=op.f('ck_wv_customers_tier')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_wv_customers')),
    sa.UniqueConstraint('code', name=op.f('uq_wv_customers_code'))
    )
    op.create_table('wv_yarn_lots',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('lot_no', sa.String(length=40), nullable=False),
    sa.Column('yarn_count', sa.String(length=20), nullable=True),
    sa.Column('supplier', sa.String(length=80), nullable=True),
    sa.Column('received_on', sa.Date(), nullable=True),
    sa.Column('strength_cn_tex', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('elongation_pct', sa.Numeric(precision=4, scale=1), nullable=True),
    sa.Column('cv_pct', sa.Numeric(precision=4, scale=1), nullable=True),
    sa.Column('data_origin', sa.String(length=10), server_default='LIVE', nullable=False),
    sa.CheckConstraint("data_origin IN ('DEMO', 'IMPORTED', 'LIVE')", name=op.f('ck_wv_yarn_lots_data_origin')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_wv_yarn_lots')),
    sa.UniqueConstraint('lot_no', name=op.f('uq_wv_yarn_lots_lot_no'))
    )
    op.create_table('wv_schedule_plans',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('plan_ref', sa.String(length=40), nullable=False),
    sa.Column('status', sa.String(length=10), nullable=False),
    sa.Column('objective', sa.String(length=200), nullable=False),
    sa.Column('horizon_days', sa.Integer(), nullable=False),
    sa.Column('summary', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by_user_id', sa.String(length=50), nullable=True),
    sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('decided_by_user_id', sa.String(length=50), nullable=True),
    sa.Column('decision_note', sa.Text(), nullable=True),
    sa.Column('data_origin', sa.String(length=10), server_default='LIVE', nullable=False),
    sa.CheckConstraint("data_origin IN ('DEMO', 'IMPORTED', 'LIVE')", name=op.f('ck_wv_schedule_plans_data_origin')),
    sa.CheckConstraint("status IN ('PROPOSED', 'APPROVED', 'REJECTED')", name=op.f('ck_wv_schedule_plans_status')),
    sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], name=op.f('fk_wv_schedule_plans_created_by_user_id_users')),
    sa.ForeignKeyConstraint(['decided_by_user_id'], ['users.id'], name=op.f('fk_wv_schedule_plans_decided_by_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_wv_schedule_plans')),
    sa.UniqueConstraint('plan_ref', name=op.f('uq_wv_schedule_plans_plan_ref'))
    )
    op.create_table('wv_shift_notes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('note_ref', sa.String(length=40), nullable=False),
    sa.Column('shift_date', sa.Date(), nullable=False),
    sa.Column('shift_id', sa.Integer(), nullable=False),
    sa.Column('loom_id', sa.Integer(), nullable=True),
    sa.Column('category', sa.String(length=20), nullable=False),
    sa.Column('severity', sa.String(length=8), nullable=False),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('author_name', sa.String(length=80), nullable=True),
    sa.Column('created_by_user_id', sa.String(length=50), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('data_origin', sa.String(length=10), server_default='LIVE', nullable=False),
    sa.CheckConstraint("category IN ('HANDOVER', 'ISSUE', 'MAINTENANCE_REQUEST', 'QUALITY')", name=op.f('ck_wv_shift_notes_category')),
    sa.CheckConstraint("data_origin IN ('DEMO', 'IMPORTED', 'LIVE')", name=op.f('ck_wv_shift_notes_data_origin')),
    sa.CheckConstraint("severity IN ('INFO', 'WARNING', 'URGENT')", name=op.f('ck_wv_shift_notes_severity')),
    sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], name=op.f('fk_wv_shift_notes_created_by_user_id_users')),
    sa.ForeignKeyConstraint(['loom_id'], ['wv_looms.id'], name=op.f('fk_wv_shift_notes_loom_id_wv_looms')),
    sa.ForeignKeyConstraint(['shift_id'], ['wv_shifts.id'], name=op.f('fk_wv_shift_notes_shift_id_wv_shifts')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_wv_shift_notes')),
    sa.UniqueConstraint('note_ref', name=op.f('uq_wv_shift_notes_note_ref'))
    )
    op.create_index('ix_wv_shift_notes_date_shift', 'wv_shift_notes', ['shift_date', 'shift_id'], unique=False)
    op.add_column('wv_actions', sa.Column('verified_cause', sa.Text(), nullable=True))
    op.add_column('wv_beams', sa.Column('size_pickup_pct', sa.Numeric(precision=4, scale=1), nullable=True))
    op.add_column('wv_loom_readings', sa.Column('power_kw', sa.Numeric(precision=6, scale=2), nullable=True))
    op.add_column('wv_loom_readings', sa.Column('vibration_mm_s', sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column('wv_loom_readings', sa.Column('motor_temp_c', sa.Numeric(precision=5, scale=1), nullable=True))
    op.add_column('wv_loom_readings', sa.Column('air_pressure_bar', sa.Numeric(precision=4, scale=2), nullable=True))
    op.add_column('wv_looms', sa.Column('serial_no', sa.String(length=40), nullable=True))
    op.add_column('wv_looms', sa.Column('year_of_make', sa.Integer(), nullable=True))
    op.add_column('wv_looms', sa.Column('shedding', sa.String(length=20), nullable=True))
    op.add_column('wv_looms', sa.Column('colours', sa.Integer(), nullable=True))
    op.add_column('wv_looms', sa.Column('power_kw_rated', sa.Numeric(precision=5, scale=1), nullable=True))
    op.add_column('wv_looms', sa.Column('bay', sa.String(length=30), nullable=True))
    op.add_column('wv_looms', sa.Column('last_overhaul_on', sa.Date(), nullable=True))
    op.add_column('wv_looms', sa.Column('warranty_until', sa.Date(), nullable=True))
    op.add_column('wv_operators', sa.Column('designation', sa.String(length=40), nullable=True))
    op.add_column('wv_operators', sa.Column('department', sa.String(length=30), nullable=True))
    op.add_column('wv_operators', sa.Column('contract_type', sa.String(length=12), nullable=True))
    op.add_column('wv_operators', sa.Column('joined_on', sa.Date(), nullable=True))
    op.add_column('wv_operators', sa.Column('experience_years', sa.Numeric(precision=4, scale=1), nullable=True))
    op.add_column('wv_operators', sa.Column('skills', sa.String(length=80), nullable=True))
    op.add_column('wv_operators', sa.Column('phone', sa.String(length=20), nullable=True))
    op.add_column('wv_production_orders', sa.Column('customer_id', sa.Integer(), nullable=True))
    op.add_column('wv_production_orders', sa.Column('priority', sa.String(length=1), server_default='B', nullable=False))
    op.add_column('wv_production_orders', sa.Column('rate_per_m', sa.Numeric(precision=10, scale=2), nullable=True))
    op.create_index(op.f('ix_wv_production_orders_customer_id'), 'wv_production_orders', ['customer_id'], unique=False)
    op.create_foreign_key(op.f('fk_wv_production_orders_customer_id_wv_customers'), 'wv_production_orders', 'wv_customers', ['customer_id'], ['id'])
    op.add_column('wv_styles', sa.Column('loom_type_required', sa.String(length=30), nullable=True))
    op.create_check_constraint(op.f('ck_wv_production_orders_priority'), 'wv_production_orders', "priority IN ('A', 'B', 'C')")


def downgrade() -> None:
    op.drop_constraint(op.f('ck_wv_production_orders_priority'), 'wv_production_orders', type_='check')
    op.drop_column('wv_styles', 'loom_type_required')
    op.drop_constraint(op.f('fk_wv_production_orders_customer_id_wv_customers'), 'wv_production_orders', type_='foreignkey')
    op.drop_index(op.f('ix_wv_production_orders_customer_id'), table_name='wv_production_orders')
    op.drop_column('wv_production_orders', 'rate_per_m')
    op.drop_column('wv_production_orders', 'priority')
    op.drop_column('wv_production_orders', 'customer_id')
    op.drop_column('wv_operators', 'phone')
    op.drop_column('wv_operators', 'skills')
    op.drop_column('wv_operators', 'experience_years')
    op.drop_column('wv_operators', 'joined_on')
    op.drop_column('wv_operators', 'contract_type')
    op.drop_column('wv_operators', 'department')
    op.drop_column('wv_operators', 'designation')
    op.drop_column('wv_looms', 'warranty_until')
    op.drop_column('wv_looms', 'last_overhaul_on')
    op.drop_column('wv_looms', 'bay')
    op.drop_column('wv_looms', 'power_kw_rated')
    op.drop_column('wv_looms', 'colours')
    op.drop_column('wv_looms', 'shedding')
    op.drop_column('wv_looms', 'year_of_make')
    op.drop_column('wv_looms', 'serial_no')
    op.drop_column('wv_loom_readings', 'air_pressure_bar')
    op.drop_column('wv_loom_readings', 'motor_temp_c')
    op.drop_column('wv_loom_readings', 'vibration_mm_s')
    op.drop_column('wv_loom_readings', 'power_kw')
    op.drop_column('wv_beams', 'size_pickup_pct')
    op.drop_column('wv_actions', 'verified_cause')
    op.drop_index('ix_wv_shift_notes_date_shift', table_name='wv_shift_notes')
    op.drop_table('wv_shift_notes')
    op.drop_table('wv_schedule_plans')
    op.drop_table('wv_yarn_lots')
    op.drop_table('wv_customers')
