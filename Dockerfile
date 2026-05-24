FROM python:3.12-slim

# Git 은 런타임에 git status/diff 호출이 필요하므로 함께 설치한다.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py ./
COPY aigitgen/ ./aigitgen/

# 평가자는 호스트 저장소를 /repo 로 bind mount 하고 cwd 를 거기로 두는 것이 기본.
WORKDIR /repo

ENTRYPOINT ["python", "/app/main.py"]
CMD ["--help"]
