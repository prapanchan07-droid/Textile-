"""baseline: the tables that existed before the weaving schema

Databases created by the old ``create_all`` start-up already contain these tables, so every step
here is skipped when the table is already present. Existing rows are never touched.


Revision ID: 0001
Revises: 
Create Date: 2026-10-15 17:25:53.944325
"""
from alembic import op
import sqlalchemy as sa


revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


# Tables that were already there before this migration ran (created by the old create_all).
_existing: set = set()


def _create_table(name, *columns, **kw):
    if sa.inspect(op.get_bind()).has_table(name):
        _existing.add(name)
        return
    op.create_table(name, *columns, **kw)


def _create_index(name, table, columns, **kw):
    if table not in _existing:
        op.create_index(name, table, columns, **kw)



def upgrade() -> None:
    _create_table('module_registry',
    sa.Column('id', sa.String(length=50), nullable=False),
    sa.Column('module_number', sa.String(length=10), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('phase', sa.String(length=50), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('installed_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_module_registry'))
    )
    _create_index(op.f('ix_module_registry_module_number'), 'module_registry', ['module_number'], unique=True)
    _create_table('reports',
    sa.Column('id', sa.String(length=50), nullable=False),
    sa.Column('file_hash', sa.String(length=64), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=False),
    sa.Column('file_path', sa.String(length=500), nullable=False),
    sa.Column('report_type', sa.String(length=100), nullable=False),
    sa.Column('confidence_score', sa.Float(), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('report_date', sa.String(length=20), nullable=True),
    sa.Column('upload_timestamp', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_reports'))
    )
    _create_index(op.f('ix_reports_file_hash'), 'reports', ['file_hash'], unique=True)
    _create_index(op.f('ix_reports_report_date'), 'reports', ['report_date'], unique=False)
    _create_index(op.f('ix_reports_report_type'), 'reports', ['report_type'], unique=False)
    _create_table('system_info',
    sa.Column('id', sa.String(length=50), nullable=False),
    sa.Column('key', sa.String(length=100), nullable=False),
    sa.Column('value', sa.Text(), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_system_info'))
    )
    _create_index(op.f('ix_system_info_key'), 'system_info', ['key'], unique=True)
    _create_table('users',
    sa.Column('id', sa.String(length=50), nullable=False),
    sa.Column('username', sa.String(length=80), nullable=False),
    sa.Column('full_name', sa.String(length=120), nullable=False),
    sa.Column('role', sa.String(length=30), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('last_login_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users'))
    )
    _create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)
    _create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    _create_table('action_item_records',
    sa.Column('id', sa.String(length=50), nullable=False),
    sa.Column('source_report_id', sa.String(length=50), nullable=False),
    sa.Column('report_date', sa.String(length=20), nullable=False),
    sa.Column('issue', sa.String(length=255), nullable=False),
    sa.Column('action', sa.Text(), nullable=False),
    sa.Column('owner', sa.String(length=100), nullable=False),
    sa.Column('status', sa.String(length=30), nullable=False),
    sa.ForeignKeyConstraint(['source_report_id'], ['reports.id'], name=op.f('fk_action_item_records_source_report_id_reports')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_action_item_records'))
    )
    _create_index(op.f('ix_action_item_records_report_date'), 'action_item_records', ['report_date'], unique=False)
    _create_index(op.f('ix_action_item_records_source_report_id'), 'action_item_records', ['source_report_id'], unique=False)
    _create_table('business_daily_records',
    sa.Column('id', sa.String(length=50), nullable=False),
    sa.Column('source_report_id', sa.String(length=50), nullable=False),
    sa.Column('report_date', sa.String(length=20), nullable=False),
    sa.Column('revenue_lakhs', sa.Float(), nullable=False),
    sa.Column('orders_meters', sa.Float(), nullable=False),
    sa.Column('dispatched_meters', sa.Float(), nullable=False),
    sa.Column('collected_lakhs', sa.Float(), nullable=False),
    sa.Column('outstanding_lakhs', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['source_report_id'], ['reports.id'], name=op.f('fk_business_daily_records_source_report_id_reports')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_business_daily_records'))
    )
    _create_index(op.f('ix_business_daily_records_report_date'), 'business_daily_records', ['report_date'], unique=False)
    _create_index(op.f('ix_business_daily_records_source_report_id'), 'business_daily_records', ['source_report_id'], unique=False)
    _create_table('downtime_records',
    sa.Column('id', sa.String(length=50), nullable=False),
    sa.Column('source_report_id', sa.String(length=50), nullable=False),
    sa.Column('report_date', sa.String(length=20), nullable=False),
    sa.Column('shift', sa.String(length=50), nullable=True),
    sa.Column('machine_id', sa.String(length=100), nullable=True),
    sa.Column('machine_type', sa.String(length=100), nullable=True),
    sa.Column('downtime_minutes', sa.Float(), nullable=True),
    sa.Column('loss_kg', sa.Float(), nullable=False),
    sa.Column('reason_category', sa.String(length=100), nullable=False),
    sa.Column('remarks', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['source_report_id'], ['reports.id'], name=op.f('fk_downtime_records_source_report_id_reports')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_downtime_records'))
    )
    _create_index(op.f('ix_downtime_records_report_date'), 'downtime_records', ['report_date'], unique=False)
    _create_index(op.f('ix_downtime_records_shift'), 'downtime_records', ['shift'], unique=False)
    _create_table('energy_records',
    sa.Column('id', sa.String(length=50), nullable=False),
    sa.Column('source_report_id', sa.String(length=50), nullable=False),
    sa.Column('report_date', sa.String(length=20), nullable=False),
    sa.Column('shift', sa.String(length=50), nullable=True),
    sa.Column('kwh_consumed', sa.Float(), nullable=False),
    sa.Column('energy_per_kg', sa.Float(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['source_report_id'], ['reports.id'], name=op.f('fk_energy_records_source_report_id_reports')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_energy_records'))
    )
    _create_index(op.f('ix_energy_records_report_date'), 'energy_records', ['report_date'], unique=False)
    _create_table('machine_daily_records',
    sa.Column('id', sa.String(length=50), nullable=False),
    sa.Column('source_report_id', sa.String(length=50), nullable=False),
    sa.Column('report_date', sa.String(length=20), nullable=False),
    sa.Column('unit', sa.String(length=100), nullable=True),
    sa.Column('section', sa.String(length=100), nullable=True),
    sa.Column('shift', sa.String(length=50), nullable=True),
    sa.Column('machine_type', sa.String(length=100), nullable=False),
    sa.Column('machine_id', sa.String(length=100), nullable=False),
    sa.Column('target_kg', sa.Float(), nullable=False),
    sa.Column('actual_kg', sa.Float(), nullable=False),
    sa.Column('downtime_min', sa.Float(), nullable=False),
    sa.Column('downtime_reason', sa.String(length=100), nullable=True),
    sa.Column('is_planned_downtime', sa.Boolean(), nullable=False),
    sa.Column('stoppage_count', sa.Integer(), nullable=False),
    sa.Column('power_events', sa.Integer(), nullable=False),
    sa.Column('energy_kwh', sa.Float(), nullable=True),
    sa.Column('quality_rating_pct', sa.Float(), nullable=True),
    sa.Column('main_issue', sa.String(length=255), nullable=True),
    sa.Column('last_maintenance', sa.String(length=50), nullable=True),
    sa.Column('next_maintenance', sa.String(length=50), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['source_report_id'], ['reports.id'], name=op.f('fk_machine_daily_records_source_report_id_reports')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_machine_daily_records'))
    )
    _create_index(op.f('ix_machine_daily_records_machine_id'), 'machine_daily_records', ['machine_id'], unique=False)
    _create_index(op.f('ix_machine_daily_records_report_date'), 'machine_daily_records', ['report_date'], unique=False)
    _create_index(op.f('ix_machine_daily_records_source_report_id'), 'machine_daily_records', ['source_report_id'], unique=False)
    _create_table('manpower_records',
    sa.Column('id', sa.String(length=50), nullable=False),
    sa.Column('source_report_id', sa.String(length=50), nullable=False),
    sa.Column('report_date', sa.String(length=20), nullable=False),
    sa.Column('shift', sa.String(length=50), nullable=True),
    sa.Column('department', sa.String(length=100), nullable=True),
    sa.Column('planned_count', sa.Integer(), nullable=False),
    sa.Column('actual_count', sa.Integer(), nullable=False),
    sa.Column('gap_count', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['source_report_id'], ['reports.id'], name=op.f('fk_manpower_records_source_report_id_reports')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_manpower_records'))
    )
    _create_index(op.f('ix_manpower_records_report_date'), 'manpower_records', ['report_date'], unique=False)
    _create_table('production_records',
    sa.Column('id', sa.String(length=50), nullable=False),
    sa.Column('source_report_id', sa.String(length=50), nullable=False),
    sa.Column('report_date', sa.String(length=20), nullable=False),
    sa.Column('shift', sa.String(length=50), nullable=True),
    sa.Column('department', sa.String(length=100), nullable=True),
    sa.Column('unit', sa.String(length=100), nullable=True),
    sa.Column('machine_type', sa.String(length=100), nullable=True),
    sa.Column('machine_id', sa.String(length=100), nullable=True),
    sa.Column('actual_kg', sa.Float(), nullable=False),
    sa.Column('target_kg', sa.Float(), nullable=False),
    sa.Column('gap_kg', sa.Float(), nullable=False),
    sa.Column('achievement_pct', sa.Float(), nullable=False),
    sa.Column('source_sheet', sa.String(length=100), nullable=True),
    sa.Column('source_row', sa.Integer(), nullable=True),
    sa.Column('source_column', sa.String(length=100), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['source_report_id'], ['reports.id'], name=op.f('fk_production_records_source_report_id_reports')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_production_records'))
    )
    _create_index(op.f('ix_production_records_report_date'), 'production_records', ['report_date'], unique=False)
    _create_index(op.f('ix_production_records_shift'), 'production_records', ['shift'], unique=False)
    _create_table('quality_parameter_records',
    sa.Column('id', sa.String(length=50), nullable=False),
    sa.Column('source_report_id', sa.String(length=50), nullable=False),
    sa.Column('report_date', sa.String(length=20), nullable=False),
    sa.Column('machine_id', sa.String(length=100), nullable=True),
    sa.Column('parameter', sa.String(length=100), nullable=False),
    sa.Column('value', sa.Float(), nullable=False),
    sa.Column('limit_value', sa.Float(), nullable=False),
    sa.Column('unit', sa.String(length=30), nullable=False),
    sa.ForeignKeyConstraint(['source_report_id'], ['reports.id'], name=op.f('fk_quality_parameter_records_source_report_id_reports')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_quality_parameter_records'))
    )
    _create_index(op.f('ix_quality_parameter_records_report_date'), 'quality_parameter_records', ['report_date'], unique=False)
    _create_index(op.f('ix_quality_parameter_records_source_report_id'), 'quality_parameter_records', ['source_report_id'], unique=False)
    _create_table('quality_records',
    sa.Column('id', sa.String(length=50), nullable=False),
    sa.Column('source_report_id', sa.String(length=50), nullable=False),
    sa.Column('report_date', sa.String(length=20), nullable=False),
    sa.Column('shift', sa.String(length=50), nullable=True),
    sa.Column('yarn_count', sa.String(length=50), nullable=True),
    sa.Column('quality_score', sa.Float(), nullable=False),
    sa.Column('defect_rate', sa.Float(), nullable=False),
    sa.Column('warp_breaks', sa.Integer(), nullable=False),
    sa.Column('weft_breaks', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['source_report_id'], ['reports.id'], name=op.f('fk_quality_records_source_report_id_reports')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_quality_records'))
    )
    _create_index(op.f('ix_quality_records_report_date'), 'quality_records', ['report_date'], unique=False)
    _create_table('stock_records',
    sa.Column('id', sa.String(length=50), nullable=False),
    sa.Column('source_report_id', sa.String(length=50), nullable=False),
    sa.Column('report_date', sa.String(length=20), nullable=False),
    sa.Column('category', sa.String(length=100), nullable=False),
    sa.Column('current_value_lakhs', sa.Float(), nullable=False),
    sa.Column('limit_value_lakhs', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['source_report_id'], ['reports.id'], name=op.f('fk_stock_records_source_report_id_reports')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_stock_records'))
    )
    _create_index(op.f('ix_stock_records_report_date'), 'stock_records', ['report_date'], unique=False)
    _create_index(op.f('ix_stock_records_source_report_id'), 'stock_records', ['source_report_id'], unique=False)


def downgrade() -> None:
    # Deliberately empty. This revision only adopts tables that hold the mill's real data
    # (users, imported reports, ...), and a migration must never drop those.
    pass
