# 표준 라이브러리만 사용하므로 별도 의존성 설치가 없다.
FROM python:3.12-slim

# 한글 입출력을 위해 UTF-8 로 고정한다.
ENV PYTHONUTF8=1 \
    PYTHONIOENCODING=utf-8 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# 소스 전체 복사(외부 패키지 설치 단계 없음).
COPY . /app

# 기본 실행: 전체 기능 시연 + evidence 생성.
# 개별 명령은 다음처럼 덮어쓸 수 있다.
#   docker run --rm <image> python -m budget_app summary --month 2024-01
CMD ["python", "scripts/run_demo.py"]
