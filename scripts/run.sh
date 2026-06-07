#!/usr/bin/env bash
# run.sh — 단일 진입점. 전체 트러블슈팅 파이프라인을 한 번에 재현한다.
#
# 사용법:
#   bash scripts/run.sh all        # 부트→OOM→CPU→Deadlock→Scheduler→Charts (기본)
#   bash scripts/run.sh boot       # 부트 사전조건 검증만
#   bash scripts/run.sh oom        # 메모리 누수/OOM 만
#   bash scripts/run.sh cpu        # CPU 과점유 만
#   bash scripts/run.sh deadlock   # 교착상태 만
#   bash scripts/run.sh scheduler  # 보너스: 스케줄러 블록 캡처
#   bash scripts/run.sh charts     # 수집된 로그로 PNG 차트만 생성
#
# 모든 증거가 한 번의 실행에서 같은 타임라인으로 나오도록 'all' 사용을 권장한다.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAGE="${1:-all}"

run_charts() {
  echo ">>> [CHARTS] PNG 차트 생성"
  python3 "$HERE/make_charts.py"
}

case "$STAGE" in
  boot)      bash "$HERE/run_boot.sh" ;;
  oom)       bash "$HERE/run_oom.sh" ;;
  cpu)       bash "$HERE/run_cpu.sh" ;;
  deadlock)  bash "$HERE/run_deadlock.sh" ;;
  scheduler) bash "$HERE/run_scheduler.sh" ;;
  charts)    run_charts ;;
  all)
    bash "$HERE/run_boot.sh"
    bash "$HERE/run_oom.sh"
    bash "$HERE/run_cpu.sh"
    bash "$HERE/run_deadlock.sh"
    bash "$HERE/run_scheduler.sh"
    run_charts
    echo ">>> [ALL] 전체 파이프라인 완료. evidence/ 확인."
    ;;
  *)
    echo "unknown stage: $STAGE" >&2
    echo "use: all|boot|oom|cpu|deadlock|scheduler|charts" >&2
    exit 2
    ;;
esac
