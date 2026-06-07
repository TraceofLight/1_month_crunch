#!/usr/bin/env bash
# run_cpu.sh — CPU 과점유 / Watchdog 스테이지.
#
#   before(95): CpuWorker 가 자체 보고 'Current Load' 를 한계(95%)로 끌어올리며,
#               고정 임계치 50% 를 넘는 순간 Watchdog 가 SIGTERM → 종료코드 143.
#   after(30) : Load 가 30% 천장에서 톱니로 진동, 50% 를 못 넘어 종료되지 않음.
# MEMORY_LIMIT 은 512 로 고정해 OOM 이 먼저 끼어드는 것을 막아 CPU 만 격리한다.
# before 런 도중 ps/top 스냅샷을 떠 'app 자체 지표 vs OS 실측'을 대비시킨다.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/lib.sh"

OUT="$EVID/cpu"
mkdir -p "$OUT"
SUM="$OUT/before_after.txt"
: > "$SUM"

echo ">>> [CPU] before 런: CPU_MAX_OCCUPY=95 (Watchdog 종료 관측)"
cleanup
setup_env 512 95 false
t0=$(date +%s)
"$APP" > "$OUT/app_before.log" 2>&1 &
apid=$!
bash "$HERE/monitor.sh" 2 45 "$OUT/monitor_before.log" &
mpid=$!
sleep 15   # 워치독 발동 전(약 30s) 구간에서 OS 실측 스냅샷
snap_cpu > "$OUT/cpu_metrics_before.txt" 2>&1
wait "$apid"; rc_before=$?
t1=$(date +%s)
wait "$mpid" 2>/dev/null || true
cleanup
{
  echo "[before] CPU_MAX_OCCUPY=95  exit_code=${rc_before}  survival=$((t1-t0))s"
  grep -E 'Current Load|Threshold Violated|WATCHDOG|EMERGENCY' "$OUT/app_before.log" | tail -4
  echo
} >> "$SUM"

echo ">>> [CPU] after 런: CPU_MAX_OCCUPY=30 (생존 관측 60s)"
cleanup
setup_env 512 30 false
"$APP" > "$OUT/app_after.log" 2>&1 &
apid=$!
bash "$HERE/monitor.sh" 3 60 "$OUT/monitor_after.log"
alive="GONE"; pgrep -f "$PATTERN" >/dev/null 2>&1 && alive="ALIVE"
cleanup
{
  echo "[after] CPU_MAX_OCCUPY=30  after_60s=${alive} (운영자 정지)"
  echo "Load 최고/최저 표본:"
  grep -oE 'Current Load: [0-9.]+%' "$OUT/app_after.log" | sort -t' ' -k3 -n | sed -n '1p;$p'
  echo "임계 위반 로그 존재? : $(grep -c 'Threshold Violated' "$OUT/app_after.log") 건"
  echo
} >> "$SUM"

echo ">>> [CPU] 완료. 요약: $SUM"
cat "$SUM"
