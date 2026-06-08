"""Routes for login and logout."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from database import get_db
from models import User
from services.auth_service import authenticate_user
from templates import templates


router = APIRouter()


@router.get("/login")
def login_page(request: Request, user: User | None = Depends(get_current_user)):
    """Render the login form."""

    return templates.TemplateResponse("login.html", {"request": request, "user": user, "error": None})


@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """Authenticate credentials and store the user id in the session."""

    user = authenticate_user(db, username, password)
    if user is None:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "user": None,
                "error": "아이디 또는 비밀번호가 올바르지 않습니다.",
            },
            status_code=401,
        )
    request.session["user_id"] = user.id
    return RedirectResponse("/app", status_code=303)


@router.post("/logout")
def logout(request: Request):
    """Clear the current session and return to the public home page."""

    request.session.clear()
    return RedirectResponse("/", status_code=303)
