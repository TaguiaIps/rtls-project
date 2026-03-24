from __future__ import annotations

import argparse
import sys

from sqlalchemy import select

from rtls_api.audit import write_audit_event
from rtls_api.auth import create_user, normalize_email
from rtls_api.config import Settings
from rtls_api.db import create_session_factory
from rtls_api.models import User, UserRole


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bootstrap the first RTLS Administrator account.")
    parser.add_argument("--email", required=True, help="Administrator email address")
    parser.add_argument("--password", required=True, help="Administrator password")
    parser.add_argument("--display-name", default="Platform Administrator", help="Display name")
    return parser


def run_bootstrap(args: argparse.Namespace, settings: Settings | None = None) -> int:
    settings = settings or Settings()
    session_factory = create_session_factory(settings)

    with session_factory() as db:
        existing_user = db.scalar(select(User).where(User.email == normalize_email(args.email)))
        if existing_user is not None:
            print("Administrator bootstrap failed: email already exists.", file=sys.stderr)
            return 1

        admin_count = db.scalar(
            select(User).where(User.role == UserRole.ADMINISTRATOR.value).limit(1)
        )
        if admin_count is not None:
            print(
                "Administrator bootstrap failed: an Administrator account already exists.",
                file=sys.stderr,
            )
            return 1

        user = create_user(
            db,
            email=args.email,
            password=args.password,
            role=UserRole.ADMINISTRATOR,
            display_name=args.display_name,
        )
        write_audit_event(
            db,
            action_category="configuration",
            action_type="admin.bootstrap.created",
            actor=user,
            target_type="user",
            target_id=user.id,
        )
        db.commit()

    print(f"Administrator account created for {normalize_email(args.email)}.")
    return 0


def main() -> int:
    parser = build_parser()
    return run_bootstrap(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
