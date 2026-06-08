"""FastAPI application entry point for the authenticated task service."""

from __future__ import annotations

import os

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from starlette.middleware.sessions import SessionMiddleware

from auth.exceptions import AuthRequiredError, DomainError
from database import init_db
from routers import auth as auth_router
from routers import pages as pages_router
from templates import templates


app = FastAPI(title="프로젝트 작업 관리 서비스")
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "change-this-secret-for-local-development"),
    same_site="lax",
    https_only=False,
)


@app.on_event("startup")
def on_startup() -> None:
    """Create database tables and seed the demo user before serving requests."""

    init_db()


@app.exception_handler(AuthRequiredError)
async def handle_auth_required(request: Request, exc: AuthRequiredError) -> HTMLResponse:
    """Render the login page when a protected page is requested anonymously."""

    return templates.TemplateResponse(
        "login.html",
        {"request": request, "user": None, "error": exc.message},
        status_code=401,
    )


@app.exception_handler(DomainError)
async def handle_domain_error(request: Request, exc: DomainError) -> HTMLResponse:
    """Show domain failures with the same visual layout as normal pages."""

    return templates.TemplateResponse(
        "error.html",
        {"request": request, "user": None, "message": exc.message},
        status_code=400,
    )


app.include_router(auth_router.router)
app.include_router(pages_router.router)
