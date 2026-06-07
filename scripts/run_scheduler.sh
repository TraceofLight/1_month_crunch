#!/usr/bin/env bash
# run_scheduler.sh — 보너스: 스케줄링 알고리즘 추론용 증거 수집.
#
# 모든 설정이 최적(MEMORY_LIMIT>=256, CPU<50, THREAD=false)이면 'Healthy System
# Monitoring' 시나리오가 선택되며, 부하 워커 전에 Task Scheduler 안정성 테스트가
# 한 번 돈다. 이 [Scheduler]/[Thread-X] 블록을 떠서 실행 순서와 끼어듦 여부를
# 분석한다(런타임 스케줄러 추론용; OS 스케줄러 추론이 아님을 README 에 명시).
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/lib.sh"

OUT="$EVID/scheduler"
mkdir -p "$OUT"

echo ">>> [SCHED] Healthy 런으로 스케줄러 블록 캡처"
cleanup
setup_env 512 30 false
timeout 12 "$APP" > "$OUT/healthy_full.log" 2>&1 || true
cleanup

# 스케줄러 관련 라인만 추출(등록→실행→완료, 각 Thread 진행률 포함).
grep -nE 'Scenario Selected|Scheduler|Thread-[ABC]' "$OUT/healthy_full.log" > "$OUT/scheduler_block.txt" || true

echo ">>> [SCHED] 완료. 블록: $OUT/scheduler_block.txt"
cat "$OUT/scheduler_block.txt"
