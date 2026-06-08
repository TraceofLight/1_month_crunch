"""Database configuration and initialization helpers."""

from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
CONNECT_ARGS = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=CONNECT_ARGS)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM models."""


def get_db() -> Generator[Session, None, None]:
    """Provide a database session for FastAPI dependencies."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables and seed the demo user if it does not exist."""

    from auth.passwords import hash_password
    from models import Project, Task, User
    from repositories.user_repository import get_user_by_username

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if get_user_by_username(db, "demo") is None:
            user = User(
                username="demo",
                display_name="demo",
                password_hash=hash_password("demo1234"),
            )
            project = Project(name="샘플 프로젝트", description="로그인 후 확인할 수 있는 예시 데이터", owner=user)
            project.tasks.append(Task(title="첫 작업 완료해 보기", status="todo"))
            db.add(user)
            db.commit()
