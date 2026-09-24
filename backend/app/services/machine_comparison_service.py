from typing import List, Optional, Dict
from app.db.session import SessionLocal
from app.services.template.factory_data import has_template_data
from app.services.template.comparison_template import comparison_source
from app.schemas.machine_comparison import (
    MachineComparisonResponse,
    MachineMasterOption,
    MachineMetricValue,
    MultiMetricRow,
    HeadToHeadMetric,
    ComparisonInsightData,
)

class MachineComparisonService:
    @staticmethod
    def get_comparison_data(
        selected_ids: Optional[List[str]] = None,
        metric: str = "EFFICIENCY",
        period: str = "TODAY",
        machine_type_filter: str = "ALL",
        reference_type: str = "FACTORY_AVG"
    ) -> MachineComparisonResponse:
        
        # 1. Master Machine List (Source of truth)
        master_machines = [
            MachineMasterOption(machine_id="V-09", machine_type="Vortex", section="Spinning Unit 1"),
            MachineMasterOption(machine_id="V-05", machine_type="Vortex", section="Spinning Unit 1"),
            MachineMasterOption(machine_id="V-12", machine_type="Vortex", section="Spinning Unit 1"),
            MachineMasterOption(machine_id="SMX-03", machine_type="Simplex", section="Prep Unit 2"),
            MachineMasterOption(machine_id="RF-04", machine_type="Ring Frame", section="Spinning Unit 2"),
            MachineMasterOption(machine_id="A-02", machine_type="Airjet", section="Weaving Unit 1"),
        ]

        available_types = ["ALL", "Vortex", "Airjet", "Ring Frame", "Simplex"]

        # Default selection if none provided: V-09, V-05, V-12
        if not selected_ids:
            selected_ids = ["V-09", "V-05", "V-12"]

        # Raw Machine Dataset
        raw_db: Dict[str, Dict[str, float]] = {
            "V-09": {
                "EFFICIENCY": 84.2,
                "PRODUCTION": 8420.0,
                "PRODUCTION_LOSS": 680.0,
                "DOWNTIME": 240.0,
                "UTILIZATION": 79.5,
                "ENERGY": 1850.0,
                "ENERGY_PER_KG": 0.22,
                "QUALITY": 96.1,
            },
            "V-05": {
                "EFFICIENCY": 88.1,
                "PRODUCTION": 8780.0,
                "PRODUCTION_LOSS": 420.0,
                "DOWNTIME": 135.0,
                "UTILIZATION": 85.0,
                "ENERGY": 1920.0,
                "ENERGY_PER_KG": 0.21,
                "QUALITY": 97.4,
            },
            "V-12": {
                "EFFICIENCY": 92.4,
                "PRODUCTION": 9020.0,
                "PRODUCTION_LOSS": 180.0,
                "DOWNTIME": 45.0,
                "UTILIZATION": 91.2,
                "ENERGY": 1950.0,
                "ENERGY_PER_KG": 0.20,
                "QUALITY": 98.6,
            },
            "SMX-03": {
                "EFFICIENCY": 90.5,
                "PRODUCTION": 3100.0,
                "PRODUCTION_LOSS": 290.0,
                "DOWNTIME": 90.0,
                "UTILIZATION": 88.0,
                "ENERGY": 710.0,
                "ENERGY_PER_KG": 0.23,
                "QUALITY": 97.8,
            },
            "RF-04": {
                "EFFICIENCY": 94.8,
                "PRODUCTION": 11200.0,
                "PRODUCTION_LOSS": 300.0,
                "DOWNTIME": 40.0,
                "UTILIZATION": 93.5,
                "ENERGY": 2350.0,
                "ENERGY_PER_KG": 0.19,
                "QUALITY": 99.1,
            },
            "A-02": {
                "EFFICIENCY": 95.2,
                "PRODUCTION": 10450.0,
                "PRODUCTION_LOSS": 250.0,
                "DOWNTIME": 30.0,
                "UTILIZATION": 94.0,
                "ENERGY": 2100.0,
                "ENERGY_PER_KG": 0.18,
                "QUALITY": 99.3,
            }
        }

        # Uploaded template data replaces the synthetic machine set, metrics and factory averages
        template_ref: Optional[Dict[str, float]] = None
        db = SessionLocal()
        try:
            if has_template_data(db):
                master_machines, available_types, raw_db, template_ref, selected_ids = comparison_source(db, selected_ids, period)
        finally:
            db.close()

        # Filter active selected machines
        active_ids = [m_id for m_id in selected_ids if m_id in raw_db]
        
        # Determine Metric metadata
        metric_meta = {
            "EFFICIENCY": {"name": "Efficiency", "unit": "%", "higher_better": True},
            "PRODUCTION": {"name": "Production", "unit": "kg", "higher_better": True},
            "PRODUCTION_LOSS": {"name": "Production Loss", "unit": "kg", "higher_better": False},
            "DOWNTIME": {"name": "Downtime", "unit": "min", "higher_better": False},
            "UTILIZATION": {"name": "Utilization", "unit": "%", "higher_better": True},
            "ENERGY": {"name": "Energy Consumption", "unit": "kWh", "higher_better": False},
            "ENERGY_PER_KG": {"name": "Energy / kg", "unit": "kWh/kg", "higher_better": False},
            "QUALITY": {"name": "Quality Rating", "unit": "%", "higher_better": True},
        }.get(metric.upper(), {"name": "Efficiency", "unit": "%", "higher_better": True})

        # Calculate Baseline Reference Value
        ref_val = 91.6 # Factory Avg Efficiency default
        if metric.upper() == "EFFICIENCY":
            ref_val = 91.6
        elif metric.upper() == "PRODUCTION":
            ref_val = 8495.0
        elif metric.upper() == "PRODUCTION_LOSS":
            ref_val = 353.0
        elif metric.upper() == "DOWNTIME":
            ref_val = 96.0
        elif metric.upper() == "UTILIZATION":
            ref_val = 88.5
        elif metric.upper() == "ENERGY_PER_KG":
            ref_val = 0.20
        elif metric.upper() == "QUALITY":
            ref_val = 98.0

        if template_ref is not None:
            ref_val = template_ref.get(metric.upper(), 0.0)

        if metric_meta['unit'] == '%':
            ref_formatted = f"{ref_val:.1f} %"
        elif metric_meta['unit'] == 'kWh/kg':
            ref_formatted = f"{ref_val:.2f} kWh/kg"
        else:
            ref_formatted = f"{ref_val:,.0f} {metric_meta['unit']}"

        # Build Primary Metrics list
        primary_metrics: List[MachineMetricValue] = []
        for m_id in active_ids:
            m_type = next((m.machine_type for m in master_machines if m.machine_id == m_id), "Unknown")
            val = raw_db[m_id].get(metric.upper(), 0.0)
            
            if metric_meta['unit'] == '%':
                fmt = f"{val:.1f}%"
            elif metric_meta['unit'] in ['kg', 'kWh', 'min']:
                fmt = f"{val:,.0f} {metric_meta['unit']}"
            else:
                fmt = f"{val:.2f} {metric_meta['unit']}"

            var = val - ref_val
            var_lbl = f"{'+' if var > 0 else ''}{var:.1f} vs Factory Avg"

            status = "NORMAL"
            if metric_meta['higher_better']:
                if val < 85.0:
                    status = "CRITICAL"
                elif val < 90.0:
                    status = "ATTENTION"
            else:
                if val > 200:
                    status = "CRITICAL"
                elif val > 100:
                    status = "ATTENTION"

            primary_metrics.append(
                MachineMetricValue(
                    machine_id=m_id,
                    machine_type=m_type,
                    value=val,
                    formatted_value=fmt,
                    unit=metric_meta['unit'],
                    status=status,
                    variance_vs_reference=var,
                    variance_label=var_lbl
                )
            )

        # Multi-Metric Comparison Matrix
        multi_metric_keys = ["EFFICIENCY", "PRODUCTION", "DOWNTIME", "ENERGY_PER_KG", "QUALITY"]
        multi_matrix: List[MultiMetricRow] = []
        for key in multi_metric_keys:
            m_info = {
                "EFFICIENCY": ("Efficiency", "%"),
                "PRODUCTION": ("Production", "kg"),
                "DOWNTIME": ("Downtime", "min"),
                "ENERGY_PER_KG": ("Energy / kg", "kWh/kg"),
                "QUALITY": ("Quality Rating", "%"),
            }[key]
            
            row_vals: Dict[str, str] = {}
            for m_id in active_ids:
                v = raw_db[m_id].get(key, 0.0)
                if m_info[1] == '%':
                    row_vals[m_id] = f"{v:.1f}%"
                elif m_info[1] in ['kg', 'min']:
                    row_vals[m_id] = f"{v:,.0f} {m_info[1]}"
                else:
                    row_vals[m_id] = f"{v:.2f} {m_info[1]}"

            multi_matrix.append(
                MultiMetricRow(
                    metric_name=m_info[0],
                    unit=m_info[1],
                    values=row_vals
                )
            )

        # Head-to-Head (if exactly 2 machines selected)
        h2h_list: Optional[List[HeadToHeadMetric]] = None
        if len(active_ids) == 2:
            m1, m2 = active_ids[0], active_ids[1]
            h2h_list = []
            for key in multi_metric_keys:
                m_info = {
                    "EFFICIENCY": ("Efficiency", "%", True),
                    "PRODUCTION": ("Production", "kg", True),
                    "DOWNTIME": ("Downtime", "min", False),
                    "ENERGY_PER_KG": ("Energy / kg", "kWh/kg", False),
                    "QUALITY": ("Quality Rating", "%", True),
                }[key]
                
                v1 = raw_db[m1].get(key, 0.0)
                v2 = raw_db[m2].get(key, 0.0)
                
                fmt1 = f"{v1:.1f}%" if m_info[1] == '%' else f"{v1:,.0f} {m_info[1]}"
                fmt2 = f"{v2:.1f}%" if m_info[1] == '%' else f"{v2:,.0f} {m_info[1]}"

                diff = v1 - v2
                leader = m1 if (diff > 0 if m_info[2] else diff < 0) else m2
                delta_str = f"{abs(diff):.1f} {m_info[1]} difference"

                h2h_list.append(
                    HeadToHeadMetric(
                        metric_key=key,
                        metric_name=m_info[0],
                        unit=m_info[1],
                        machine1_value=v1,
                        machine1_formatted=fmt1,
                        machine2_value=v2,
                        machine2_formatted=fmt2,
                        delta_text=delta_str,
                        leader_machine_id=leader
                    )
                )

        # Factual Insight Synthesis
        if active_ids:
            sorted_by_val = sorted(primary_metrics, key=lambda x: x.value, reverse=metric_meta['higher_better'])
            top_m = sorted_by_val[0]
            bot_m = sorted_by_val[-1]

            if len(active_ids) == 1:
                summary = f"{top_m.machine_id} recorded {top_m.formatted_value} {metric_meta['name'].lower()} during the selected period."
                obs = [f"{top_m.machine_id} is operating at {top_m.variance_label}."]
            else:
                summary = f"{top_m.machine_id} recorded the highest selected-period {metric_meta['name'].lower()} ({top_m.formatted_value}), while {bot_m.machine_id} recorded the lowest ({bot_m.formatted_value})."
                obs = [
                    f"{top_m.machine_id} outperformed the selected group average by {abs(top_m.value - ref_val):.1f} {metric_meta['unit']}.",
                    f"{bot_m.machine_id} shows the largest margin for operational improvement among selected machines."
                ]
        else:
            summary = "Select machines from the dropdown above to generate comparison metrics."
            obs = []

        insight = ComparisonInsightData(
            summary_text=summary,
            key_observations=obs
        )

        return MachineComparisonResponse(
            company_name="Ashok Textiles",
            selected_period=period,
            selected_metric=metric,
            selected_machine_type=machine_type_filter,
            selected_machine_ids=active_ids,
            available_machine_types=available_types,
            all_master_machines=master_machines,
            reference_type=reference_type,
            reference_value=ref_val,
            reference_formatted=ref_formatted,
            primary_metrics=primary_metrics,
            multi_metric_matrix=multi_matrix,
            head_to_head=h2h_list,
            insight=insight
        )

machine_comparison_service = MachineComparisonService()
