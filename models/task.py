"""Task ORM model."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Task(Base):
    """Task whose status can change through business actions."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    title: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(20), default="todo")

    project: Mapped["Project"] = relationship(back_populates="tasks")
