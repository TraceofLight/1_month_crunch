#!/usr/bin/env bash
# run_oom.sh — 메모리 누수 / OOM 스테이지.
#
# MEMORY_LIMIT 을 바꿔 가며 3회 실행한다.
#   before(128): 권장치 미만 → MemoryWorker 힙이 한계를 넘는 순간 MemoryGuard 가
#                SIGKILL → 셸 종료코드 137.
#   mid(256)   : 권장치 경계 → 더 늦게(한계가 높아 더 오래) 종료. 생존시간이
#                MEMORY_LIMIT 에 비례함을 보이는 중간 점.
#   after(512) : 권장치 → 한계 도달 시 죽지 않고 Cache Flush 로 자가 회복,
#                무한 생존(운영자가 정지).
# 각 런마다 monitor.sh 로 RSS 추이를, 앱 콘솔로 종료/회복 마커를 남긴다.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/lib.sh"

OUT="$EVID/oom"
mkdir -p "$OUT"
SUM="$OUT/before_after.txt"
: > "$SUM"

# 종료형 런: 앱이 스스로 죽을 때까지 관측. 인자: LIMIT TAG MAXSEC
run_dies() {
  local limit="$1" tag="$2" maxsec="$3"
  echo ">>> [OOM] $tag 런: MEMORY_LIMIT=$limit (종료 관측)"
  cleanup
  setup_env "$limit" 30 false
  local t0 t1 rc
  t0=$(date +%s)
  "$APP" > "$OUT/app_${tag}.log" 2>&1 &
  local apid=$!
  bash "$HERE/monitor.sh" 2 "$maxsec" "$OUT/monitor_${tag}.log" &
  local mpid=$!
  wait "$apid"; rc=$?
  t1=$(date +%s)
  wait "$mpid" 2>/dev/null || true
  cleanup
  local peak
  peak=$(grep -oE 'Current Heap: [0-9]+MB' "$OUT/app_${tag}.log" | tail -1)
  {
    echo "[$tag] MEMORY_LIMIT=${limit}MB  exit_code=${rc}  survival=$((t1-t0))s  last_${peak:-NA}"
    grep -E 'MemoryGuard|Self-terminating' "$OUT/app_${tag}.log" | tail -2
    echo
  } >> "$SUM"
}

# 생존형 런: 한계 도달 후에도 죽지 않음. 인자: LIMIT TAG WINDOWSEC
run_survives() {
  local limit="$1" tag="$2" win="$3"
  echo ">>> [OOM] $tag 런: MEMORY_LIMIT=$limit (생존 관측 ${win}s)"
  cleanup
  setup_env "$limit" 30 false
  "$APP" > "$OUT/app_${tag}.log" 2>&1 &
  local apid=$!
  bash "$HERE/monitor.sh" 3 "$win" "$OUT/monitor_${tag}.log"
  local alive="GONE"
  pgrep -f "$PATTERN" >/dev/null 2>&1 && alive="ALIVE"
  cleanup
  {
    echo "[$tag] MEMORY_LIMIT=${limit}MB  after_${win}s=${alive} (운영자 정지, 자가 종료 아님)"
    grep -E 'Reached Limit|Cache Flushed|MEMORY RECOVERED' "$OUT/app_${tag}.log" | head -3
    echo
  } >> "$SUM"
}

run_dies   128 before 30
run_dies   256 mid    45
run_survives 512 after 100

echo ">>> [OOM] 완료. 요약: $SUM"
cat "$SUM"
