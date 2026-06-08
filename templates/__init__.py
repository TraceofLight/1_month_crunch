"""Jinja2 template configuration."""

from __future__ import annotations

from fastapi.templating import Jinja2Templates


templates = Jinja2Templates(directory="templates")
