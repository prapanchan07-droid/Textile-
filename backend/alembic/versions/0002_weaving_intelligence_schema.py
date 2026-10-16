"""weaving intelligence schema

Adds the wv_* tables only; nothing existing is altered or dropped.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-15 17:31:46.685910
"""
from alembic import op
import sqlalchemy as sa


revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('wv_defect_types',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=30), nullable=False),
    sa.Column('name', sa.String(length=60), nullable=False),
    sa.Column('category', sa.String(length=10), nullable=False),
    sa.CheckConstraint("category IN ('WEAVING', 'YARN', 'PROCESS', 'OTHER')", name=op.f('ck_wv_defect_types_category')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_wv_defect_types')),
    sa.UniqueConstraint('code', name=op.f('uq_wv_defect_types_code'))
    )
    op.create_table('wv_looms',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('loom_code', sa.String(length=20), nullable=False),
    sa.Column('loom_type', sa.String(length=30), nullable=False),
    sa.Column('make', sa.String(length=60), nullable=True),
    sa.Column('model', sa.String(length=60), nullable=True),
    sa.Column('reed_space_cm', sa.Numeric(precision=6, scale=1), nullable=True),
    sa.Column('rated_rpm', sa.Integer(), nullable=False),
    sa.Column('installed_on', sa.Date(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('data_origin', sa.String(length=10), server_default='LIVE', nullable=False),
    sa.CheckConstraint("data_origin IN ('DEMO', 'IMPORTED', 'LIVE')", name=op.f('ck_wv_looms_data_origin')),
    sa.CheckConstraint('rated_rpm > 0', name=op.f('ck_wv_looms_rated_rpm_positive')),
    sa.CheckConstraint('reed_space_cm IS NULL OR reed_space_cm > 0', name=op.f('ck_wv_looms_reed_space_positive')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_wv_looms')),
    sa.UniqueConstraint('loom_code', name=op.f('uq_wv_looms_loom_code'))
    )
    op.create_table('wv_shifts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=10), nullable=False),
    sa.Column('name', sa.String(length=40), nullable=False),
    sa.Column('start_time', sa.Time(), nullable=False),
    sa.Column('end_time', sa.Time(), nullable=False),
    sa.Column('crosses_midnight', sa.Boolean(), nullable=False),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.CheckConstraint('start_time <> end_time', name=op.f('ck_wv_shifts_distinct_times')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_wv_shifts')),
    sa.UniqueConstraint('code', name=op.f('uq_wv_shifts_code'))
    )
    op.create_table('wv_stop_reasons',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=30), nullable=False),
    sa.Column('name', sa.String(length=60), nullable=False),
    sa.Column('category', sa.String(length=20), nullable=False),
    sa.Column('is_planned', sa.Boolean(), nullable=False),
    sa.Column('counts_toward_stop_rate', sa.Boolean(), nullable=False),
    sa.Column('diagnostic_hint', sa.Text(), nullable=True),
    sa.CheckConstraint("category IN ('WARP', 'WEFT', 'MECHANICAL', 'ELECTRICAL', 'BEAM', 'STYLE', 'WAITING', 'YARN', 'PLANNED_MAINTENANCE', 'OTHER')", name=op.f('ck_wv_stop_reasons_category')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_wv_stop_reasons')),
    sa.UniqueConstraint('code', name=op.f('uq_wv_stop_reasons_code'))
    )
    op.create_table('wv_styles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('style_code', sa.String(length=20), nullable=False),
    sa.Column('fabric_name', sa.String(length=80), nullable=False),
    sa.Column('weave', sa.String(length=30), nullable=True),
    sa.Column('warp_count', sa.String(length=20), nullable=True),
    sa.Column('weft_count', sa.String(length=20), nullable=True),
    sa.Column('epi', sa.Numeric(precision=6, scale=1), nullable=True),
    sa.Column('ppi', sa.Numeric(precision=6, scale=1), nullable=False),
    sa.Column('width_in', sa.Numeric(precision=6, scale=1), nullable=True),
    sa.Column('target_efficiency_pct', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('rate_per_m', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('std_cost_per_m', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('variable_cost_per_m', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('data_origin', sa.String(length=10), server_default='LIVE', nullable=False),
    sa.CheckConstraint("data_origin IN ('DEMO', 'IMPORTED', 'LIVE')", name=op.f('ck_wv_styles_data_origin')),
    sa.CheckConstraint('ppi > 0', name=op.f('ck_wv_styles_ppi_positive')),
    sa.CheckConstraint('rate_per_m >= 0 AND std_cost_per_m >= 0 AND variable_cost_per_m >= 0', name=op.f('ck_wv_styles_money_non_negative')),
    sa.CheckConstraint('target_efficiency_pct > 0 AND target_efficiency_pct <= 100', name=op.f('ck_wv_styles_target_eff_range')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_wv_styles')),
    sa.UniqueConstraint('style_code', name=op.f('uq_wv_styles_style_code'))
    )
    op.create_table('wv_actions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('action_ref', sa.String(length=20), nullable=False),
    sa.Column('finding_key', sa.String(length=160), nullable=True),
    sa.Column('issue', sa.Text(), nullable=False),
    sa.Column('action', sa.Text(), nullable=False),
    sa.Column('owner_role', sa.String(length=30), nullable=True),
    sa.Column('owner_name', sa.String(length=80), nullable=True),
    sa.Column('due_date', sa.Date(), nullable=True),
    sa.Column('status', sa.String(length=12), nullable=False),
    sa.Column('expected_impact_lakhs', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('requires_approval', sa.Boolean(), nullable=False),
    sa.Column('approved_by_user_id', sa.String(length=50), nullable=True),
    sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_by_user_id', sa.String(length=50), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('outcome_note', sa.Text(), nullable=True),
    sa.Column('outcome_measured_lakhs', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('data_origin', sa.String(length=10), server_default='LIVE', nullable=False),
    sa.CheckConstraint("data_origin IN ('DEMO', 'IMPORTED', 'LIVE')", name=op.f('ck_wv_actions_data_origin')),
    sa.CheckConstraint("status IN ('OPEN', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')", name=op.f('ck_wv_actions_status')),
    sa.ForeignKeyConstraint(['approved_by_user_id'], ['users.id'], name=op.f('fk_wv_actions_approved_by_user_id_users')),
    sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], name=op.f('fk_wv_actions_created_by_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_wv_actions')),
    sa.UniqueConstraint('action_ref', name=op.f('uq_wv_actions_action_ref'))
    )
    op.create_index(op.f('ix_wv_actions_finding_key'), 'wv_actions', ['finding_key'], unique=False)
    op.create_index('ix_wv_actions_status_due', 'wv_actions', ['status', 'due_date'], unique=False)
    op.create_table('wv_beams',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('beam_no', sa.String(length=30), nullable=False),
    sa.Column('style_id', sa.Integer(), nullable=False),
    sa.Column('total_ends', sa.Integer(), nullable=False),
    sa.Column('length_m', sa.Numeric(precision=10, scale=1), nullable=False),
    sa.Column('yarn_lot', sa.String(length=40), nullable=True),
    sa.Column('sized_on', sa.Date(), nullable=True),
    sa.Column('status', sa.String(length=12), nullable=False),
    sa.Column('data_origin', sa.String(length=10), server_default='LIVE', nullable=False),
    sa.CheckConstraint("data_origin IN ('DEMO', 'IMPORTED', 'LIVE')", name=op.f('ck_wv_beams_data_origin')),
    sa.CheckConstraint("status IN ('READY', 'MOUNTED', 'FINISHED')", name=op.f('ck_wv_beams_status')),
    sa.CheckConstraint('length_m > 0', name=op.f('ck_wv_beams_length_positive')),
    sa.CheckConstraint('total_ends > 0', name=op.f('ck_wv_beams_ends_positive')),
    sa.ForeignKeyConstraint(['style_id'], ['wv_styles.id'], name=op.f('fk_wv_beams_style_id_wv_styles')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_wv_beams')),
    sa.UniqueConstraint('beam_no', name=op.f('uq_wv_beams_beam_no'))
    )
    op.create_index(op.f('ix_wv_beams_style_id'), 'wv_beams', ['style_id'], unique=False)
    op.create_index(op.f('ix_wv_beams_yarn_lot'), 'wv_beams', ['yarn_lot'], unique=False)
    op.create_table('wv_operators',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('employee_code', sa.String(length=20), nullable=False),
    sa.Column('full_name', sa.String(length=120), nullable=True),
    sa.Column('operator_role', sa.String(length=12), nullable=False),
    sa.Column('grade', sa.String(length=6), nullable=True),
    sa.Column('home_shift_id', sa.Integer(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('data_origin', sa.String(length=10), server_default='LIVE', nullable=False),
    sa.CheckConstraint("data_origin IN ('DEMO', 'IMPORTED', 'LIVE')", name=op.f('ck_wv_operators_data_origin')),
    sa.CheckConstraint("operator_role IN ('WEAVER', 'FITTER', 'INSPECTOR', 'TECHNICIAN', 'SUPERVISOR')", name=op.f('ck_wv_operators_role')),
    sa.ForeignKeyConstraint(['home_shift_id'], ['wv_shifts.id'], name=op.f('fk_wv_operators_home_shift_id_wv_shifts')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_wv_operators')),
    sa.UniqueConstraint('employee_code', name=op.f('uq_wv_operators_employee_code'))
    )
    op.create_table('wv_production_orders',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('order_no', sa.String(length=30), nullable=False),
    sa.Column('style_id', sa.Integer(), nullable=False),
    sa.Column('customer', sa.String(length=120), nullable=True),
    sa.Column('ordered_m', sa.Numeric(precision=12, scale=1), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=True),
    sa.Column('due_date', sa.Date(), nullable=True),
    sa.Column('status', sa.String(length=12), nullable=False),
    sa.Column('data_origin', sa.String(length=10), server_default='LIVE', nullable=False),
    sa.CheckConstraint("data_origin IN ('DEMO', 'IMPORTED', 'LIVE')", name=op.f('ck_wv_production_orders_data_origin')),
    sa.CheckConstraint("status IN ('PLANNED', 'RUNNING', 'COMPLETED', 'CANCELLED')", name=op.f('ck_wv_production_orders_status')),
    sa.CheckConstraint('ordered_m > 0', name=op.f('ck_wv_production_orders_qty_positive')),
    sa.ForeignKeyConstraint(['style_id'], ['wv_styles.id'], name=op.f('fk_wv_production_orders_style_id_wv_styles')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_wv_production_orders')),
    sa.UniqueConstraint('order_no', name=op.f('uq_wv_production_orders_order_no'))
    )
    op.create_index(op.f('ix_wv_production_orders_due_date'), 'wv_production_orders', ['due_date'], unique=False)
    op.create_index(op.f('ix_wv_production_orders_style_id'), 'wv_production_orders', ['style_id'], unique=False)
    op.create_table('wv_attendance',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('shift_date', sa.Date(), nullable=False),
    sa.Column('shift_id', sa.Integer(), nullable=False),
    sa.Column('operator_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=8), nullable=False),
    sa.Column('data_origin', sa.String(length=10), server_default='LIVE', nullable=False),
    sa.CheckConstraint("data_origin IN ('DEMO', 'IMPORTED', 'LIVE')", name=op.f('ck_wv_attendance_data_origin')),
    sa.CheckConstraint("status IN ('PRESENT', 'ABSENT', 'LEAVE')", name=op.f('ck_wv_attendance_status')),
    sa.ForeignKeyConstraint(['operator_id'], ['wv_operators.id'], name=op.f('fk_wv_attendance_operator_id_wv_operators')),
    sa.ForeignKeyConstraint(['shift_id'], ['wv_shifts.id'], name=op.f('fk_wv_attendance_shift_id_wv_shifts')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_wv_attendance')),
    sa.UniqueConstraint('shift_date', 'shift_id', 'operator_id', name='uq_wv_attendance_slot')
    )
    op.create_index(op.f('ix_wv_attendance_shift_date'), 'wv_attendance', ['shift_date'], unique=False)
    op.create_table('wv_beam_mountings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('beam_id', sa.Integer(), nullable=False),
    sa.Column('loom_id', sa.Integer(), nullable=False),
    sa.Column('mounted_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('removed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('data_origin', sa.String(length=10), server_default='LIVE', nullable=False),
    sa.CheckConstraint("data_origin IN ('DEMO', 'IMPORTED', 'LIVE')", name=op.f('ck_wv_beam_mountings_data_origin')),
    sa.CheckConstraint('removed_at IS NULL OR removed_at > mounted_at', name=op.f('ck_wv_beam_mountings_order')),
    sa.ForeignKeyConstraint(['beam_id'], ['wv_beams.id'], name=op.f('fk_wv_beam_mountings_beam_id_wv_beams')),
    sa.ForeignKeyConstraint(['loom_id'], ['wv_looms.id'], name=op.f('fk_wv_beam_mountings_loom_id_wv_looms')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_wv_beam_mountings')),
    sa.UniqueConstraint('loom_id', 'mounted_at', name='uq_wv_beam_mountings_loom_mounted')
    )
    op.create_index(op.f('ix_wv_beam_mountings_beam_id'), 'wv_beam_mountings', ['beam_id'], unique=False)
    op.create_index('ix_wv_beam_mountings_loom_time', 'wv_beam_mountings', ['loom_id', 'mounted_at'], unique=False)
    op.create_index('uq_wv_beam_mountings_open_loom', 'wv_beam_mountings', ['loom_id'], unique=True, postgresql_where=sa.text('removed_at IS NULL'), sqlite_where=sa.text('removed_at IS NULL'))
    op.create_table('wv_inspections',
    sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('roll_no', sa.String(length=40), nullable=False),
    sa.Column('loom_id', sa.Integer(), nullable=False),
    sa.Column('style_id', sa.Integer(), nullable=False),
    sa.Column('beam_id', sa.Integer(), nullable=True),
    sa.Column('shift_id', sa.Integer(), nullable=False),
    sa.Column('shift_date', sa.Date(), nullable=False),
    sa.Column('inspected_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('inspector_id', sa.Integer(), nullable=True),
    sa.Column('length_m', sa.Numeric(precision=8, scale=2), nullable=False),
    sa.Column('grade', sa.String(length=8), nullable=False),
    sa.Column('data_origin', sa.String(length=10), server_default='LIVE', nullable=False),
    sa.CheckConstraint("data_origin IN ('DEMO', 'IMPORTED', 'LIVE')", name=op.f('ck_wv_inspections_data_origin')),
    sa.CheckConstraint("grade IN ('A', 'B', 'C', 'REJECT')", name=op.f('ck_wv_inspections_grade')),
    sa.CheckConstraint('length_m > 0', name=op.f('ck_wv_inspections_length_positive')),
    sa.ForeignKeyConstraint(['beam_id'], ['wv_beams.id'], name=op.f('fk_wv_inspections_beam_id_wv_beams')),
    sa.ForeignKeyConstraint(['inspector_id'], ['wv_operators.id'], name=op.f('fk_wv_inspections_inspector_id_wv_operators')),
    sa.ForeignKeyConstraint(['loom_id'], ['wv_looms.id'], name=op.f('fk_wv_inspections_loom_id_wv_looms')),
    sa.ForeignKeyConstraint(['shift_id'], ['wv_shifts.id'], name=op.f('fk_wv_inspections_shift_id_wv_shifts')),
    sa.ForeignKeyConstraint(['style_id'], ['wv_styles.id'], name=op.f('fk_wv_inspections_style_id_wv_styles')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_wv_inspections')),
    sa.UniqueConstraint('roll_no', name=op.f('uq_wv_inspections_roll_no'))
    )
    op.create_index('ix_wv_inspections_beam', 'wv_inspections', ['beam_id'], unique=False)
    op.create_index('ix_wv_inspections_date_loom', 'wv_inspections', ['shift_date', 'loom_id'], unique=False)
    op.create_index('ix_wv_inspections_date_shift', 'wv_inspections', ['shift_date', 'shift_id'], unique=False)
    op.create_index('ix_wv_inspections_date_style', 'wv_inspections', ['shift_date', 'style_id'], unique=False)
    op.create_table('wv_loom_readings',
    sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('loom_id', sa.Integer(), nullable=False),
    sa.Column('reading_start', sa.DateTime(timezone=True), nullable=False),
    sa.Column('reading_end', sa.DateTime(timezone=True), nullable=False),
    sa.Column('duration_seconds', sa.Integer(), nullable=False),
    sa.Column('shift_id', sa.Integer(), nullable=False),
    sa.Column('shift_date', sa.Date(), nullable=False),
    sa.Column('style_id', sa.Integer(), nullable=True),
    sa.Column('beam_id', sa.Integer(), nullable=True),
    sa.Column('order_id', sa.Integer(), nullable=True),
    sa.Column('weaver_id', sa.Integer(), nullable=True),
    sa.Column('running_seconds', sa.Integer(), nullable=False),
    sa.Column('picks', sa.BigInteger(), nullable=True),
    sa.Column('quality_flag', sa.String(length=10), server_default='OK', nullable=False),
    sa.Column('data_origin', sa.String(length=10), server_default='LIVE', nullable=False),
    sa.CheckConstraint("data_origin IN ('DEMO', 'IMPORTED', 'LIVE')", name=op.f('ck_wv_loom_readings_data_origin')),
    sa.CheckConstraint("quality_flag IN ('OK', 'PARTIAL', 'NO_PICKS')", name=op.f('ck_wv_loom_readings_quality_flag')),
    sa.CheckConstraint('duration_seconds > 0', name=op.f('ck_wv_loom_readings_duration_positive')),
    sa.CheckConstraint('picks IS NULL OR picks >= 0', name=op.f('ck_wv_loom_readings_picks_non_negative')),
    sa.CheckConstraint('reading_end > reading_start', name=op.f('ck_wv_loom_readings_interval_order')),
    sa.CheckConstraint('running_seconds >= 0 AND running_seconds <= duration_seconds', name=op.f('ck_wv_loom_readings_running_within_interval')),
    sa.ForeignKeyConstraint(['beam_id'], ['wv_beams.id'], name=op.f('fk_wv_loom_readings_beam_id_wv_beams')),
    sa.ForeignKeyConstraint(['loom_id'], ['wv_looms.id'], name=op.f('fk_wv_loom_readings_loom_id_wv_looms')),
    sa.ForeignKeyConstraint(['order_id'], ['wv_production_orders.id'], name=op.f('fk_wv_loom_readings_order_id_wv_production_orders')),
    sa.ForeignKeyConstraint(['shift_id'], ['wv_shifts.id'], name=op.f('fk_wv_loom_readings_shift_id_wv_shifts')),
    sa.ForeignKeyConstraint(['style_id'], ['wv_styles.id'], name=op.f('fk_wv_loom_readings_style_id_wv_styles')),
    sa.ForeignKeyConstraint(['weaver_id'], ['wv_operators.id'], name=op.f('fk_wv_loom_readings_weaver_id_wv_operators')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_wv_loom_readings')),
    sa.UniqueConstraint('loom_id', 'reading_start', name='uq_wv_loom_readings_loom_start')
    )
    op.create_index('ix_wv_loom_readings_beam', 'wv_loom_readings', ['beam_id'], unique=False)
    op.create_index('ix_wv_loom_readings_date_loom', 'wv_loom_readings', ['shift_date', 'loom_id'], unique=False)
    op.create_index('ix_wv_loom_readings_date_shift', 'wv_loom_readings', ['shift_date', 'shift_id'], unique=False)
    op.create_index('ix_wv_loom_readings_date_style', 'wv_loom_readings', ['shift_date', 'style_id'], unique=False)
    op.create_table('wv_order_assignments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('order_id', sa.Integer(), nullable=False),
    sa.Column('loom_id', sa.Integer(), nullable=False),
    sa.Column('assigned_from', sa.DateTime(timezone=True), nullable=False),
    sa.Column('assigned_to', sa.DateTime(timezone=True), nullable=True),
    sa.Column('data_origin', sa.String(length=10), server_default='LIVE', nullable=False),
    sa.CheckConstraint("data_origin IN ('DEMO', 'IMPORTED', 'LIVE')", name=op.f('ck_wv_order_assignments_data_origin')),
    sa.CheckConstraint('assigned_to IS NULL OR assigned_to > assigned_from', name=op.f('ck_wv_order_assignments_order')),
    sa.ForeignKeyConstraint(['loom_id'], ['wv_looms.id'], name=op.f('fk_wv_order_assignments_loom_id_wv_looms')),
    sa.ForeignKeyConstraint(['order_id'], ['wv_production_orders.id'], name=op.f('fk_wv_order_assignments_order_id_wv_production_orders')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_wv_order_assignments')),
    sa.UniqueConstraint('loom_id', 'assigned_from', name='uq_wv_order_assignments_loom_from')
    )
    op.create_index(op.f('ix_wv_order_assignments_loom_id'), 'wv_order_assignments', ['loom_id'], unique=False)
    op.create_index(op.f('ix_wv_order_assignments_order_id'), 'wv_order_assignments', ['order_id'], unique=False)
    op.create_index('uq_wv_order_assignments_open_loom', 'wv_order_assignments', ['loom_id'], unique=True, postgresql_where=sa.text('assigned_to IS NULL'), sqlite_where=sa.text('assigned_to IS NULL'))
    op.create_table('wv_shift_assignments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('shift_date', sa.Date(), nullable=False),
    sa.Column('shift_id', sa.Integer(), nullable=False),
    sa.Column('loom_id', sa.Integer(), nullable=False),
    sa.Column('operator_id', sa.Integer(), nullable=False),
    sa.Column('assignment_role', sa.String(length=10), nullable=False),
    sa.Column('data_origin', sa.String(length=10), server_default='LIVE', nullable=False),
    sa.CheckConstraint("assignment_role IN ('WEAVER', 'FITTER')", name=op.f('ck_wv_shift_assignments_role')),
    sa.CheckConstraint("data_origin IN ('DEMO', 'IMPORTED', 'LIVE')", name=op.f('ck_wv_shift_assignments_data_origin')),
    sa.ForeignKeyConstraint(['loom_id'], ['wv_looms.id'], name=op.f('fk_wv_shift_assignments_loom_id_wv_looms')),
    sa.ForeignKeyConstraint(['operator_id'], ['wv_operators.id'], name=op.f('fk_wv_shift_assignments_operator_id_wv_operators')),
    sa.ForeignKeyConstraint(['shift_id'], ['wv_shifts.id'], name=op.f('fk_wv_shift_assignments_shift_id_wv_shifts')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_wv_shift_assignments')),
    sa.UniqueConstraint('shift_date', 'shift_id', 'loom_id', 'assignment_role', name='uq_wv_shift_assignments_slot')
    )
    op.create_index(op.f('ix_wv_shift_assignments_operator_id'), 'wv_shift_assignments', ['operator_id'], unique=False)
    op.create_table('wv_stop_events',
    sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('loom_id', sa.Integer(), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('reason_id', sa.Integer(), nullable=False),
    sa.Column('shift_id', sa.Integer(), nullable=False),
    sa.Column('shift_date', sa.Date(), nullable=False),
    sa.Column('style_id', sa.Integer(), nullable=True),
    sa.Column('beam_id', sa.Integer(), nullable=True),
    sa.Column('weaver_id', sa.Integer(), nullable=True),
    sa.Column('fitter_id', sa.Integer(), nullable=True),
    sa.Column('note', sa.Text(), nullable=True),
    sa.Column('data_origin', sa.String(length=10), server_default='LIVE', nullable=False),
    sa.CheckConstraint("data_origin IN ('DEMO', 'IMPORTED', 'LIVE')", name=op.f('ck_wv_stop_events_data_origin')),
    sa.CheckConstraint('ended_at IS NULL OR ended_at >= started_at', name=op.f('ck_wv_stop_events_interval_order')),
    sa.ForeignKeyConstraint(['beam_id'], ['wv_beams.id'], name=op.f('fk_wv_stop_events_beam_id_wv_beams')),
    sa.ForeignKeyConstraint(['fitter_id'], ['wv_operators.id'], name=op.f('fk_wv_stop_events_fitter_id_wv_operators')),
    sa.ForeignKeyConstraint(['loom_id'], ['wv_looms.id'], name=op.f('fk_wv_stop_events_loom_id_wv_looms')),
    sa.ForeignKeyConstraint(['reason_id'], ['wv_stop_reasons.id'], name=op.f('fk_wv_stop_events_reason_id_wv_stop_reasons')),
    sa.ForeignKeyConstraint(['shift_id'], ['wv_shifts.id'], name=op.f('fk_wv_stop_events_shift_id_wv_shifts')),
    sa.ForeignKeyConstraint(['style_id'], ['wv_styles.id'], name=op.f('fk_wv_stop_events_style_id_wv_styles')),
    sa.ForeignKeyConstraint(['weaver_id'], ['wv_operators.id'], name=op.f('fk_wv_stop_events_weaver_id_wv_operators')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_wv_stop_events')),
    sa.UniqueConstraint('loom_id', 'started_at', name='uq_wv_stop_events_loom_start')
    )
    op.create_index('ix_wv_stop_events_beam', 'wv_stop_events', ['beam_id'], unique=False)
    op.create_index('ix_wv_stop_events_date_loom', 'wv_stop_events', ['shift_date', 'loom_id'], unique=False)
    op.create_index('ix_wv_stop_events_open', 'wv_stop_events', ['loom_id'], unique=False, postgresql_where=sa.text('ended_at IS NULL'), sqlite_where=sa.text('ended_at IS NULL'))
    op.create_index('ix_wv_stop_events_reason_date', 'wv_stop_events', ['reason_id', 'shift_date'], unique=False)
    op.create_index('ix_wv_stop_events_started_at', 'wv_stop_events', ['started_at'], unique=False)
    op.create_index('ix_wv_stop_events_style_date', 'wv_stop_events', ['style_id', 'shift_date'], unique=False)
    op.create_table('wv_defect_observations',
    sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('inspection_id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('defect_type_id', sa.Integer(), nullable=False),
    sa.Column('severity', sa.String(length=10), nullable=False),
    sa.Column('points', sa.Integer(), nullable=False),
    sa.Column('defect_count', sa.Integer(), nullable=False),
    sa.Column('position_m', sa.Numeric(precision=8, scale=2), nullable=True),
    sa.CheckConstraint("severity IN ('MINOR', 'MAJOR', 'CRITICAL')", name=op.f('ck_wv_defect_observations_severity')),
    sa.CheckConstraint('defect_count > 0', name=op.f('ck_wv_defect_observations_count_positive')),
    sa.CheckConstraint('points BETWEEN 1 AND 4', name=op.f('ck_wv_defect_observations_points_range')),
    sa.ForeignKeyConstraint(['defect_type_id'], ['wv_defect_types.id'], name=op.f('fk_wv_defect_observations_defect_type_id_wv_defect_types')),
    sa.ForeignKeyConstraint(['inspection_id'], ['wv_inspections.id'], name=op.f('fk_wv_defect_observations_inspection_id_wv_inspections'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_wv_defect_observations'))
    )
    op.create_index('ix_wv_defect_observations_inspection', 'wv_defect_observations', ['inspection_id'], unique=False)
    op.create_index('ix_wv_defect_observations_type', 'wv_defect_observations', ['defect_type_id'], unique=False)
    op.create_table('wv_maintenance_events',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('event_ref', sa.String(length=60), nullable=False),
    sa.Column('loom_id', sa.Integer(), nullable=False),
    sa.Column('event_type', sa.String(length=12), nullable=False),
    sa.Column('task', sa.String(length=120), nullable=False),
    sa.Column('planned_for', sa.Date(), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('status', sa.String(length=12), nullable=False),
    sa.Column('technician_id', sa.Integer(), nullable=True),
    sa.Column('stop_event_id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('data_origin', sa.String(length=10), server_default='LIVE', nullable=False),
    sa.CheckConstraint("data_origin IN ('DEMO', 'IMPORTED', 'LIVE')", name=op.f('ck_wv_maintenance_events_data_origin')),
    sa.CheckConstraint("event_type IN ('PREVENTIVE', 'BREAKDOWN', 'INSPECTION')", name=op.f('ck_wv_maintenance_events_event_type')),
    sa.CheckConstraint("status IN ('PLANNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')", name=op.f('ck_wv_maintenance_events_status')),
    sa.CheckConstraint('completed_at IS NULL OR started_at IS NULL OR completed_at >= started_at', name=op.f('ck_wv_maintenance_events_interval_order')),
    sa.ForeignKeyConstraint(['loom_id'], ['wv_looms.id'], name=op.f('fk_wv_maintenance_events_loom_id_wv_looms')),
    sa.ForeignKeyConstraint(['stop_event_id'], ['wv_stop_events.id'], name=op.f('fk_wv_maintenance_events_stop_event_id_wv_stop_events')),
    sa.ForeignKeyConstraint(['technician_id'], ['wv_operators.id'], name=op.f('fk_wv_maintenance_events_technician_id_wv_operators')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_wv_maintenance_events')),
    sa.UniqueConstraint('event_ref', name=op.f('uq_wv_maintenance_events_event_ref'))
    )
    op.create_index('ix_wv_maintenance_events_loom_status', 'wv_maintenance_events', ['loom_id', 'status'], unique=False)
    op.create_index('ix_wv_maintenance_events_planned', 'wv_maintenance_events', ['planned_for'], unique=False)


def downgrade() -> None:
    # Reverses the weaving schema. This DELETES all weaving data (looms, readings, stop events, ...);
    # users and legacy report tables are untouched. Back up first (docs/database.md).
    op.drop_index('ix_wv_maintenance_events_planned', table_name='wv_maintenance_events')
    op.drop_index('ix_wv_maintenance_events_loom_status', table_name='wv_maintenance_events')
    op.drop_table('wv_maintenance_events')
    op.drop_index('ix_wv_defect_observations_type', table_name='wv_defect_observations')
    op.drop_index('ix_wv_defect_observations_inspection', table_name='wv_defect_observations')
    op.drop_table('wv_defect_observations')
    op.drop_index('ix_wv_stop_events_style_date', table_name='wv_stop_events')
    op.drop_index('ix_wv_stop_events_started_at', table_name='wv_stop_events')
    op.drop_index('ix_wv_stop_events_reason_date', table_name='wv_stop_events')
    op.drop_index('ix_wv_stop_events_open', table_name='wv_stop_events', postgresql_where=sa.text('ended_at IS NULL'), sqlite_where=sa.text('ended_at IS NULL'))
    op.drop_index('ix_wv_stop_events_date_loom', table_name='wv_stop_events')
    op.drop_index('ix_wv_stop_events_beam', table_name='wv_stop_events')
    op.drop_table('wv_stop_events')
    op.drop_index(op.f('ix_wv_shift_assignments_operator_id'), table_name='wv_shift_assignments')
    op.drop_table('wv_shift_assignments')
    op.drop_index('uq_wv_order_assignments_open_loom', table_name='wv_order_assignments', postgresql_where=sa.text('assigned_to IS NULL'), sqlite_where=sa.text('assigned_to IS NULL'))
    op.drop_index(op.f('ix_wv_order_assignments_order_id'), table_name='wv_order_assignments')
    op.drop_index(op.f('ix_wv_order_assignments_loom_id'), table_name='wv_order_assignments')
    op.drop_table('wv_order_assignments')
    op.drop_index('ix_wv_loom_readings_date_style', table_name='wv_loom_readings')
    op.drop_index('ix_wv_loom_readings_date_shift', table_name='wv_loom_readings')
    op.drop_index('ix_wv_loom_readings_date_loom', table_name='wv_loom_readings')
    op.drop_index('ix_wv_loom_readings_beam', table_name='wv_loom_readings')
    op.drop_table('wv_loom_readings')
    op.drop_index('ix_wv_inspections_date_style', table_name='wv_inspections')
    op.drop_index('ix_wv_inspections_date_shift', table_name='wv_inspections')
    op.drop_index('ix_wv_inspections_date_loom', table_name='wv_inspections')
    op.drop_index('ix_wv_inspections_beam', table_name='wv_inspections')
    op.drop_table('wv_inspections')
    op.drop_index('uq_wv_beam_mountings_open_loom', table_name='wv_beam_mountings', postgresql_where=sa.text('removed_at IS NULL'), sqlite_where=sa.text('removed_at IS NULL'))
    op.drop_index('ix_wv_beam_mountings_loom_time', table_name='wv_beam_mountings')
    op.drop_index(op.f('ix_wv_beam_mountings_beam_id'), table_name='wv_beam_mountings')
    op.drop_table('wv_beam_mountings')
    op.drop_index(op.f('ix_wv_attendance_shift_date'), table_name='wv_attendance')
    op.drop_table('wv_attendance')
    op.drop_index(op.f('ix_wv_production_orders_style_id'), table_name='wv_production_orders')
    op.drop_index(op.f('ix_wv_production_orders_due_date'), table_name='wv_production_orders')
    op.drop_table('wv_production_orders')
    op.drop_table('wv_operators')
    op.drop_index(op.f('ix_wv_beams_yarn_lot'), table_name='wv_beams')
    op.drop_index(op.f('ix_wv_beams_style_id'), table_name='wv_beams')
    op.drop_table('wv_beams')
    op.drop_index('ix_wv_actions_status_due', table_name='wv_actions')
    op.drop_index(op.f('ix_wv_actions_finding_key'), table_name='wv_actions')
    op.drop_table('wv_actions')
    op.drop_table('wv_styles')
    op.drop_table('wv_stop_reasons')
    op.drop_table('wv_shifts')
    op.drop_table('wv_looms')
    op.drop_table('wv_defect_types')
