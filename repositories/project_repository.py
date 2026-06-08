"""Data access helpers for projects."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from models import Project, User


def list_projects_for_user(db: Session, user: User) -> list[Project]:
    """Return projects with tasks for the current user."""

    statement = (
        select(Project)
        .options(selectinload(Project.owner), selectinload(Project.tasks))
        .where(Project.owner_id == user.id)
        .order_by(Project.id)
    )
    return list(db.scalars(statement))


def get_project_for_user(db: Session, project_id: int, user: User) -> Project | None:
    """Return a project only when it belongs to the current user."""

    return db.scalar(select(Project).where(Project.id == project_id, Project.owner_id == user.id))


def save_project(db: Session, project: Project) -> Project:
    """Persist a project and return it with a database identity."""

    db.add(project)
    db.commit()
    db.refresh(project)
    return project
