"""
Machine data adapters: one interface, one implementation per manufacturer system.

An IP address alone does not say which protocol a loom speaks or what it exposes. The Toyota and Tsudakoma
adapters below are therefore deliberately not implemented: they declare what is needed (OEM interface, gateway,
credentials, field list) and report AWAITING_VENDOR_INFO. No endpoint, port, register or protocol is guessed.

All adapters are read-only. The interface has no method that writes to a machine.

The simulator produces deterministic readings so the whole pipeline (collector, storage, live status, stale
detection, alerts) can be exercised before real connectivity exists. Its samples are stored with
data_origin = SIMULATED and are shown as simulated everywhere.
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional

from app.mill import constants as C


class AdapterNotReady(RuntimeError):
    """The integration cannot run yet (missing vendor information, interface or credentials)."""


class AdapterError(RuntimeError):
    """A read was attempted and failed (timeout, refused, bad payload)."""


@dataclass
class Reading:
    sampled_at: datetime
    state: str  # RUNNING / STOPPED / UNKNOWN
    rpm: Optional[float] = None
    efficiency_pct: Optional[float] = None
    picks_counter: Optional[float] = None
    stop_code: Optional[str] = None
    warp_stops: Optional[int] = None
    weft_stops: Optional[int] = None
    air_nm3: Optional[float] = None
    values: Dict[str, object] = field(default_factory=dict)


class Adapter:
    name = "NONE"
    origin = C.ORIGIN_LIVE
    requirements: str = ""

    def __init__(self, host: Optional[str], port: Optional[int], credentials: Optional[str], timeout_s: float = 5.0):
        self.host, self.port, self.credentials, self.timeout_s = host, port, credentials, timeout_s

    def read(self, loom_code: str, now: datetime) -> Reading:  # pragma: no cover - interface
        raise NotImplementedError


class SimulatorAdapter(Adapter):
    """Deterministic per loom and minute: the same inputs always give the same reading."""
    name = "SIMULATOR"
    origin = C.ORIGIN_SIMULATED
    requirements = "None. For testing the monitoring pipeline only; readings are marked SIMULATED."

    def read(self, loom_code: str, now: datetime) -> Reading:
        minute = int(now.timestamp() // 60)
        h = int(hashlib.sha256(f"{loom_code}:{minute}".encode()).hexdigest()[:8], 16)
        base_rpm = 1200 if loom_code.startswith(("TY", "TS")) else 260
        running = h % 10 != 0  # about 10% of samples stopped
        rpm = base_rpm * (1 + 0.01 * math.sin(minute / 30)) if running else 0.0
        return Reading(
            sampled_at=now.replace(second=0, microsecond=0), state="RUNNING" if running else "STOPPED", rpm=round(rpm, 1),
            efficiency_pct=round(85 + (h % 120) / 10, 1), picks_counter=float(minute * base_rpm),
            stop_code=None if running else ("WARP" if h % 3 == 0 else "WEFT"), values={"simulated": True},
        )


class _VendorAdapter(Adapter):
    def read(self, loom_code: str, now: datetime) -> Reading:
        raise AdapterNotReady(f"{self.name}: integration not available yet. Needed: {self.requirements}")


class ToyotaTMSAdapter(_VendorAdapter):
    name = "TOYOTA_TMS"
    requirements = ("Toyota's documented read interface for the mill's monitoring system (the source of the 'Shift Report' export), "
                    "loom model/generation per loom, approved access from the collector host, credentials, and the field list "
                    "(state, RPM, picks, stop codes, air flow if fitted).")


class TsudakomaTISSAdapter(_VendorAdapter):
    name = "TSUDAKOMA_TISS"
    requirements = ("Tsudakoma's documented interface for the mill's monitoring system or TISS gateway (the source of the "
                    "'Report by term' export), approved network path, credentials, and confirmation of which values are exposed "
                    "(air consumption is currently 0 for all looms in the exports, i.e. not measured).")


ADAPTERS = {"SIMULATOR": SimulatorAdapter, "TOYOTA_TMS": ToyotaTMSAdapter, "TSUDAKOMA_TISS": TsudakomaTISSAdapter}


def requirements() -> Dict[str, str]:
    return {k: v.requirements for k, v in ADAPTERS.items()}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
