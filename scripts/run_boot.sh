#!/usr/bin/env bash
# run_boot.sh — 부트 사전 조건 검증 스테이지.
#
# (1) 모든 조건 충족 시 6/6 [OK] 후 'Agent READY' 까지 가는 정상 부트,
# (2) 조건 위반 시 해당 단계에서 [FAIL] 후 'System Boot Failed' 로 자동 실패
# 처리되는 모습을 각각 증거로 남긴다. 정상 부트는 곧바로 워크로드로 진입하므로
# 짧게 띄운 뒤 정리한다.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/lib.sh"

OUT="$EVID/boot"
mkdir -p "$OUT"

echo ">>> [BOOT] 정상 부트(6/6 통과) 캡처"
cleanup
setup_env 512 30 false
timeout 6 "$APP" > "$OUT/boot_success.log" 2>&1 || true
cleanup

echo ">>> [BOOT] 실패 케이스 1: MEMORY_LIMIT 범위 위반(40, 허용 50~512)"
cleanup
setup_env 40 30 false
timeout 6 "$APP" > "$OUT/boot_fail_memory_range.log" 2>&1 || true
cleanup

echo ">>> [BOOT] 실패 케이스 2: secret.key 내용 불일치"
cleanup
setup_env 512 30 false
printf 'wrong_key_value' > "$AGENT_KEY_PATH/secret.key"
timeout 6 "$APP" > "$OUT/boot_fail_secretkey.log" 2>&1 || true
# 다음 스테이지를 위해 정상 키 복구
printf 'agent_api_key_test' > "$AGENT_KEY_PATH/secret.key"
cleanup

echo ">>> [BOOT] 실패 케이스 3: AGENT_PORT 고정값(15034) 위반"
cleanup
setup_env 512 30 false
export AGENT_PORT=9999
timeout 6 "$APP" > "$OUT/boot_fail_port.log" 2>&1 || true
export AGENT_PORT=15034
cleanup

echo ">>> [BOOT] 완료. 증거: $OUT/"
