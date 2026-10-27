"""
Command line for operators and administrators.

    python -m app.mill.cli import FILE [FILE ...]   # preview + commit each file, print the import summary
    python -m app.mill.cli evaluate-alerts            # run the alert rules over the stored data
    python -m app.mill.cli bootstrap-groups [--count 11]
    python -m app.mill.cli collect-once               # one telemetry polling cycle (enabled connections only)
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional


def main(argv: Optional[List[str]] = None) -> int:
    from app.db.session import SessionLocal

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("import")
    p.add_argument("files", nargs="+")
    sub.add_parser("evaluate-alerts")
    b = sub.add_parser("bootstrap-groups")
    b.add_argument("--count", type=int, default=11)
    sub.add_parser("collect-once")
    args = ap.parse_args(argv)

    with SessionLocal() as db:
        if args.cmd == "import":
            from app.mill.alerts.engine import evaluate_all
            from app.mill.importers.service import ImportRefused, import_file

            failed = 0
            for path in args.files:
                with open(path, "rb") as f:
                    content = f.read()
                try:
                    batch = import_file(db, content, os.path.basename(path))
                except ImportRefused as e:
                    db.rollback()
                    print(f"{path}: refused: {e}")
                    failed += 1
                    continue
                rec = batch.reconciliation or []
                mism = sum(1 for c in rec if c["status"] == "MISMATCH")
                print(f"{path}: batch #{batch.id} {batch.source_format} {batch.period_start}..{batch.period_end} "
                      f"inserted={batch.records_inserted} updated={batch.records_updated} unchanged={batch.records_unchanged} "
                      f"errors={batch.error_count} warnings={batch.warning_count} checks={len(rec)} mismatches={mism}")
            print(evaluate_all(db))
            db.commit()
            return 1 if failed else 0
        if args.cmd == "evaluate-alerts":
            from app.mill.alerts.engine import evaluate_all

            print(evaluate_all(db))
            db.commit()
            return 0
        if args.cmd == "bootstrap-groups":
            from app.mill.seed import bootstrap_groups

            made = bootstrap_groups(db, args.count)
            db.commit()
            print(f"created {len(made)} groups" if made else "groups already exist; nothing created")
            return 0
        if args.cmd == "collect-once":
            from app.mill.telemetry.collector import collect_once

            print(collect_once(db))
            db.commit()
            return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
