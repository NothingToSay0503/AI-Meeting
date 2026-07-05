import argparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole, UserStatus


def seed_admin_user(
    db: Session,
    *,
    username: str,
    password: str,
    display_name: str = "系统管理员",
    email: str | None = None,
) -> User:
    existing = db.scalar(select(User).where(User.username == username))
    if existing is not None:
        return existing

    user = User(
        username=username,
        password_hash=hash_password(password),
        display_name=display_name,
        email=email,
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the first admin user.")
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--display-name", default="系统管理员")
    parser.add_argument("--email", default=None)
    args = parser.parse_args()

    with SessionLocal() as db:
        user = seed_admin_user(
            db,
            username=args.username,
            password=args.password,
            display_name=args.display_name,
            email=args.email,
        )
        print(f"Admin user ready: {user.username}")


if __name__ == "__main__":
    main()
