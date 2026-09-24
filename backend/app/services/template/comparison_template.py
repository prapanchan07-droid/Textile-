"""Data source for the Machine Comparison page when template data is available."""
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.schemas.machine_comparison import MachineMasterOption
from app.services.template.factory_data import aggregate_window, current_window

_METRICS = ["EFFICIENCY", "PRODUCTION", "PRODUCTION_LOSS", "DOWNTIME", "UTILIZATION", "ENERGY", "ENERGY_PER_KG", "QUALITY"]


def comparison_source(
    db: Session, selected_ids: Optional[List[str]], period: str
) -> Tuple[List[MachineMasterOption], List[str], Dict[str, Dict[str, float]], Dict[str, float], List[str]]:
    """Returns (master machines, machine types, per-machine metrics, factory-average reference per metric, selected ids)."""
    agg = aggregate_window(db, current_window(db, period))
    machines = agg.ranked_by_loss() if agg else []

    master = [MachineMasterOption(machine_id=m.machine_id, machine_type=m.machine_type, section=m.section)
              for m in sorted(machines, key=lambda m: m.machine_id)]
    types = ["ALL"] + sorted({m.machine_type for m in machines})

    raw: Dict[str, Dict[str, float]] = {}
    for m in machines:
        raw[m.machine_id] = {
            "EFFICIENCY": m.efficiency,
            "PRODUCTION": round(m.actual, 1),
            "PRODUCTION_LOSS": round(m.loss, 1),
            "DOWNTIME": round(m.downtime_min, 1),
            "UTILIZATION": m.utilization,
            "ENERGY": round(m.kwh, 1),
            "ENERGY_PER_KG": m.energy_per_kg,
            "QUALITY": m.quality if m.quality is not None else 0.0,
        }

    ref = {}
    for key in _METRICS:
        vals = [v[key] for v in raw.values()]
        ref[key] = round(sum(vals) / len(vals), 3) if vals else 0.0

    chosen = [i for i in (selected_ids or []) if i in raw]
    if not chosen:
        chosen = [m.machine_id for m in machines[:3]]
    return master, types, raw, ref, chosen
