"""
In-process background loop: telemetry polling, deadline/stale alert checks and escalation every
BACKGROUND_INTERVAL_SECONDS. Runs in a daemon thread started with the API (one API process). For several API
workers, set BACKGROUND_JOBS_ENABLED=false on all but one, or run `python -m app.mill.cli collect-once` and
`evaluate-alerts` from a scheduler instead.
"""
from __future__ import annotations

import threading

from app.core.config import settings
from app.core.logging import logger

_stop = threading.Event()
_thread = None


def _tick() -> None:
    from app.db.session import SessionLocal
    from app.mill.alerts.engine import escalate, evaluate_system
    from app.mill.telemetry.collector import collect_once

    with SessionLocal() as db:
        try:
            collect_once(db)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Telemetry cycle failed: {e}", exc_info=True)
        try:
            stats = {"evaluated": 0, "opened": 0, "refreshed": 0, "cleared": 0, "cooldown": 0}
            evaluate_system(db, stats)
            escalate(db)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Alert maintenance cycle failed: {e}", exc_info=True)


def _run() -> None:
    while not _stop.wait(settings.BACKGROUND_INTERVAL_SECONDS):
        _tick()


def start() -> None:
    global _thread
    if not settings.BACKGROUND_JOBS_ENABLED or (_thread and _thread.is_alive()):
        return
    _stop.clear()
    _thread = threading.Thread(target=_run, name="mill-background", daemon=True)
    _thread.start()
    logger.info(f"Background jobs every {settings.BACKGROUND_INTERVAL_SECONDS}s")


def stop() -> None:
    _stop.set()
