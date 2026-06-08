"""User ORM model."""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class User(Base):
    """Service user who owns projects."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(80))
    password_hash: Mapped[str] = mapped_column(String(160))

    # 사용자가 삭제되면 사용자가 만든 프로젝트와 작업도 소유자를 잃으므로 함께 삭제한다.
    projects: Mapped[list["Project"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )
