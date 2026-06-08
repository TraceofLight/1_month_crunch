"""Memo CRUD routes and page transitions."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.routers.dependencies import get_memo_service
from app.schemas.memo import MemoFormData, MemoView
from app.services.memo_service import MemoService


BASE_DIR = Path(__file__).resolve().parents[2]
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
router = APIRouter(prefix="/memos", tags=["memos"])


def form_context(title: str = "", content: str = "", category: str = "") -> dict[str, str]:
    """Create a dictionary used to refill memo forms after validation errors."""
    return {"title": title, "content": content, "category": category}


def not_found_response(request: Request):
    """Render the missing memo guidance page."""
    return templates.TemplateResponse(
        "memos/not_found.html",
        {"request": request},
        status_code=status.HTTP_404_NOT_FOUND,
    )


@router.get("")
def list_memos(request: Request, q: str | None = None, service: MemoService = Depends(get_memo_service)):
    """Render the memo list page, optionally filtered by a search query."""
    memos = service.list_memos(q)
    return templates.TemplateResponse("memos/list.html", {"request": request, "memos": memos, "q": q or ""})


@router.get("/new")
def new_memo(request: Request):
    """Render the memo creation form."""
    return templates.TemplateResponse(
        "memos/form.html",
        {"request": request, "mode": "create", "form": form_context(), "errors": []},
    )


@router.post("")
def create_memo(
    request: Request,
    title: str = Form(""),
    content: str = Form(""),
    category: str = Form(""),
    service: MemoService = Depends(get_memo_service),
):
    """Create a memo from HTML form fields and redirect to the list page."""
    _, errors = service.create_memo(MemoFormData(title=title, content=content, category=category))
    if errors:
        return templates.TemplateResponse(
            "memos/form.html",
            {"request": request, "mode": "create", "form": form_context(title, content, category), "errors": errors},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return RedirectResponse(request.url_for("list_memos"), status_code=status.HTTP_303_SEE_OTHER)


@router.get("/{memo_id}")
def detail_memo(request: Request, memo_id: int, service: MemoService = Depends(get_memo_service)):
    """Render one memo detail page."""
    memo = service.get_memo(memo_id)
    if memo is None:
        return not_found_response(request)
    return templates.TemplateResponse("memos/detail.html", {"request": request, "memo": memo})


@router.get("/{memo_id}/edit")
def edit_memo(request: Request, memo_id: int, service: MemoService = Depends(get_memo_service)):
    """Render the memo edit form."""
    memo = service.get_memo(memo_id)
    if memo is None:
        return not_found_response(request)
    return templates.TemplateResponse(
        "memos/form.html",
        {"request": request, "mode": "edit", "memo": memo, "form": memo_to_form(memo), "errors": []},
    )


@router.post("/{memo_id}/edit")
def update_memo(
    request: Request,
    memo_id: int,
    title: str = Form(""),
    content: str = Form(""),
    category: str = Form(""),
    service: MemoService = Depends(get_memo_service),
):
    """Update a memo from HTML form fields and redirect to the detail page."""
    memo, errors, exists = service.update_memo(memo_id, MemoFormData(title=title, content=content, category=category))
    if not exists:
        return not_found_response(request)
    if errors:
        return templates.TemplateResponse(
            "memos/form.html",
            {
                "request": request,
                "mode": "edit",
                "memo": memo,
                "form": form_context(title, content, category),
                "errors": errors,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return RedirectResponse(request.url_for("detail_memo", memo_id=memo_id), status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{memo_id}/delete")
def delete_memo(request: Request, memo_id: int, service: MemoService = Depends(get_memo_service)):
    """Delete a memo and redirect to the list page."""
    if not service.delete_memo(memo_id):
        return not_found_response(request)
    return RedirectResponse(request.url_for("list_memos"), status_code=status.HTTP_303_SEE_OTHER)


def memo_to_form(memo: MemoView) -> dict[str, str]:
    """Convert a memo DTO into form values for editing."""
    return form_context(title=memo.title, content=memo.content, category=memo.category)
