#!/usr/bin/env bash
# monitor.sh — agent-leak-app 관제 스크립트.
#
# 대상 프로세스를 INTERVAL 초마다 최대 DURATION 초 동안 표본하여
# 합산 %CPU, 합산 %MEM, 최대 RSS(MB) 를 한 줄씩 기록한다. 미션 예시와 동일한
# "[시각] PROCESS:... CPU:..% MEM:..% RSS:..MB DISK:.. FIREWALL:.." 포맷이다.
#
# PyInstaller 런처/워커가 같은 이름(comm 15자 초과)으로 갈라지므로 `pgrep -f`
# 로 전체 PID 를 잡아 ps 로 집계한다. 단순 첫 PID 만 보면 런처(RSS ~2MB)만
# 잡혀 사용량이 0 으로 보인다.
#
# 사용법: monitor.sh [INTERVAL_SEC] [DURATION_SEC] [OUTFILE]
#   INTERVAL  표본 주기(초)    기본 3
#   DURATION  최대 관측(초)    기본 60
#   OUTFILE   기록 파일        기본 표준출력만

set -u
PATTERN="agent-leak-app-x86"
INTERVAL="${1:-3}"
DURATION="${2:-60}"
OUT="${3:-}"

emit() {
  echo "$1"
  [ -n "$OUT" ] && echo "$1" >> "$OUT"
}

[ -n "$OUT" ] && : > "$OUT"

start=$(date +%s)
end=$(( start + DURATION ))

while [ "$(date +%s)" -le "$end" ]; do
  now="$(date '+%Y-%m-%d %H:%M:%S')"
  pids=$(pgrep -f "$PATTERN" | tr '\n' ',' | sed 's/,$//')
  if [ -z "$pids" ]; then
    emit "[$now] PROCESS:agent-leak-app STATUS:NOT_RUNNING (프로세스 종료 감지)"
    break
  fi
  # 합산 %CPU/%MEM, 최대 RSS(KB→MB). 런처+워커 전체를 더한다.
  read cpu mem rss <<EOF
$(ps -o %cpu=,%mem=,rss= -p "$pids" 2>/dev/null | awk '{c+=$1; m+=$2; if($3>r)r=$3} END{printf "%.1f %.1f %.0f", c, m, r/1024}')
EOF
  disk=$(df -h / | awk 'NR==2{print $4}')
  if command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -qi '^Status: active'; then
    fw=active
  else
    fw=inactive
  fi
  emit "[$now] PROCESS:agent-leak-app CPU:${cpu}% MEM:${mem}% RSS:${rss}MB DISK:${disk} FIREWALL:${fw}"
  sleep "$INTERVAL"
done
