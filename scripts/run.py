"""Run the full memo application pipeline and start the web server."""

from __future__ import annotations

import argparse

import uvicorn

from app.database import create_tables


def parse_args() -> argparse.Namespace:
    """Parse command-line options for the development server."""
    parser = argparse.ArgumentParser(description="FastAPI 메모 CRUD 서버 실행")
    parser.add_argument("--host", default="0.0.0.0", help="서버 바인딩 호스트")
    parser.add_argument("--port", default=8000, type=int, help="서버 포트")
    return parser.parse_args()


def main() -> None:
    """Create database tables and start Uvicorn."""
    args = parse_args()
    create_tables()
    uvicorn.run("app.main:app", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
