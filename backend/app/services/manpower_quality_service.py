from typing import List, Optional
from app.db.session import SessionLocal
from app.services.template.factory_data import has_manpower_quality_data
from app.services.template.manpower_quality_template import manpower_quality_from_template
from app.schemas.manpower_quality import (
    ManpowerQualityModuleResponse,
    ManpowerSummary,
    DepartmentManpowerItem,
    ManpowerTrendPoint,
    QualityStatusData,
    QualityParameterItem,
    QualityMachineItem,
    AttentionItem
)

class ManpowerQualityService:
    @staticmethod
    def get_manpower_quality_data(period: str = "THIS_MONTH") -> ManpowerQualityModuleResponse:
        """Uses uploaded template data when present, otherwise the built-in synthetic data."""
        db = SessionLocal()
        try:
            if has_manpower_quality_data(db):
                return manpower_quality_from_template(db, period)
        finally:
            db.close()
        return ManpowerQualityService._synthetic_manpower_quality_data(period)

    @staticmethod
    def _synthetic_manpower_quality_data(period: str = "THIS_MONTH") -> ManpowerQualityModuleResponse:
        # 1. Manpower Summary
        manpower_summary = ManpowerSummary(
            required=1250,
            available=1180,
            shortage=70,
            attendance_pct=94.4
        )

        # 2. Department Manpower Gaps (Sorted by largest shortage first)
        department_gaps = [
            DepartmentManpowerItem(department="Spinning", required=420, available=390, gap=-30, attendance_pct=92.8),
            DepartmentManpowerItem(department="Weaving", required=300, available=285, gap=-15, attendance_pct=95.0),
            DepartmentManpowerItem(department="Maintenance", required=80, available=75, gap=-5, attendance_pct=93.7),
            DepartmentManpowerItem(department="Sizing", required=120, available=118, gap=-2, attendance_pct=98.3),
            DepartmentManpowerItem(department="Carding & Prep", required=180, available=178, gap=-2, attendance_pct=98.8),
            DepartmentManpowerItem(department="Quality & Lab", required=150, available=149, gap=-1, attendance_pct=99.3),
        ]

        # 3. Manpower Trend Points
        manpower_trend = [
            ManpowerTrendPoint(date_label="Sep 16", required=1250, available=1195, shortage=55, attendance_pct=95.6),
            ManpowerTrendPoint(date_label="Sep 17", required=1250, available=1190, shortage=60, attendance_pct=95.2),
            ManpowerTrendPoint(date_label="Sep 18", required=1250, available=1205, shortage=45, attendance_pct=96.4),
            ManpowerTrendPoint(date_label="Sep 19", required=1250, available=1170, shortage=80, attendance_pct=93.6),
            ManpowerTrendPoint(date_label="Sep 20", required=1250, available=1185, shortage=65, attendance_pct=94.8),
            ManpowerTrendPoint(date_label="Sep 21", required=1250, available=1175, shortage=75, attendance_pct=94.0),
            ManpowerTrendPoint(date_label="Sep 22", required=1250, available=1180, shortage=70, attendance_pct=94.4),
        ]

        # 4. Quality Status
        quality_status = QualityStatusData(
            status="ATTENTION",
            samples_tested=24,
            pass_rate_pct=95.8,
            defect_rate_pct=4.2,
            main_issue="Thick Places (Thick/Km)"
        )

        # 5. Quality Parameters
        quality_parameters = [
            QualityParameterItem(parameter="Thick/Km", label="Thick Places / Km", value=52.0, limit=40.0, unit="/km", status="OUT OF LIMIT"),
            QualityParameterItem(parameter="U%", label="Unevenness % (U%)", value=11.8, limit=12.0, unit="%", status="ATTENTION"),
            QualityParameterItem(parameter="Count CV", label="Count CV %", value=1.2, limit=1.5, unit="%", status="NORMAL"),
            QualityParameterItem(parameter="Strength CV", label="Strength CV %", value=4.8, limit=5.5, unit="%", status="NORMAL"),
            QualityParameterItem(parameter="Neps/Km", label="Neps / Km", value=120.0, limit=140.0, unit="/km", status="NORMAL"),
            QualityParameterItem(parameter="Thin/Km", label="Thin Places / Km", value=8.0, limit=15.0, unit="/km", status="NORMAL"),
        ]

        # 6. Quality Trends By Parameter
        quality_trends_by_param = {
            "Thick/Km": [
                {"date_label": "Sep 16", "value": 38.0, "limit": 40.0},
                {"date_label": "Sep 17", "value": 41.0, "limit": 40.0},
                {"date_label": "Sep 18", "value": 44.0, "limit": 40.0},
                {"date_label": "Sep 19", "value": 49.0, "limit": 40.0},
                {"date_label": "Sep 20", "value": 48.0, "limit": 40.0},
                {"date_label": "Sep 21", "value": 50.0, "limit": 40.0},
                {"date_label": "Sep 22", "value": 52.0, "limit": 40.0},
            ],
            "U%": [
                {"date_label": "Sep 16", "value": 11.2, "limit": 12.0},
                {"date_label": "Sep 17", "value": 11.4, "limit": 12.0},
                {"date_label": "Sep 18", "value": 11.5, "limit": 12.0},
                {"date_label": "Sep 19", "value": 11.7, "limit": 12.0},
                {"date_label": "Sep 20", "value": 11.6, "limit": 12.0},
                {"date_label": "Sep 21", "value": 11.8, "limit": 12.0},
                {"date_label": "Sep 22", "value": 11.8, "limit": 12.0},
            ],
            "Neps/Km": [
                {"date_label": "Sep 16", "value": 110.0, "limit": 140.0},
                {"date_label": "Sep 17", "value": 115.0, "limit": 140.0},
                {"date_label": "Sep 18", "value": 112.0, "limit": 140.0},
                {"date_label": "Sep 19", "value": 125.0, "limit": 140.0},
                {"date_label": "Sep 20", "value": 118.0, "limit": 140.0},
                {"date_label": "Sep 21", "value": 122.0, "limit": 140.0},
                {"date_label": "Sep 22", "value": 120.0, "limit": 140.0},
            ],
            "Count CV": [
                {"date_label": "Sep 16", "value": 1.1, "limit": 1.5},
                {"date_label": "Sep 17", "value": 1.2, "limit": 1.5},
                {"date_label": "Sep 18", "value": 1.1, "limit": 1.5},
                {"date_label": "Sep 19", "value": 1.3, "limit": 1.5},
                {"date_label": "Sep 20", "value": 1.2, "limit": 1.5},
                {"date_label": "Sep 21", "value": 1.2, "limit": 1.5},
                {"date_label": "Sep 22", "value": 1.2, "limit": 1.5},
            ],
            "Strength CV": [
                {"date_label": "Sep 16", "value": 4.5, "limit": 5.5},
                {"date_label": "Sep 17", "value": 4.6, "limit": 5.5},
                {"date_label": "Sep 18", "value": 4.7, "limit": 5.5},
                {"date_label": "Sep 19", "value": 4.9, "limit": 5.5},
                {"date_label": "Sep 20", "value": 4.8, "limit": 5.5},
                {"date_label": "Sep 21", "value": 4.7, "limit": 5.5},
                {"date_label": "Sep 22", "value": 4.8, "limit": 5.5},
            ],
        }

        # 7. Quality Issue By Machine / Process
        quality_issues_by_machine = [
            QualityMachineItem(machine_process="Vortex V-09", quality_issue="Thick/Km", current_value=52.0, limit=40.0, unit="/km", status="OUT OF LIMIT"),
            QualityMachineItem(machine_process="Vortex V-05", quality_issue="U%", current_value=11.8, limit=12.0, unit="%", status="ATTENTION"),
            QualityMachineItem(machine_process="Airjet A-02", quality_issue="Neps/Km", current_value=120.0, limit=140.0, unit="/km", status="NORMAL"),
            QualityMachineItem(machine_process="Ring Frame RF-04", quality_issue="Count CV", current_value=1.2, limit=1.5, unit="%", status="NORMAL"),
        ]

        # 8. Needs Attention Section
        needs_attention = [
            AttentionItem(severity="HIGH", title="Spinning manpower shortage", detail="30 workers short in Spinning shift B"),
            AttentionItem(severity="HIGH", title="Thick/Km above specification limit", detail="Observed on Vortex V-09 (52 vs 40 limit)"),
            AttentionItem(severity="MEDIUM", title="Weaving attendance below target", detail="Attendance at 95.0% (15 workers short)"),
        ]

        return ManpowerQualityModuleResponse(
            company_name="Ashok Textiles",
            period=period,
            manpower_summary=manpower_summary,
            department_gaps=department_gaps,
            manpower_trend=manpower_trend,
            quality_status=quality_status,
            quality_parameters=quality_parameters,
            quality_trends_by_param=quality_trends_by_param,
            quality_issues_by_machine=quality_issues_by_machine,
            needs_attention=needs_attention
        )
