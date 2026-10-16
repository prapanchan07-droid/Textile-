"""
Copy the legacy SQLite database (users, imported reports, ...) into PostgreSQL.

    python -m app.db.sqlite_to_postgres --source ai_factory_manager.db --target "$DATABASE_URL" [--dry-run]

Safety properties
  * The source file is only ever read. A verified backup copy is written first.
  * The target is brought to the latest migration (additive) before copying.
  * Rows are INSERTed with ON CONFLICT DO NOTHING: nothing already in PostgreSQL is overwritten,
    updated or deleted, and no table is truncated or dropped.
  * Everything happens in ONE transaction. Source and target are compared (row counts, every
    primary key, and every user's password hash and role) before it commits; any mismatch rolls
    the whole copy back. ``--dry-run`` does the full copy and validation, then rolls back.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy import create_engine, func, inspect, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

# The app settings insist on a configured database at import time. This tool is told its target on the
# command line, so use that for the import (an explicitly configured DATABASE_URL is left alone).
if "--target" in sys.argv[:-1]:
    os.environ.setdefault("DATABASE_URL", sys.argv[sys.argv.index("--target") + 1])

from app.db.migrate import upgrade_to_head  # noqa: E402
from app.db.session import Base  # noqa: E402
import app.db.models_registry  # noqa: E402,F401

BATCH = 1000
# Weaving tables are new in PostgreSQL; the SQLite file never had them.
SKIP_PREFIX = "wv_"


@dataclass
class TableReport:
    table: str
    source_rows: int
    inserted: int = 0
    already_present: int = 0
    missing_after: int = 0


@dataclass
class MigrationReport:
    backup_path: Optional[Path] = None
    backup_sha256: Optional[str] = None
    tables: List[TableReport] = field(default_factory=list)
    problems: List[str] = field(default_factory=list)
    committed: bool = False

    @property
    def ok(self) -> bool:
        return not self.problems


def backup_sqlite(source: Path, backup_dir: Path) -> tuple[Path, str]:
    """Consistent online backup (safe even while the app has the file open), verified by integrity check."""
    backup_dir.mkdir(parents=True, exist_ok=True)
    dest = backup_dir / f"{source.stem}.{datetime.now().strftime('%Y%m%d-%H%M%S')}.bak.db"
    src = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    dst = sqlite3.connect(dest)
    try:
        src.backup(dst)
        if dst.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError(f"Backup {dest} failed its integrity check")
    finally:
        src.close()
        dst.close()
    return dest, hashlib.sha256(dest.read_bytes()).hexdigest()


def migrate(source: Path, target_url: str, backup_dir: Path, dry_run: bool = False) -> MigrationReport:
    report = MigrationReport()
    if not source.is_file():
        raise FileNotFoundError(f"SQLite file not found: {source}")
    if not target_url.startswith("postgresql"):
        raise ValueError("The target must be a PostgreSQL URL (postgresql+psycopg://...)")

    report.backup_path, report.backup_sha256 = backup_sqlite(source, backup_dir)
    upgrade_to_head(target_url)

    src_engine = create_engine(f"sqlite:///file:{source}?mode=ro&uri=true")
    tgt_engine = create_engine(target_url)
    try:
        src_tables = set(inspect(src_engine).get_table_names())
        tables = [t for t in Base.metadata.sorted_tables if t.name in src_tables and not t.name.startswith(SKIP_PREFIX)]
        with src_engine.connect() as src, tgt_engine.connect() as tgt:
            tx = tgt.begin()
            try:
                for table in tables:
                    src_cols = {c["name"] for c in inspect(src_engine).get_columns(table.name)}
                    cols = [c for c in table.columns if c.name in src_cols]
                    rep = TableReport(table.name, source_rows=src.execute(select(func.count()).select_from(table)).scalar_one())
                    before = tgt.execute(select(func.count()).select_from(table)).scalar_one()
                    result = src.execution_options(stream_results=True).execute(select(*cols))
                    while True:
                        chunk = result.mappings().fetchmany(BATCH)
                        if not chunk:
                            break
                        tgt.execute(pg_insert(table).on_conflict_do_nothing(), [dict(r) for r in chunk])
                    rep.inserted = tgt.execute(select(func.count()).select_from(table)).scalar_one() - before
                    rep.already_present = rep.source_rows - rep.inserted
                    report.tables.append(rep)

                _validate(src, tgt, tables, report)
                if report.ok and not dry_run:
                    tx.commit()
                    report.committed = True
                else:
                    tx.rollback()
            except Exception:
                tx.rollback()
                raise
    finally:
        src_engine.dispose()
        tgt_engine.dispose()
    return report


def _validate(src, tgt, tables, report: MigrationReport) -> None:
    for table, rep in zip(tables, report.tables):
        pk_cols = [c for c in table.primary_key.columns]
        src_pks = {tuple(r) for r in src.execute(select(*pk_cols))}
        tgt_pks = {tuple(r) for r in tgt.execute(select(*pk_cols))}
        rep.missing_after = len(src_pks - tgt_pks)
        if rep.missing_after:
            report.problems.append(f"{table.name}: {rep.missing_after} source row(s) are missing from PostgreSQL")
        if len(src_pks) != rep.source_rows:
            report.problems.append(f"{table.name}: primary-key count differs from row count in the source")

    if "users" in {t.name for t in tables}:
        users = Base.metadata.tables["users"]
        cols = [users.c.id, users.c.username, users.c.role, users.c.password_hash, users.c.is_active]
        src_users = {r.id: tuple(r) for r in src.execute(select(*cols))}
        tgt_users = {r.id: tuple(r) for r in tgt.execute(select(*cols))}
        for uid, row in src_users.items():
            if tgt_users.get(uid) != row:
                report.problems.append(f"users: account {row[1]!r} differs between SQLite and PostgreSQL (hash, role or status)")


def _print(report: MigrationReport, dry_run: bool) -> None:
    print(f"Backup: {report.backup_path}  (sha256 {report.backup_sha256})")
    print(f"{'table':<28}{'source':>8}{'inserted':>10}{'already there':>15}")
    for t in report.tables:
        print(f"{t.table:<28}{t.source_rows:>8}{t.inserted:>10}{t.already_present:>15}")
    for p in report.problems:
        print(f"PROBLEM: {p}")
    if report.committed:
        print("Committed. Validation passed.")
    elif report.ok and dry_run:
        print("Dry run: validation passed, nothing was written.")
    else:
        print("Rolled back. Nothing was written to PostgreSQL.")


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True, type=Path, help="path to the SQLite file")
    ap.add_argument("--target", required=True, help="PostgreSQL URL")
    ap.add_argument("--backup-dir", type=Path, default=Path("backups"))
    ap.add_argument("--dry-run", action="store_true", help="copy and validate, then roll back")
    args = ap.parse_args(argv)
    report = migrate(args.source, args.target, args.backup_dir, args.dry_run)
    _print(report, args.dry_run)
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
