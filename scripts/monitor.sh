#!/usr/bin/env bash
#
# monitor.sh - 시스템 관제 자동화 스크립트
#
# 배포된 agent 애플리케이션의 헬스 체크(프로세스/포트)와 시스템 자원(CPU/MEM/DISK)을
# 수집하여 콘솔에 출력하고, /var/log/agent-app/monitor.log 에 한 줄로 누적 기록한다.
# agent-admin 계정의 crontab 으로 매분 실행되는 것을 전제로 작성되었다.
#
# 종료 코드:
#   0  - 정상 (임계값 경고가 있어도 0)
#   1  - 헬스 체크 실패 (앱 프로세스 미존재 또는 포트 미LISTEN)
#
# 환경 변수(미지정 시 기본값 사용 → cron 의 최소 환경에서도 동작):
#   AGENT_LOG_DIR     로그 디렉터리           (기본 /var/log/agent-app)
#   AGENT_PORT        앱 LISTEN 포트          (기본 15034)
#   AGENT_APP_NAME    앱 프로세스 매칭 문자열 (기본 agent-app-linux-x86)
#   MONITOR_MAX_SIZE  로그 회전 임계 바이트   (기본 10MB, 테스트용 축소 가능)

set -u

# ----------------------------------------------------------------------------
# 설정값
# ----------------------------------------------------------------------------
AGENT_LOG_DIR="${AGENT_LOG_DIR:-/var/log/agent-app}"
LOG_FILE="$AGENT_LOG_DIR/monitor.log"
APP_PORT="${AGENT_PORT:-15034}"
APP_NAME="${AGENT_APP_NAME:-agent-app-linux-x86}"

# 임계값(초과 시 경고만 출력)
CPU_THRESHOLD=20      # %
MEM_THRESHOLD=10      # %
DISK_THRESHOLD=80     # %

# 로그 용량 관리: 파일 1개 최대 10MB, 최대 10개 파일 유지(현재 파일 + 회전본 9개)
MAX_SIZE="${MONITOR_MAX_SIZE:-$((10 * 1024 * 1024))}"
MAX_FILES=10

# ----------------------------------------------------------------------------
# 헬스 체크 헬퍼
# ----------------------------------------------------------------------------

# 앱 프로세스의 PID 목록을 출력한다(런처/워커가 분리되어 여러 PID 가 나올 수 있음).
app_pids() {
    pgrep -f "$APP_NAME" 2>/dev/null
}

# :APP_PORT 를 LISTEN 하는 소켓이 있으면 0, 없으면 1.
port_is_listening() {
    ss -ltn "sport = :$APP_PORT" 2>/dev/null | grep -q LISTEN
}

# LISTEN 소켓을 소유한 PID(=실제 서비스를 처리하는 워커)를 출력한다.
# ss -p 는 동일 사용자 또는 root 일 때만 PID 를 노출하므로, 실패하면 빈 값.
port_owner_pid() {
    ss -ltnp "sport = :$APP_PORT" 2>/dev/null \
        | grep -o 'pid=[0-9]*' | head -1 | cut -d= -f2
}

# ----------------------------------------------------------------------------
# 자원 수집 헬퍼
# ----------------------------------------------------------------------------

# 시스템 CPU 사용률(%) - /proc/stat 을 1초 간격으로 두 번 샘플링해 delta 로 계산.
# top 의 로캘 의존 출력에 기대지 않아 이식성이 높다.
cpu_usage() {
    local a b
    a=$(grep '^cpu ' /proc/stat)
    sleep 1
    b=$(grep '^cpu ' /proc/stat)
    awk -v a="$a" -v b="$b" '
        BEGIN {
            na = split(a, A, " ");  # A[1]="cpu", A[2..]=user nice system idle iowait irq softirq steal ...
            nb = split(b, B, " ");
            for (i = 2; i <= na; i++) { t1 += A[i]; t2 += B[i]; }
            idle1 = A[5] + A[6]; idle2 = B[5] + B[6];  # idle + iowait
            dt = t2 - t1; di = idle2 - idle1;
            if (dt <= 0) { printf "0.0"; exit }
            printf "%.1f", (dt - di) / dt * 100;
        }'
}

# 시스템 메모리 사용률(%) - MemAvailable 기준(재확보 가능 캐시 제외).
mem_usage() {
    awk '
        /^MemTotal:/     { total = $2 }
        /^MemAvailable:/ { avail = $2 }
        END {
            if (total > 0) printf "%.1f", (total - avail) / total * 100;
            else printf "0.0";
        }' /proc/meminfo
}

# 루트 파티션 디스크 사용률(%) - 정수.
disk_usage() {
    df -P / | awk 'NR==2 { gsub("%", "", $5); print $5 }'
}

# ----------------------------------------------------------------------------
# 방화벽 상태 점검 (경고만, 종료하지 않음)
# ----------------------------------------------------------------------------
# 비root(agent-admin)로 실행되므로 `ufw status`(root 필요)가 막힐 수 있다.
# 그 경우 누구나 읽을 수 있는 /etc/ufw/ufw.conf 의 ENABLED=yes 로 판정한다.
# firewalld 환경도 대비해 firewall-cmd 도 확인한다.
firewall_active() {
    if command -v ufw >/dev/null 2>&1; then
        if ufw status 2>/dev/null | grep -q "Status: active"; then return 0; fi
        if grep -qs '^ENABLED=yes' /etc/ufw/ufw.conf; then return 0; fi
        return 1
    fi
    if command -v firewall-cmd >/dev/null 2>&1; then
        firewall-cmd --state 2>/dev/null | grep -q running && return 0
    fi
    return 1
}

# ----------------------------------------------------------------------------
# 로그 용량 관리 (size 기반 회전: 10MB 초과 시 회전, 최대 10개 파일 유지)
# ----------------------------------------------------------------------------
rotate_log_if_needed() {
    [ -f "$LOG_FILE" ] || return 0
    local size
    size=$(stat -c %s "$LOG_FILE" 2>/dev/null || echo 0)
    [ "$size" -ge "$MAX_SIZE" ] || return 0

    # 가장 오래된 회전본(.9) 제거 후 .8→.9 ... .1→.2, 현재→.1, 현재 파일 비움.
    rm -f "${LOG_FILE}.$((MAX_FILES - 1))"
    local i
    for ((i = MAX_FILES - 2; i >= 1; i--)); do
        [ -f "${LOG_FILE}.$i" ] && mv -f "${LOG_FILE}.$i" "${LOG_FILE}.$((i + 1))"
    done
    mv -f "$LOG_FILE" "${LOG_FILE}.1"
    : > "$LOG_FILE"
}

# ----------------------------------------------------------------------------
# 본문
# ----------------------------------------------------------------------------
echo "====== SYSTEM MONITOR RESULT ======"
echo

# --- [HEALTH CHECK] : 실패 시 즉시 exit 1 ---
echo "[HEALTH CHECK]"

pids=$(app_pids)
if [ -z "$pids" ]; then
    echo "Checking process '$APP_NAME'... [FAIL]"
    echo "[CRITICAL] Application process not found. Aborting."
    exit 1
fi
# 로그에 기록할 대표 PID: LISTEN 소켓 소유자(워커) 우선, 없으면 첫 번째 PID.
pid=$(port_owner_pid)
[ -z "$pid" ] && pid=$(echo "$pids" | head -1)
echo "Checking process '$APP_NAME'... [OK] (PID: $pid)"

if port_is_listening; then
    echo "Checking port $APP_PORT... [OK]"
else
    echo "Checking port $APP_PORT... [FAIL]"
    echo "[CRITICAL] Port $APP_PORT is not in LISTEN state. Aborting."
    exit 1
fi
echo

# --- [STATUS CHECK] : 방화벽은 경고만 ---
echo "[STATUS CHECK]"
if firewall_active; then
    echo "Checking firewall... [OK]"
else
    echo "Checking firewall... [WARNING]"
    echo "[WARNING] Firewall is not active."
fi
echo

# --- [RESOURCE MONITORING] ---
cpu=$(cpu_usage)
mem=$(mem_usage)
disk=$(disk_usage)

echo "[RESOURCE MONITORING]"
echo "CPU Usage  : ${cpu}%"
echo "MEM Usage  : ${mem}%"
echo "DISK Used  : ${disk}%"
echo

# --- 임계값 경고(경고만, 종료하지 않음) ---
# awk 로 부동소수 비교(정수/실수 모두 안전).
if awk -v v="$cpu" -v t="$CPU_THRESHOLD" 'BEGIN{exit !(v>t)}'; then
    echo "[WARNING] CPU threshold exceeded (${cpu}% > ${CPU_THRESHOLD}%)"
fi
if awk -v v="$mem" -v t="$MEM_THRESHOLD" 'BEGIN{exit !(v>t)}'; then
    echo "[WARNING] MEM threshold exceeded (${mem}% > ${MEM_THRESHOLD}%)"
fi
if awk -v v="$disk" -v t="$DISK_THRESHOLD" 'BEGIN{exit !(v>t)}'; then
    echo "[WARNING] DISK threshold exceeded (${disk}% > ${DISK_THRESHOLD}%)"
fi
echo

# --- 로그 기록 ---
mkdir -p "$AGENT_LOG_DIR" 2>/dev/null
rotate_log_if_needed
ts=$(date '+%Y-%m-%d %H:%M:%S')
line="[$ts] PID:$pid CPU:${cpu}% MEM:${mem}% DISK_USED:${disk}%"
if echo "$line" >> "$LOG_FILE" 2>/dev/null; then
    echo "[INFO] Log appended: $LOG_FILE"
else
    echo "[ERROR] Failed to write log: $LOG_FILE" >&2
    exit 1
fi

exit 0
