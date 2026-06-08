"""Start the FastAPI service with database initialization."""

from __future__ import annotations

import sys
from pathlib import Path

import uvicorn

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from database import init_db


def main() -> None:
    """Initialize persistence and run the ASGI server."""

    init_db()
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
