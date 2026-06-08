"""Business rules for projects and tasks."""

from __future__ import annotations

from sqlalchemy.orm import Session

from auth.exceptions import DomainError
from models import Project, Task, User
from repositories.project_repository import get_project_for_user, list_projects_for_user, save_project
from repositories.task_repository import get_task_for_user, save_task


STATUS_LABELS = {
    "todo": "진행 전",
    "done": "완료",
}


def status_label(status: str) -> str:
    """Return the Korean label for a task status."""

    return STATUS_LABELS.get(status, status)


def list_dashboard_projects(db: Session, user: User) -> list[Project]:
    """Return the projects shown on the protected dashboard."""

    return list_projects_for_user(db, user)


def create_project(db: Session, user: User, name: str, description: str) -> Project:
    """Create a project owned by the current user."""

    clean_name = name.strip()
    if not clean_name:
        raise DomainError("프로젝트 이름을 입력해야 합니다.")
    return save_project(db, Project(owner_id=user.id, name=clean_name, description=description.strip()))


def create_task(db: Session, user: User, project_id: int, title: str) -> Task:
    """Create a task under a project owned by the current user."""

    project = get_project_for_user(db, project_id, user)
    if project is None:
        raise DomainError("작업을 추가할 프로젝트를 찾을 수 없습니다.")
    clean_title = title.strip()
    if not clean_title:
        raise DomainError("작업 제목을 입력해야 합니다.")
    return save_task(db, Task(project_id=project.id, title=clean_title, status="todo"))


def complete_task(db: Session, user: User, task_id: int) -> tuple[str, str]:
    """Change a task from todo to done and return previous and new labels."""

    task = get_task_for_user(db, task_id, user)
    if task is None:
        raise DomainError("상태를 변경할 작업을 찾을 수 없습니다.")
    previous = task.status
    if previous == "done":
        raise DomainError("이미 완료된 작업입니다.")
    task.status = "done"
    db.commit()
    return status_label(previous), status_label(task.status)
