import re
from typing import Dict, List, Tuple, Any, Optional

# Standard Field Aliases Map
FIELD_ALIASES: Dict[str, List[str]] = {
    "target_production": [
        "TARGET", "TARGET PRODUCTION", "TARGET @ 22.5 HRS", "PLAN", "PLANNED PROD", 
        "TARGET (KG)", "TARGET_KG", "PROD TARGET", "PLANNED OUTPUT"
    ],
    "actual_production": [
        "ACTUAL", "ACTUAL PRODUCTION", "ACTUAL PROD", "PROD", "OUTPUT", 
        "ACTUAL (KG)", "ACTUAL_KG", "PRODUCED (KG)", "TOTAL PRODUCTION"
    ],
    "efficiency": [
        "EFF%", "EFFICIENCY", "EFF", "EFFICIENCY %", "PERFORMANCE %", "EFF P"
    ],
    "production_gap": [
        "LOSS", "PRODUCTION LOSS", "GAP", "VARIANCE", "SHORTFALL", "GAP (KG)", "LOSS_KG"
    ],
    "machine_id": [
        "M/C NO", "MACHINE NO", "LOOM NO", "MACHINE NUMBER", "MC NO", "MACHINE ID", 
        "M/C", "FRAME NO", "MACHINE"
    ],
    "machine_type": [
        "MACHINE TYPE", "MC TYPE", "DEPARTMENT TYPE", "PROCESS", "TECHNOLOGY", "SECTION TYPE"
    ],
    "shift": [
        "SHIFT", "SHIFT NAME", "WORKING SHIFT", "SHIFTS", "SFT"
    ],
    "date": [
        "DATE", "REPORT DATE", "ENTRY DATE", "PRODUCTION DATE", "DAY", "DT"
    ],
    "department": [
        "DEPARTMENT", "DEPT", "SECTION", "UNIT SECTION"
    ],
    "unit": [
        "UNIT", "MILL", "PLANT", "FACTORY"
    ],
    "yarn_count": [
        "COUNT", "YARN COUNT", "NE", "ENGLISH COUNT", "TEX"
    ],
    "downtime_minutes": [
        "DOWNTIME", "STOPPAGE (MIN)", "DOWNTIME MIN", "STOPPAGE MINUTES", "STOP TIME", "OFF MIN"
    ],
    "loss_kg": [
        "DOWNTIME LOSS (KG)", "STOPPAGE LOSS", "LOSS KG", "PROD LOSS KG"
    ],
    "reason_category": [
        "REASON", "STOPPAGE REASON", "REMARKS", "CATEGORY", "DOWNTIME REASON", "CAUSE"
    ],
    "kwh_consumed": [
        "KWH", "ENERGY CONSUMED", "POWER (KWH)", "UNITS (KWH)", "ELECTRICITY"
    ],
    "energy_per_kg": [
        "U/KG", "ENERGY/KG", "KWH/KG", "SPECIFIC ENERGY", "UNIT/KG"
    ],
    "planned_manpower": [
        "PLANNED MP", "REQUIRED MANPOWER", "BUDGET MP", "PLANNED WORKERS"
    ],
    "actual_manpower": [
        "ACTUAL MP", "ATTENDANCE", "PRESENT WORKERS", "ACTUAL WORKERS"
    ]
}

# Keywords for report type detection
REPORT_TYPE_KEYWORDS: Dict[str, List[str]] = {
    "PRODUCTION": ["production", "prod", "output", "target", "actual", "achievement", "shift"],
    "PREPARATORY_PRODUCTION": ["preparatory", "carding", "drawing", "simplex", "blowroom", "prep"],
    "SPINNING_PRODUCTION": ["spinning", "ring frame", "vortex", "airjet", "rotor", "spindle"],
    "WEAVING": ["weaving", "loom", "warp", "weft", "rpm", "picks"],
    "QUALITY": ["quality", "count", "defect", "warp breaks", "weft breaks", "csp", "ipi"],
    "DOWNTIME": ["downtime", "stoppage", "idle", "breakdown", "maintenance", "stop minutes"],
    "ENERGY": ["energy", "kwh", "power", "units", "u/kg", "electricity"],
    "MANPOWER": ["manpower", "workers", "attendance", "absenteeism", "operator"],
    "MAINTENANCE": ["maintenance", "spare", "repair", "overhaul", "lubrication"],
    "BUSINESS": ["revenue", "sales", "cost", "financial", "margin", "profit"]
}

class Normalizer:
    @staticmethod
    def normalize_header(header_text: str) -> str:
        """Standardize raw table headers into clean canonical key names."""
        clean = str(header_text).strip().upper()
        clean_sub = re.sub(r'[^A-Z0-9%_\s]', '', clean).strip()

        for canonical_key, aliases in FIELD_ALIASES.items():
            for alias in aliases:
                if clean_sub == alias or alias in clean_sub:
                    return canonical_key
        return clean.lower().replace(' ', '_')

    @staticmethod
    def detect_report_type(filename: str, sheet_names: List[str], headers: List[str]) -> Tuple[str, float]:
        """Auto-detect report type from filename, sheet names, and extracted column headers."""
        combined_text = f"{filename} {' '.join(sheet_names)} {' '.join(headers)}".lower()

        scores: Dict[str, float] = {}
        for rtype, keywords in REPORT_TYPE_KEYWORDS.items():
            score = 0.0
            for kw in keywords:
                if kw in combined_text:
                    score += 1.0
            if score > 0:
                scores[rtype] = score

        if not scores:
            return "PRODUCTION", 0.60

        best_type = max(scores, key=scores.get)
        raw_score = scores[best_type]
        confidence = min(0.98, 0.70 + (raw_score * 0.07))
        return best_type, round(confidence, 2)

    @staticmethod
    def parse_shift(value: Any) -> Optional[str]:
        """Extract standard shift designation ('Shift I', 'Shift II', 'Shift III', 'Shift A', 'Shift B', 'Shift C')."""
        if value is None:
            return None
        val_str = str(value).strip().upper()
        if not val_str or val_str in ("NONE", "NAN", "NULL", ""):
            return None

        # Check Shift III / 3 / C first
        if re.search(r'\b(SHIFT\s*3|SHIFT\s*III|SHIFT\s*C|3RD|SFT\s*3|SFT\s*C)\b', val_str) or val_str in ("3", "C", "III", "SHIFT 3", "SHIFT C", "SHIFT III"):
            return "Shift III"
        # Check Shift II / 2 / B second
        if re.search(r'\b(SHIFT\s*2|SHIFT\s*II|SHIFT\s*B|2ND|SFT\s*2|SFT\s*B)\b', val_str) or val_str in ("2", "B", "II", "SHIFT 2", "SHIFT B", "SHIFT II"):
            return "Shift II"
        # Check Shift I / 1 / A third
        if re.search(r'\b(SHIFT\s*1|SHIFT\s*I|SHIFT\s*A|1ST|SFT\s*1|SFT\s*A)\b', val_str) or val_str in ("1", "A", "I", "SHIFT 1", "SHIFT A", "SHIFT I"):
            return "Shift I"

        return val_str.title()

    @staticmethod
    def parse_number(value: Any, default: float = 0.0) -> float:
        """Clean numerical text strings into floating-point numbers."""
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return float(value)
        val_str = str(value).strip()
        val_str = re.sub(r'[^0-9.-]', '', val_str)
        try:
            return float(val_str)
        except ValueError:
            return default
