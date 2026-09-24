from typing import List, Optional
from app.schemas.machines import (
    MachinesModuleResponse,
    MachinePerformanceItem,
    SpotlightMachine,
    DowntimeKpi,
    DowntimeReasonItem,
    MachineTrendPoint,
    MachineDetailData
)

class MachinesService:
    @staticmethod
    def get_machines_data(
        period: str = "THIS_MONTH",
        machine_type: str = "ALL",
        machine_id: str = "ALL"
    ) -> MachinesModuleResponse:
        
        # 1. Master Machine List (Detailed physical machine data)
        master_machines = [
            MachinePerformanceItem(
                machine_id="V-09",
                machine_type="Vortex",
                actual_kg=8420.0,
                target_kg=9100.0,
                efficiency_pct=84.2,
                loss_kg=680.0,
                downtime_min=240,
                status="CRITICAL",
                main_issue="Repeated stoppages / Power events"
            ),
            MachinePerformanceItem(
                machine_id="V-05",
                machine_type="Vortex",
                actual_kg=8780.0,
                target_kg=9200.0,
                efficiency_pct=88.1,
                loss_kg=420.0,
                downtime_min=135,
                status="ATTENTION",
                main_issue="Maintenance delay"
            ),
            MachinePerformanceItem(
                machine_id="SMX-03",
                machine_type="Simplex",
                actual_kg=3100.0,
                target_kg=3390.0,
                efficiency_pct=90.5,
                loss_kg=290.0,
                downtime_min=90,
                status="ATTENTION",
                main_issue="Cleaning cycle extension"
            ),
            MachinePerformanceItem(
                machine_id="V-12",
                machine_type="Vortex",
                actual_kg=9020.0,
                target_kg=9200.0,
                efficiency_pct=93.5,
                loss_kg=180.0,
                downtime_min=45,
                status="NORMAL",
                main_issue="Minor yarn breakage"
            ),
            MachinePerformanceItem(
                machine_id="RF-04",
                machine_type="Ring Frame",
                actual_kg=11200.0,
                target_kg=11500.0,
                efficiency_pct=94.8,
                loss_kg=300.0,
                downtime_min=40,
                status="NORMAL",
                main_issue="Routine lubrication"
            ),
            MachinePerformanceItem(
                machine_id="A-02",
                machine_type="Airjet",
                actual_kg=10450.0,
                target_kg=10700.0,
                efficiency_pct=95.2,
                loss_kg=250.0,
                downtime_min=30,
                status="NORMAL",
                main_issue="Material changeover"
            )
        ]

        # Machine Types Master
        machine_types = ["All", "Vortex", "Airjet", "Ring Frame", "Simplex"]

        # Filter by Machine Type
        filtered_machines = master_machines
        if machine_type and machine_type.upper() != "ALL":
            filtered_machines = [m for m in filtered_machines if m.machine_type.lower() == machine_type.lower()]

        # Selected machine for spotlight / detail focus
        selected_m = master_machines[0]
        if machine_id and machine_id.upper() != "ALL":
            for m in master_machines:
                if m.machine_id.lower() == machine_id.lower():
                    selected_m = m
                    break
        elif filtered_machines:
            selected_m = filtered_machines[0]

        # Identify Spotlight Machine
        spotlight_machine = SpotlightMachine(
            machine_id=selected_m.machine_id,
            machine_type=selected_m.machine_type,
            loss_kg=selected_m.loss_kg,
            efficiency_pct=selected_m.efficiency_pct,
            downtime_min=selected_m.downtime_min,
            main_issue=selected_m.main_issue
        )

        # Downtime KPIs
        downtime_kpis = DowntimeKpi(
            total_downtime_min=510,
            unplanned_downtime_min=390,
            planned_downtime_min=120,
            stoppage_count=18
        )

        # Downtime by Reason
        downtime_reasons = [
            DowntimeReasonItem(category="Electrical / Power", downtime_min=180, percentage=35.3),
            DowntimeReasonItem(category="Maintenance", downtime_min=140, percentage=27.5),
            DowntimeReasonItem(category="Cleaning", downtime_min=90, percentage=17.6),
            DowntimeReasonItem(category="Material / Process", downtime_min=60, percentage=11.8),
            DowntimeReasonItem(category="Other", downtime_min=40, percentage=7.8),
        ]

        # Multi-Machine Performance Trend Maps
        machine_trends_by_id = {
            "V-09": [
                {"date_label": "Sep 16", "efficiency_pct": 89.2, "loss_kg": 480.0},
                {"date_label": "Sep 17", "efficiency_pct": 87.5, "loss_kg": 540.0},
                {"date_label": "Sep 18", "efficiency_pct": 91.0, "loss_kg": 390.0},
                {"date_label": "Sep 19", "efficiency_pct": 82.1, "loss_kg": 780.0},
                {"date_label": "Sep 20", "efficiency_pct": 88.4, "loss_kg": 510.0},
                {"date_label": "Sep 21", "efficiency_pct": 86.0, "loss_kg": 600.0},
                {"date_label": "Sep 22", "efficiency_pct": 84.2, "loss_kg": 680.0},
            ],
            "V-05": [
                {"date_label": "Sep 16", "efficiency_pct": 91.5, "loss_kg": 320.0},
                {"date_label": "Sep 17", "efficiency_pct": 90.0, "loss_kg": 360.0},
                {"date_label": "Sep 18", "efficiency_pct": 89.2, "loss_kg": 410.0},
                {"date_label": "Sep 19", "efficiency_pct": 87.0, "loss_kg": 460.0},
                {"date_label": "Sep 20", "efficiency_pct": 88.5, "loss_kg": 400.0},
                {"date_label": "Sep 21", "efficiency_pct": 89.0, "loss_kg": 380.0},
                {"date_label": "Sep 22", "efficiency_pct": 88.1, "loss_kg": 420.0},
            ],
            "SMX-03": [
                {"date_label": "Sep 16", "efficiency_pct": 92.0, "loss_kg": 240.0},
                {"date_label": "Sep 17", "efficiency_pct": 91.8, "loss_kg": 250.0},
                {"date_label": "Sep 18", "efficiency_pct": 89.5, "loss_kg": 310.0},
                {"date_label": "Sep 19", "efficiency_pct": 90.0, "loss_kg": 290.0},
                {"date_label": "Sep 20", "efficiency_pct": 91.2, "loss_kg": 260.0},
                {"date_label": "Sep 21", "efficiency_pct": 89.8, "loss_kg": 300.0},
                {"date_label": "Sep 22", "efficiency_pct": 90.5, "loss_kg": 290.0},
            ],
            "V-12": [
                {"date_label": "Sep 16", "efficiency_pct": 94.5, "loss_kg": 150.0},
                {"date_label": "Sep 17", "efficiency_pct": 95.0, "loss_kg": 140.0},
                {"date_label": "Sep 18", "efficiency_pct": 93.0, "loss_kg": 190.0},
                {"date_label": "Sep 19", "efficiency_pct": 94.2, "loss_kg": 160.0},
                {"date_label": "Sep 20", "efficiency_pct": 93.8, "loss_kg": 170.0},
                {"date_label": "Sep 21", "efficiency_pct": 94.0, "loss_kg": 165.0},
                {"date_label": "Sep 22", "efficiency_pct": 93.5, "loss_kg": 180.0},
            ],
            "RF-04": [
                {"date_label": "Sep 16", "efficiency_pct": 96.0, "loss_kg": 220.0},
                {"date_label": "Sep 17", "efficiency_pct": 95.5, "loss_kg": 240.0},
                {"date_label": "Sep 18", "efficiency_pct": 94.2, "loss_kg": 310.0},
                {"date_label": "Sep 19", "efficiency_pct": 95.0, "loss_kg": 280.0},
                {"date_label": "Sep 20", "efficiency_pct": 94.0, "loss_kg": 320.0},
                {"date_label": "Sep 21", "efficiency_pct": 95.2, "loss_kg": 260.0},
                {"date_label": "Sep 22", "efficiency_pct": 94.8, "loss_kg": 300.0},
            ],
            "A-02": [
                {"date_label": "Sep 16", "efficiency_pct": 96.2, "loss_kg": 200.0},
                {"date_label": "Sep 17", "efficiency_pct": 95.8, "loss_kg": 220.0},
                {"date_label": "Sep 18", "efficiency_pct": 96.0, "loss_kg": 210.0},
                {"date_label": "Sep 19", "efficiency_pct": 94.8, "loss_kg": 270.0},
                {"date_label": "Sep 20", "efficiency_pct": 95.5, "loss_kg": 230.0},
                {"date_label": "Sep 21", "efficiency_pct": 95.0, "loss_kg": 260.0},
                {"date_label": "Sep 22", "efficiency_pct": 95.2, "loss_kg": 250.0},
            ],
        }

        active_trend = machine_trends_by_id.get(selected_m.machine_id, machine_trends_by_id["V-09"])
        trend_points = [MachineTrendPoint(**pt) for pt in active_trend]

        # Detailed view for selected target machine
        machine_detail = MachineDetailData(
            machine_id=selected_m.machine_id,
            machine_type=selected_m.machine_type,
            actual_kg=selected_m.actual_kg,
            target_kg=selected_m.target_kg,
            efficiency_pct=selected_m.efficiency_pct,
            loss_kg=selected_m.loss_kg,
            total_downtime_min=selected_m.downtime_min,
            stoppage_count=8 if selected_m.machine_id == "V-09" else 4,
            main_reason="Electrical / Power" if selected_m.machine_id == "V-09" else "Maintenance",
            last_maintenance="18 Sep 2026",
            next_maintenance="28 Sep 2026",
            recent_event="Main Motor Drive Line Inspection",
            power_events=3 if selected_m.machine_id == "V-09" else 1,
            power_downtime_min=140 if selected_m.machine_id == "V-09" else 30,
            quality_status="NORMAL - 99.1% Grade A"
        )

        return MachinesModuleResponse(
            company_name="Ashok Textiles",
            period=period,
            selected_machine_type=machine_type,
            selected_machine_id=machine_id,
            machine_types=machine_types,
            all_machines=filtered_machines,
            spotlight_machine=spotlight_machine,
            downtime_kpis=downtime_kpis,
            downtime_reasons=downtime_reasons,
            machine_trend=trend_points,
            machine_trends_by_id=machine_trends_by_id,
            machine_detail=machine_detail
        )
