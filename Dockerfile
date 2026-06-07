# agent-leak-app 트러블슈팅 실습용 컨테이너.
#
# 평가자가 로컬 OS/패키지 상태에 의존하지 않고 동일하게 재현할 수 있도록
# 분석 환경(리눅스 + procps + matplotlib)과 바이너리, 스크립트를 함께 담는다.
# 부트 사전 조건상 root 가 아닌 일반 사용자로 실행해야 하므로 비루트 계정을 만든다.
#
# 빌드:  docker build -t agent-leak-lab .
# 실행:  docker run --rm agent-leak-lab boot     # 또는 oom|cpu|deadlock|scheduler
#        docker run --rm agent-leak-lab all      # 전체 파이프라인
FROM ubuntu:24.04

# 재현성: 분석 도구를 명시적으로 설치(ps/top/pgrep=procps, 차트=matplotlib).
RUN apt-get update && apt-get install -y --no-install-recommends \
        procps \
        python3 \
        python3-matplotlib \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 비루트 실행 계정(부트 1단계 [Checking User Account] 통과 조건).
RUN useradd -m -u 1001 -s /bin/bash agent
USER agent
WORKDIR /home/agent/lab

# 바이너리와 스크립트 반입(소유권을 실행 계정으로).
COPY --chown=agent:agent agent-leak-app-x86 ./agent-leak-app-x86
COPY --chown=agent:agent scripts ./scripts

# 컨테이너 내부 작업 디렉터리(쓰기 가능)로 AGENT_HOME 고정.
ENV AGENT_LAB_HOME=/home/agent/lab/agent-home

ENTRYPOINT ["bash", "scripts/run.sh"]
CMD ["all"]
