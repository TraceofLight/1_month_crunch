#!/usr/bin/env bash
# run_deadlock.sh — 교착상태(Deadlock) 스테이지.
#
#   before(MULTI_THREAD_ENABLE=true): 워커 스레드들이 서로의 락(Shared_Memory_A /
#       Socket_Pool_B)을 순환 대기 → 프로세스는 살아있으나 무응답. 종료 신호 없음.
#   after(MULTI_THREAD_ENABLE=false): 동시성 비활성 → 정상 워크로드 진행(응답).
# 'PID 생존 + 스레드 futex 대기 + %CPU 0 + RSS 정지 + 로그 멈춤' 을 두 시점에서
# 떠서, 느린 진행이 아니라 완전한 정지(=교착)임을 증명한다.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/lib.sh"

OUT="$EVID/deadlock"
mkdir -p "$OUT"
SUM="$OUT/before_after.txt"
: > "$SUM"

echo ">>> [DEADLOCK] before 런: MULTI_THREAD_ENABLE=true"
cleanup
setup_env 512 30 true
"$APP" > "$OUT/app_before.log" 2>&1 &
apid=$!
bash "$HERE/monitor.sh" 2 40 "$OUT/monitor_before.log" &
mpid=$!

sleep 16
echo "--- [DEADLOCK] T1 스냅샷 (t≈16s) ---"
{ echo "===== T1 (t≈16s) ====="; snap_threads; } > "$OUT/snapshot_t1.txt" 2>&1
tail -8 "$OUT/app_before.log" > "$OUT/applog_tail_t1.txt"

sleep 12
echo "--- [DEADLOCK] T2 스냅샷 (t≈28s) ---"
{ echo "===== T2 (t≈28s) ====="; snap_threads; } > "$OUT/snapshot_t2.txt" 2>&1
tail -8 "$OUT/app_before.log" > "$OUT/applog_tail_t2.txt"

# 두 시점 비교: PID 생존 / 로그·RSS 정지 여부
alive="GONE"; pgrep -f "$PATTERN" >/dev/null 2>&1 && alive="ALIVE"
wait "$mpid" 2>/dev/null || true
{
  echo "[before] MULTI_THREAD_ENABLE=true  process_after_28s=${alive} (자가 종료 없음)"
  echo "T1 마지막 로그 == T2 마지막 로그 ? : $(diff -q "$OUT/applog_tail_t1.txt" "$OUT/applog_tail_t2.txt" >/dev/null 2>&1 && echo SAME_그대로멈춤 || echo DIFFERENT)"
  echo "마지막 로그 지점:"
  tail -3 "$OUT/app_before.log"
  echo
} >> "$SUM"
cleanup

echo ">>> [DEADLOCK] after 런: MULTI_THREAD_ENABLE=false (응답성 확인 15s)"
cleanup
setup_env 512 30 false
"$APP" > "$OUT/app_after.log" 2>&1 &
apid=$!
bash "$HERE/monitor.sh" 2 15 "$OUT/monitor_after.log"
echo "--- [DEADLOCK] after 스냅샷 ---"
{ echo "===== AFTER (THREAD=false) ====="; snap_threads; } > "$OUT/snapshot_after.txt" 2>&1
{
  echo "[after] MULTI_THREAD_ENABLE=false  로그 라인 수=$(grep -c 'INFO' "$OUT/app_after.log") (계속 진행 = 응답)"
  echo "마지막 진행 로그:"
  tail -3 "$OUT/app_after.log"
  echo
} >> "$SUM"
cleanup

echo ">>> [DEADLOCK] 완료. 요약: $SUM"
cat "$SUM"
