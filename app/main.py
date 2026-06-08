"""FastAPI application entry point and router registration."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import create_tables
from app.routers import home, memos


BASE_DIR = Path(__file__).resolve().parents[1]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create SQLite tables when the ASGI application starts."""
    create_tables()
    yield


app = FastAPI(title="메모 관리 CRUD", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.include_router(home.router)
app.include_router(memos.router)
