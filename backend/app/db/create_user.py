"""
Create a login (needed on a fresh production database, where demo logins are never created).

    python -m app.db.create_user --username owner --full-name "A. Owner" --role OWNER
    PASSWORD_VAR=... python -m app.db.create_user --username owner ... --password-env PASSWORD_VAR

The password is read from an environment variable or prompted for (never passed on the command line, where it would
end up in shell history). An existing username is refused: nothing is overwritten unless you pass --reset-password.
"""
from __future__ import annotations

import argparse
import getpass
import os
import sys
import uuid
from typing import List, Optional

from sqlalchemy import select

from app.core.roles import Role
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User

MIN_PASSWORD_LENGTH = 10


def create_user(db, username: str, full_name: str, role: Role, password: str, reset_password: bool = False) -> str:
    username = username.strip().lower()
    if not username or " " in username:
        raise ValueError("username must be non-empty and contain no spaces")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"password must be at least {MIN_PASSWORD_LENGTH} characters")
    existing = db.scalar(select(User).where(User.username == username))
    if existing is not None:
        if not reset_password:
            raise ValueError(f"user {username!r} already exists (use --reset-password to change its password)")
        existing.password_hash = hash_password(password)
        db.commit()
        return "password reset"
    db.add(User(id=str(uuid.uuid4()), username=username, full_name=full_name, role=role.value, password_hash=hash_password(password)))
    db.commit()
    return "created"


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--username", required=True)
    ap.add_argument("--full-name", default="")
    ap.add_argument("--role", required=True, choices=[r.value for r in Role])
    ap.add_argument("--password-env", help="name of an environment variable holding the password (otherwise you are prompted)")
    ap.add_argument("--reset-password", action="store_true", help="allow changing the password of an existing user")
    args = ap.parse_args(argv)
    password = os.environ.get(args.password_env, "") if args.password_env else getpass.getpass("Password: ")
    if not args.password_env and password != getpass.getpass("Repeat password: "):
        print("Passwords do not match", file=sys.stderr)
        return 1
    try:
        with SessionLocal() as db:
            print(f"{args.username.strip().lower()}: {create_user(db, args.username, args.full_name or args.username, Role(args.role), password, args.reset_password)}")
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
