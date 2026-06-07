#!/usr/bin/env bash
# lib.sh — 공용 헬퍼 모음.
#
# 부트 사전 조건(환경변수/키 파일) 구성, 대상 프로세스 정리, 스레드/CPU 스냅샷
# 등 모든 스테이지 스크립트가 공유하는 함수를 정의한다. 단독 실행용이 아니라
# 다른 스크립트에서 `source` 하여 사용한다.
#
# 핵심 주의점: agent-leak-app-x86 은 PyInstaller 런처/워커 두 프로세스로 갈라지며
# comm 이름이 15자를 넘어 `pgrep -x` 로는 잡히지 않는다. 따라서 전 구간에서
# `pgrep -f agent-leak-app-x86` 으로 전체 PID 를 집계한다.

set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP="$ROOT/agent-leak-app-x86"
EVID="$ROOT/evidence"
PATTERN="agent-leak-app-x86"

# ISO 스타일 타임스탬프(초 단위). 로그 라인 머리말에 사용한다.
ts() { date '+%Y-%m-%d %H:%M:%S'; }

# 부트 사전 조건을 모두 구성한다.
# 인자: $1=MEMORY_LIMIT(MB) $2=CPU_MAX_OCCUPY(%) $3=MULTI_THREAD_ENABLE
# AGENT_HOME 이하 디렉터리와 secret.key 를 만들고, 직전 런의 로그를 비운다.
setup_env() {
  # 로그인 프로파일이 AGENT_HOME 을 쓰기 불가한 경로로 미리 export 해 두는 경우가
  # 있으므로 무조건 전용 작업 디렉터리로 덮어쓴다(AGENT_LAB_HOME 로 변경 가능).
  export AGENT_HOME="${AGENT_LAB_HOME:-/tmp/agent-leak-lab}"
  export AGENT_PORT=15034
  export AGENT_UPLOAD_DIR="$AGENT_HOME/upload_files"
  export AGENT_KEY_PATH="$AGENT_HOME/api_keys"
  export AGENT_LOG_DIR="$AGENT_HOME/logs"
  mkdir -p "$AGENT_UPLOAD_DIR" "$AGENT_KEY_PATH" "$AGENT_LOG_DIR"
  # secret.key 내용은 정확히 'agent_api_key_test' (개행 없이).
  printf 'agent_api_key_test' > "$AGENT_KEY_PATH/secret.key"
  export MEMORY_LIMIT="$1"
  export CPU_MAX_OCCUPY="$2"
  export MULTI_THREAD_ENABLE="$3"
  chmod +x "$APP" 2>/dev/null || true
  : > "$AGENT_LOG_DIR/agent_app.log"   # 런 간 로그 분리
}

# 실행 중인 agent 프로세스를 모두 종료하고 포트가 풀릴 때까지 대기한다.
# 스테이지 사이에 호출하여 15034 바인딩 충돌을 막는다.
cleanup() {
  pkill -9 -f "$PATTERN" 2>/dev/null || true
  for _ in $(seq 1 10); do
    pgrep -f "$PATTERN" >/dev/null 2>&1 || break
    sleep 0.5
  done
  sleep 1
}

# 대상 프로세스의 PID 목록(런처+워커)을 줄바꿈으로 출력한다.
app_pids() { pgrep -f "$PATTERN"; }

# 워커(자식) PID 를 출력한다. 런처가 부모, 워커가 자식이므로
# PPID 가 다른 app PID 중 부모를 제외한 쪽을 고른다. 실패 시 마지막 PID.
worker_pid() {
  local pids parent
  pids=$(app_pids | sort -n | tr '\n' ' ')
  [ -z "${pids// }" ] && return 1
  # app PID 중 부모가 또 다른 app PID 인 것을 워커로 본다.
  for p in $pids; do
    parent=$(ps -o ppid= -p "$p" 2>/dev/null | tr -d ' ')
    if echo "$pids" | tr ' ' '\n' | grep -qx "$parent"; then
      echo "$p"; return 0
    fi
  done
  echo "$pids" | tr ' ' '\n' | tail -1
}

# ps 기반 CPU/MEM/RSS 집계 스냅샷을 표준출력으로 1줄 남긴다(헤더 포함).
# 합산 %CPU, 합산 %MEM, 최대 RSS(MB) — 워커가 메모리를 쥐므로 RSS 는 최댓값.
snap_ps() {
  local pids
  pids=$(app_pids | tr '\n' ',' | sed 's/,$//')
  if [ -z "$pids" ]; then echo "no agent process"; return; fi
  echo "# ps -o pid,ppid,nice,%cpu,%mem,rss,etime,comm (RSS=KB)"
  ps -o pid,ppid,nice,%cpu,%mem,rss,etime,comm -p "$pids"
  ps -o %cpu=,%mem=,rss= -p "$pids" | \
    awk '{c+=$1; m+=$2; if($3>r)r=$3} END{printf "# AGGREGATE  CPU(sum)=%.1f%%  MEM(sum)=%.1f%%  RSS(max)=%.0fMB\n", c, m, r/1024}'
}

# CPU 비교용 스냅샷 3종: (1) ps 누적평균 %cpu (2) top 순간 %cpu (3) top 호스트 요약.
# CPU 스파이크가 'OS 포화'가 아니라 'app 자체 보고 지표'임을 대비시키기 위함.
snap_cpu() {
  local pids
  pids=$(app_pids | tr '\n' ',' | sed 's/,$//')
  if [ -z "$pids" ]; then echo "no agent process"; return; fi
  echo "### (1) ps %cpu = 프로세스 수명 누적 평균"
  ps -o pid,ppid,%cpu,time,nice,comm -p "$pids"
  echo
  echo "### (2) top -b -n2 -d0.3 (2번째 표본 = 직전 0.3초 순간 %CPU)"
  top -b -n2 -d0.3 -p "$pids" 2>/dev/null | awk '/PID +USER/{s++} s>=2{print}'
  echo
  echo "### (3) top -b -n1 헤더 = 호스트 전체 CPU 포화 여부"
  top -b -n1 2>/dev/null | grep -E '^%?Cpu|load average|^top -' | head -3
}

# 스레드/락 스냅샷: PID 생존(ps -ef), 스레드별 상태/대기채널(ps -L), 스레드별 %CPU(top -H).
# 데드락 진단에서 'PID 살아있음 + 스레드 futex 대기 + %CPU 0 + RSS 정지'를 보이기 위함.
snap_threads() {
  local wpid
  echo "### ps -ef | grep [a]gent  (PID 생존 확인)"
  ps -ef | grep '[a]gent-leak-app' || echo "(none)"
  echo
  wpid=$(worker_pid) || { echo "no worker pid"; return; }
  echo "### ps -L -p $wpid (스레드별 상태 STAT / 대기채널 WCHAN / %CPU / RSS)"
  ps -L -o pid,tid,stat,wchan:22,pcpu,rss -p "$wpid"
  echo
  echo "### top -H -b -n1 -p $wpid (스레드별 순간 %CPU)"
  top -H -b -n1 -p "$wpid" 2>/dev/null | awk '/PID +USER/{f=1} f{print}'
}
