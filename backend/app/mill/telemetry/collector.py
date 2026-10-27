"""
Telemetry collector: polls enabled machine connections, stores readings, tracks connection health.

  * Each connection is polled at its own `poll_seconds`; failures back off exponentially (capped at 30 min) so a
    fragile machine interface is never hammered.
  * A reading whose timestamp is in the future (> 2 min) or older than the stale window is rejected and counted as a
    failure: a delayed or clock-skewed value must not look live.
  * States: CONNECTED (fresh reading), STALE (last good reading older than TELEMETRY_STALE_SECONDS), OFFLINE / ERROR
    (reads failing), AWAITING_VENDOR_INFO (adapter cannot run yet). A connection with no successful read is never
    shown as healthy.
  * One connection's failure never stops the others; nothing here raises to the caller.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.mill.models import Loom, MachineConnection, TelemetrySample
from app.mill.telemetry.adapters import ADAPTERS, AdapterError, AdapterNotReady

MAX_BACKOFF_S = 1800


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def live_state(conn: Optional[MachineConnection], now: Optional[datetime] = None) -> str:
    """What the UI may show. Data older than the stale window is STALE, whatever the stored state says."""
    if conn is None or conn.adapter == "NONE":
        return "NOT_CONFIGURED"
    if conn.state == "AWAITING_VENDOR_INFO":
        return "AWAITING_VENDOR_INFO"
    if not conn.enabled:
        return "CONFIGURED"
    if conn.last_success_at is None:
        return "ERROR" if conn.state == "ERROR" else "OFFLINE"
    if (now or utcnow()) - conn.last_success_at > timedelta(seconds=settings.TELEMETRY_STALE_SECONDS):
        return "STALE"
    return conn.state if conn.state in ("OFFLINE", "ERROR") else "CONNECTED"  # recent success but the latest read failed


def _fail(conn: MachineConnection, now: datetime, state: str, err: str) -> None:
    conn.consecutive_failures += 1
    conn.state, conn.last_error = state, err[:2000]
    delay = min(MAX_BACKOFF_S, conn.poll_seconds * (2 ** min(conn.consecutive_failures, 10)))
    conn.next_attempt_at = now + timedelta(seconds=delay)


def poll(db: Session, conn: MachineConnection, loom: Loom, now: datetime) -> str:
    conn.last_attempt_at = now
    cls = ADAPTERS.get(conn.adapter)
    if cls is None:
        _fail(conn, now, "ERROR", f"Unknown adapter {conn.adapter}")
        return "error"
    creds = os.environ.get(conn.credentials_env) if conn.credentials_env else None
    adapter = cls(conn.host, conn.port, creds)
    try:
        r = adapter.read(loom.code, now)
    except AdapterNotReady as e:
        conn.state, conn.last_error = "AWAITING_VENDOR_INFO", str(e)
        conn.next_attempt_at = now + timedelta(seconds=MAX_BACKOFF_S)
        return "not_ready"
    except (AdapterError, OSError, TimeoutError, ValueError) as e:
        _fail(conn, now, "OFFLINE", f"{type(e).__name__}: {e}")
        return "failed"
    except Exception as e:  # adapter bug: keep the collector alive
        logger.error(f"Adapter {conn.adapter} crashed for {loom.code}: {e}", exc_info=True)
        _fail(conn, now, "ERROR", f"{type(e).__name__}: {e}")
        return "error"
    ts = r.sampled_at if r.sampled_at.tzinfo else r.sampled_at.replace(tzinfo=timezone.utc)
    if ts > now + timedelta(minutes=2) or (now - ts).total_seconds() > settings.TELEMETRY_STALE_SECONDS:
        _fail(conn, now, "ERROR", f"Rejected reading with timestamp {ts.isoformat()} (now {now.isoformat()})")
        return "rejected"
    if r.state not in ("RUNNING", "STOPPED", "UNKNOWN"):
        _fail(conn, now, "ERROR", f"Rejected reading with state {r.state!r}")
        return "rejected"
    db.add(TelemetrySample(loom_id=loom.id, sampled_at=ts, received_at=now, data_origin=adapter.origin, state=r.state, rpm=r.rpm,
                           efficiency_pct=r.efficiency_pct, picks_counter=r.picks_counter, stop_code=r.stop_code, warp_stops=r.warp_stops,
                           weft_stops=r.weft_stops, air_nm3=r.air_nm3, values=r.values))
    conn.state, conn.last_success_at, conn.consecutive_failures, conn.last_error = "CONNECTED", now, 0, None
    conn.next_attempt_at = now + timedelta(seconds=conn.poll_seconds)
    return "ok"


def collect_once(db: Session, now: Optional[datetime] = None) -> Dict[str, int]:
    now = now or utcnow()
    out: Dict[str, int] = {}
    q = select(MachineConnection, Loom).join(Loom).where(MachineConnection.enabled.is_(True), MachineConnection.adapter != "NONE")
    for conn, loom in db.execute(q):
        if conn.next_attempt_at and conn.next_attempt_at > now:
            out["skipped_backoff"] = out.get("skipped_backoff", 0) + 1
            continue
        try:
            with db.begin_nested():
                res = poll(db, conn, loom, now)
        except Exception as e:
            logger.error(f"Polling {loom.code} failed: {e}", exc_info=True)
            res = "error"
        out[res] = out.get(res, 0) + 1
    cutoff = now - timedelta(days=settings.TELEMETRY_RETENTION_DAYS)
    db.execute(delete(TelemetrySample).where(TelemetrySample.sampled_at < cutoff))
    db.flush()
    return out
