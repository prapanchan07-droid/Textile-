"""python -m app.weaving.seed {reference|demo} ..."""
import argparse
import sys
from datetime import date

from app.core.config import settings
from app.db.migrate import current_revision, head_revision
from app.db.session import SessionLocal
from app.weaving.seed.demo import reset_demo, seed_demo
from app.weaving.seed.reference import ensure_reference_data


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("reference", help="load shifts, stop reasons and defect types (safe in any environment)")
    d = sub.add_parser("demo", help="load deterministic DEMONSTRATION data (refuses to run in production)")
    d.add_argument("--days", type=int, default=21, help="history length when first seeding (default 21)")
    d.add_argument("--end-date", type=date.fromisoformat, default=None, help="last production day (default: today)")
    d.add_argument("--reset-demo", action="store_true", help="first delete the existing DEMO rows (only rows marked DEMO), then load fresh demo data")
    args = ap.parse_args()
    if current_revision(settings.DATABASE_URL) != head_revision():
        print('The database schema is not up to date. Run `alembic upgrade head` first.', file=sys.stderr)
        return 2
    with SessionLocal() as db:
        if args.cmd == "reference":
            print("Added:", ensure_reference_data(db))
        else:
            if args.reset_demo:
                print("Deleted DEMO rows:", {k: v for k, v in reset_demo(db).items() if v})
            print(seed_demo(db, days=args.days, end_date=args.end_date))
        db.commit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
