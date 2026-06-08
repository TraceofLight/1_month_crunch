"""Project ORM model."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Project(Base):
    """Project that groups user tasks."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, default="")

    owner: Mapped["User"] = relationship(back_populates="projects")
    # 프로젝트 삭제 시 하위 작업만 남으면 업무 맥락이 사라지므로 고아 작업을 함께 제거한다.
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
