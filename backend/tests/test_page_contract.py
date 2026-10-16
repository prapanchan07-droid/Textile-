"""Every weaving page's JSON must match the TypeScript interface the frontend reads it through (frontend/src/types/pages.ts),
so a backend change cannot silently break a page. Top level and the main nested lists are checked, both ways."""
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

pytestmark = pytest.mark.pg
TS = Path(__file__).resolve().parents[2] / "frontend" / "src" / "types" / "pages.ts"
pytestmark = [pytest.mark.pg, pytest.mark.skipif(not TS.exists(), reason="frontend sources not present")]

PAGES = {"owner": "OwnerData", "command": "CommandData", "production": "ProductionData", "stoppages": "StoppagesData", "machines": "FleetData", "maintenance": "MaintenanceData",
         "workforce": "WorkforceData", "cockpit": "CockpitData", "handover": "HandoverData", "orders": "OrdersData", "scheduler": "SchedulerData", "insights": "InsightsData",
         "quality": "QualityData", "actions": "ActionsData", "compare": "CompareMeta"}
NESTED = {  # (interface, key) -> element interface
    ("CommandData", "kpis"): "KpiData", ("CommandData", "findings"): "Finding", ("CommandData", "alerts"): "SensorAlert", ("CommandData", "orders"): "OrderRow",
    ("OwnerData", "kpis"): "KpiData", ("OrdersData", "orders"): "OrderRow", ("OrdersData", "customers"): "CustomerRow", ("FleetData", "looms"): "MachineRow",
    ("FleetData", "alerts"): "SensorAlert", ("WorkforceData", "directory"): "DirectoryRow", ("InsightsData", "findings"): "Finding", ("SchedulerData", "orders"): "SchedulerOrder",
    ("SchedulerData", "moves"): "SchedulerMove", ("ProductionData", "kpis"): "KpiData", ("ProductionData", "looms"): "LoomPerf", ("CockpitData", "notes"): "Note",
}


def interfaces():
    src = TS.read_text()
    out = {}
    for name, body in re.findall(r"export interface (\w+) \{(.*?)\n\}", src, re.S):
        fields = {}
        for fname, opt in re.findall(r"^  (\w+)(\??):", body, re.M):
            fields[fname] = opt == "?"
        out[name] = fields
    return out


IFACES = interfaces()


def check(data: dict, iface: str, where: str):
    fields = IFACES[iface]
    extra = set(data) - set(fields)
    missing = {k for k, optional in fields.items() if not optional} - set(data)
    assert not extra, f"{where}: backend sends fields the frontend type does not declare: {sorted(extra)}"
    assert not missing, f"{where}: frontend type requires fields the backend does not send: {sorted(missing)}"


@pytest.fixture(scope="module")
def client(seeded):
    with TestClient(app) as c:
        yield c


def _login(client, user):
    r = client.post("/api/v1/auth/login", json={"username": user, "password": "Ashok@2026"})
    return {"Authorization": "Bearer " + r.json()["data"]["access_token"]}


@pytest.fixture(scope="module")
def mgr(client):
    return _login(client, "manager")


# pages that only some roles may open are read as that role
PAGE_USER = {"owner": "owner", "cockpit": "supervisor", "handover": "supervisor", "maintenance": "maintenance", "quality": "quality"}


@pytest.mark.parametrize("slug,iface", list(PAGES.items()))
def test_page_matches_its_typescript_interface(client, mgr, slug, iface):
    r = client.get(f"/api/v1/weaving/pages/{slug}", headers=_login(client, PAGE_USER[slug]) if slug in PAGE_USER else mgr)
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    check(data, iface, slug)
    for (parent, key), child in NESTED.items():
        if parent == iface and data.get(key):
            check(data[key][0], child, f"{slug}.{key}[0]")


def test_machine_detail_and_compare_run_match(client, mgr):
    d = client.get("/api/v1/weaving/pages/machines/SZ-05", headers=mgr).json()["data"]
    check(d, "MachineDetail", "machine detail")
    r = client.get("/api/v1/weaving/compare/run?type=loom&keys=AJ-10&keys=AJ-14", headers=mgr).json()["data"]
    check(r, "CompareResult", "compare run")


def test_interfaces_are_the_ones_we_think_they_are():
    assert len(IFACES) > 40 and "KpiData" in IFACES and "Finding" in IFACES
