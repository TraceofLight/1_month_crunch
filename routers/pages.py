"""Page routes for the public home and protected application flow."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user, require_user
from database import get_db
from models import User
from services.project_service import (
    create_project,
    create_task,
    complete_task,
    list_dashboard_projects,
    status_label,
)
from templates import templates


router = APIRouter()


@router.get("/")
def home(request: Request, user: User | None = Depends(get_current_user)):
    """Render the public landing page with authentication-aware navigation."""

    return templates.TemplateResponse("home.html", {"request": request, "user": user})


@router.get("/app")
def dashboard(
    request: Request,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Render projects and related tasks for the logged-in user."""

    projects = list_dashboard_projects(db, user)
    flash = request.session.pop("flash", None)
    return templates.TemplateResponse(
        "app.html",
        {
            "request": request,
            "user": user,
            "projects": projects,
            "status_label": status_label,
            "flash": flash,
        },
    )


@router.post("/app/projects")
def add_project(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Create a project and return to the dashboard."""

    create_project(db, user, name, description)
    request.session["flash"] = "프로젝트를 생성했습니다."
    return RedirectResponse("/app", status_code=303)


@router.post("/app/tasks")
def add_task(
    request: Request,
    project_id: int = Form(...),
    title: str = Form(...),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Create a task under a selected project and return to the dashboard."""

    create_task(db, user, project_id, title)
    request.session["flash"] = "작업을 생성했습니다."
    return RedirectResponse("/app", status_code=303)


@router.post("/app/tasks/{task_id}/complete")
def mark_task_done(
    request: Request,
    task_id: int,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Complete a task and display the before and after states."""

    previous, current = complete_task(db, user, task_id)
    request.session["flash"] = f"{previous} → {current}"
    return RedirectResponse("/app", status_code=303)
