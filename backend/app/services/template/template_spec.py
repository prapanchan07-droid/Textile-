"""Field definitions for the downloadable data template (one sheet per data set)."""
from typing import Dict, List, NamedTuple

TEMPLATE_MARKER_SHEET = "Instructions"
TEMPLATE_REPORT_TYPE = "TEMPLATE"


class Col(NamedTuple):
    header: str
    required: bool
    kind: str        # date | text | number | int | shift | yesno | status
    description: str
    example: str


MACHINE_SHEET = "Machine_Data"
MANPOWER_SHEET = "Manpower"
QUALITY_SHEET = "Quality"
BUSINESS_SHEET = "Business"
STOCK_SHEET = "Stock"
ACTIONS_SHEET = "Actions"

SHEETS: Dict[str, dict] = {
    MACHINE_SHEET: {
        "purpose": "Production, downtime, energy and quality per machine per shift. "
                   "Feeds Factory Overview, Production, Machines & Downtime, Machine Comparison and Decision Center.",
        "columns": [
            Col("Date", True, "date", "Report date (YYYY-MM-DD)", "2026-09-22"),
            Col("Unit", False, "text", "Mill unit. Leave blank if not applicable", "Unit I"),
            Col("Section", False, "text", "Section / area of the machine. Defaults to Machine Type", "Spinning Unit 1"),
            Col("Shift", False, "shift", "Shift I / II / III. Leave blank for a full-day row", "Shift II"),
            Col("Machine Type", True, "text", "Vortex, Airjet, Ring Frame, Simplex, Carding ...", "Vortex"),
            Col("Machine ID", True, "text", "Unique machine number", "V-09"),
            Col("Target Kg", True, "number", "Planned production (kg)", "3033"),
            Col("Actual Kg", True, "number", "Actual production (kg)", "2790"),
            Col("Downtime Min", False, "number", "Stoppage minutes", "80"),
            Col("Downtime Reason", False, "text", "e.g. Electrical / Power, Maintenance, Cleaning, Material / Process", "Electrical / Power"),
            Col("Planned Downtime", False, "yesno", "Y if the downtime was planned (cleaning, scheduled maintenance), otherwise N", "N"),
            Col("Stoppage Count", False, "int", "Number of stoppages", "3"),
            Col("Power Events", False, "int", "Voltage drops / trips", "1"),
            Col("Energy kWh", False, "number", "Energy consumed", "620"),
            Col("Quality Rating %", False, "number", "Quality grade % for the row", "96.1"),
            Col("Main Issue", False, "text", "Short remark on the main problem", "Repeated motor trip"),
            Col("Last Maintenance", False, "text", "Date of last maintenance", "2026-09-18"),
            Col("Next Maintenance", False, "text", "Date of next maintenance", "2026-09-28"),
        ],
    },
    MANPOWER_SHEET: {
        "purpose": "Required vs available workers. Feeds Manpower & Quality and Decision Center.",
        "columns": [
            Col("Date", True, "date", "Report date (YYYY-MM-DD)", "2026-09-22"),
            Col("Department", True, "text", "Department name", "Spinning"),
            Col("Shift", False, "shift", "Leave blank for a full-day count", ""),
            Col("Required", True, "int", "Sanctioned / planned workers", "420"),
            Col("Available", True, "int", "Workers present", "390"),
        ],
    },
    QUALITY_SHEET: {
        "purpose": "Quality test readings against their limits (lower is better). Feeds Manpower & Quality.",
        "columns": [
            Col("Date", True, "date", "Report date (YYYY-MM-DD)", "2026-09-22"),
            Col("Machine ID", False, "text", "Machine the sample came from (matches Machine_Data)", "V-09"),
            Col("Parameter", True, "text", "Thick/Km, Thin/Km, Neps/Km, U%, Count CV, Strength CV ...", "Thick/Km"),
            Col("Value", True, "number", "Measured value", "52"),
            Col("Limit", True, "number", "Maximum allowed value", "40"),
            Col("Unit", False, "text", "Unit of the value", "/km"),
        ],
    },
    BUSINESS_SHEET: {
        "purpose": "Daily sales, dispatch and collections. Feeds Revenue & Loss and Decision Center.",
        "columns": [
            Col("Date", True, "date", "Report date (YYYY-MM-DD)", "2026-09-22"),
            Col("Revenue Lakhs", False, "number", "Sales value for the day (Rs lakhs)", "4.2"),
            Col("Orders Meters", False, "number", "Order quantity booked (m)", "30857"),
            Col("Dispatched Meters", False, "number", "Quantity dispatched (m)", "21418"),
            Col("Collected Lakhs", False, "number", "Payments collected (Rs lakhs)", "11.8"),
            Col("Outstanding Lakhs", False, "number", "Closing receivable balance on that date (Rs lakhs)", "90.7"),
        ],
    },
    STOCK_SHEET: {
        "purpose": "Stock value against its limit. The latest date is used. Feeds Revenue & Loss.",
        "columns": [
            Col("Date", True, "date", "Stock as-on date (YYYY-MM-DD)", "2026-09-22"),
            Col("Category", True, "text", "Fabric Stock, Yarn Stock - Unit I ...", "Fabric Stock"),
            Col("Current Value Lakhs", True, "number", "Current stock value (Rs lakhs)", "12.34"),
            Col("Limit Value Lakhs", True, "number", "Maximum stock value allowed (Rs lakhs)", "5.00"),
        ],
    },
    ACTIONS_SHEET: {
        "purpose": "Open management actions. Feeds the Decision Center action tracker.",
        "columns": [
            Col("Date", True, "date", "Date raised (YYYY-MM-DD)", "2026-09-23"),
            Col("Issue", True, "text", "What is wrong", "V-09 downtime"),
            Col("Action", True, "text", "What will be done", "Check motor alignment"),
            Col("Owner", False, "text", "Responsible person / team", "Maintenance Manager"),
            Col("Status", False, "status", "OPEN, IN_PROGRESS or COMPLETED", "OPEN"),
        ],
    },
}

DATA_SHEET_NAMES: List[str] = list(SHEETS.keys())
