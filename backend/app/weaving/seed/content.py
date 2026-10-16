"""
Synthetic content for the demonstration mill: people, customers, suppliers, machine specifications and the order book.
Everything here is invented. Names are plausible for a South Indian mill and refer to no real person or company, and
phone numbers are obviously fake. Day offsets count from the demo epoch (day 0 = first seeded production day).
"""
from typing import Dict, List

FIRST_NAMES = [
    "Murugan", "Selvam", "Ravi", "Karthik", "Senthil", "Gopal", "Arun", "Prakash", "Dinesh", "Suresh", "Mani", "Kumar", "Rajesh", "Vijay",
    "Anand", "Saravanan", "Balaji", "Ganesh", "Harish", "Manoj", "Naveen", "Pandian", "Sathish", "Thangaraj", "Velu", "Muthu", "Kannan",
    "Palani", "Raja", "Siva", "Lakshmi", "Meena", "Priya", "Kavitha", "Devi", "Selvi", "Anitha", "Revathi", "Malathi", "Sumathi", "Radha",
    "Jothi", "Bharathi", "Vasanth", "Elango", "Gunasekaran", "Ilango", "Jeeva", "Kamal", "Logesh", "Mohan", "Nandha", "Om Prakash",
    "Perumal", "Rathinam", "Sakthi", "Tamil", "Udhay", "Venkat", "Yuvaraj", "Abinaya", "Deepa", "Gayathri", "Harini", "Indhu",
]
INITIALS = ["K", "S", "R", "M", "P", "V", "A", "N", "T", "G", "B", "D"]

CUSTOMERS = [
    # code, name, segment, city, tier
    ("C01", "Sri Lakshmi Garments", "Garment", "Tiruppur", "A"),
    ("C02", "Coastal Exports Pvt Ltd", "Export", "Chennai", "A"),
    ("C03", "Kovai Shirting House", "Garment", "Coimbatore", "B"),
    ("C04", "Madurai Hosiery Mills", "Garment", "Madurai", "B"),
    ("C05", "Bharath Uniforms", "Uniform", "Erode", "B"),
    ("C06", "Deccan Home Textiles", "Home textile", "Hyderabad", "A"),
    ("C07", "Bengaluru Apparel Co", "Garment", "Bengaluru", "B"),
    ("C08", "Salem Fabric Traders", "Trader", "Salem", "C"),
]

SUPPLIERS = ["Vardhan Spinning Mills", "Kongu Cotton Yarns", "Annai Textiles"]

# Order book. Sequences per style: each order runs on every loom of the style from `start` until the next order starts.
# (suffix, customer, ordered_m, start day, due day, priority, rate adjustment vs the style's standard rate)
RUNNING_ORDERS: Dict[str, List[tuple]] = {
    "S-101": [("2417", "C01", 14500, -6, 8, "B", 1.00), ("2431", "C03", 52000, 5, 28, "B", 1.02)],
    "S-415": [("2409", "C02", 25500, -8, 10, "A", 1.03), ("2428", "C02", 56000, 8, 24, "A", 1.04)],
    "S-522": [("2402", "C05", 35000, -9, 9, "B", 0.98), ("2433", "C04", 60000, 9, 35, "C", 0.99)],
    "S-310": [("2422", "C06", 22000, 0, 21, "A", 1.05)],
    "S-630": [("2425", "C07", 18000, 2, 28, "B", 1.00)],
    "S-204": [("2419", "C08", 16000, 1, 26, "C", 0.97)],
}
# Booked but not yet on a loom: the AI scheduler plans these. (suffix, style, customer, ordered_m, due day, priority)
QUEUED_ORDERS = [
    ("2441", "S-415", "C01", 20000, 30, "A"),
    ("2444", "S-310", "C06", 9000, 34, "B"),
    ("2446", "S-101", "C03", 25000, 36, "B"),
    ("2449", "S-630", "C07", 10000, 38, "C"),
]

AIRJET_MODEL = ("Picanol", "OMNIplus-800", "Dobby", 4, 11.0, 230)
SULZER_MODEL = ("Sulzer Rüti", "P7100", "Cam", 4, 7.5, 330)

DESIGNATIONS = {"WEAVER": ["Weaver", "Senior Weaver"], "FITTER": ["Loom Fitter", "Senior Fitter"], "INSPECTOR": ["Fabric Inspector"], "TECHNICIAN": ["Maintenance Technician"], "SUPERVISOR": ["Shift Supervisor"]}
DEPARTMENTS = {"WEAVER": "Weaving", "FITTER": "Weaving", "INSPECTOR": "Quality", "TECHNICIAN": "Maintenance", "SUPERVISOR": "Weaving"}

# Shift hand-over notes for the last three production days (offset from the last seeded day): (days back, shift, loom, severity, category, text)
NOTES = [
    (0, "I", "AJ-14", "WARNING", "ISSUE", "AJ-14 weft stops are still high. Nozzle cleaned at 8 am, no change. Main-nozzle pressure on the gauge looks lower than the neighbouring looms."),
    (0, "I", "SZ-05", "URGENT", "MAINTENANCE_REQUEST", "SZ-05 is running hot and noisy near the gripper side. Asked maintenance to check the bearing before it fails."),
    (0, "I", None, "INFO", "HANDOVER", "Beam change for the S-415 row done on time. Next beams staged at the knotting bay."),
    (1, "III", "SZ-07", "WARNING", "ISSUE", "SZ-07 tripped three times after 2 am (power dip suspected). Restarted each time; output lost about 25 minutes."),
    (1, "III", None, "WARNING", "HANDOVER", "Only 6 of 9 weavers present. Two banks run by the floater and a neighbour. Fitter response was slow after midnight."),
    (1, "II", "AJ-18", "INFO", "QUALITY", "Inspection flagged repeated warp streaks on AJ-18 rolls. Reed checked, looks fine."),
    (1, "I", None, "INFO", "HANDOVER", "S-204 order moved to SZ-03 as planned. First roll looked good."),
    (2, "III", "AJ-09", "INFO", "ISSUE", "AJ-09 motor feels warmer than usual. Logged, no stoppage yet."),
    (2, "II", None, "WARNING", "QUALITY", "Float defects on S-204 from the night looms, second time this week. QA asked to compare with day shift."),
    (2, "I", None, "INFO", "HANDOVER", "Yarn lot YL-415-07 opened for the S-415 row. Warp breaks look higher than usual on the new beams."),
]

# Employees who sit outside the weaving shifts' regular weavers
SUPERVISORS = [("S-I-01", "I"), ("S-II-01", "II"), ("S-III-01", "III")]
