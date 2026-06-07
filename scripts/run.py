"""Mini Redis 전체 파이프라인 실행 진입점."""

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mini_redis.cli import main


if __name__ == "__main__":
    main()
