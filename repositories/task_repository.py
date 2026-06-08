"""Data access helpers for tasks."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Task, User


def get_task_for_user(db: Session, task_id: int, user: User) -> Task | None:
    """Return a task only when it belongs to one of the user's projects."""

    statement = select(Task).join(Task.project).where(Task.id == task_id, Task.project.has(owner_id=user.id))
    return db.scalar(statement)


def save_task(db: Session, task: Task) -> Task:
    """Persist a task and return it with a database identity."""

    db.add(task)
    db.commit()
    db.refresh(task)
    return task
