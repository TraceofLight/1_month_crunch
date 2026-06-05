#!/usr/bin/env bash
#
# report.sh - monitor.log 요약 리포트 생성 (보너스 1)
#
# monitor.log 를 분석해 CPU/MEM/DISK 의 평균/최대/최소와 샘플 수를 콘솔에 출력한다.
# 선택적으로 시작/종료 시각을 받아 해당 구간의 로그만 분석한다.
#
# 사용법:
#   report.sh                                   전체 로그 분석
#   report.sh "2026-06-05 15:00:00" "2026-06-05 16:00:00"   구간 분석
#
# 로그 한 줄 형식(monitor.sh 가 기록):
#   [YYYY-MM-DD HH:MM:SS] PID:<pid> CPU:<f>% MEM:<f>% DISK_USED:<i>%

set -u

AGENT_LOG_DIR="${AGENT_LOG_DIR:-/var/log/agent-app}"
LOG_FILE="${1:-}"
# 첫 인자가 시각 형태이면 로그 경로가 아니라 START 로 취급.
if [ -n "$LOG_FILE" ] && printf '%s' "$LOG_FILE" | grep -q '^[0-9][0-9][0-9][0-9]-'; then
    LOG_FILE=""
fi
LOG_FILE="${LOG_FILE:-$AGENT_LOG_DIR/monitor.log}"

# START/END 인자 파싱: 로그 경로를 명시하지 않은 일반적 호출에서는 $1,$2 가 구간.
START=""
END=""
if printf '%s' "${1:-}" | grep -q '^[0-9][0-9][0-9][0-9]-'; then
    START="${1:-}"
    END="${2:-}"
else
    START="${2:-}"
    END="${3:-}"
fi

if [ ! -f "$LOG_FILE" ]; then
    echo "[ERROR] Log file not found: $LOG_FILE" >&2
    exit 1
fi

# mawk 호환: {n} 구간 수량자와 3-인자 match() 를 쓰지 않고 split/gsub 만 사용.
awk -v start="$START" -v end="$END" '
    # "[2026-06-05 15:58:01] PID:.. CPU:..% MEM:..% DISK_USED:..%"
    {
        ts = $1 " " $2;
        gsub(/[\[\]]/, "", ts);              # 대괄호 제거 → "2026-06-05 15:58:01"
        if (start != "" && ts < start) next; # 문자열 비교(ISO 형식이라 사전식=시간순)
        if (end   != "" && ts > end)   next;

        cpu = $4; gsub(/[^0-9.]/, "", cpu);
        mem = $5; gsub(/[^0-9.]/, "", mem);
        dsk = $6; gsub(/[^0-9.]/, "", dsk);
        if (cpu == "" && mem == "" && dsk == "") next;

        n++;
        acc_cpu += cpu; acc_mem += mem; acc_dsk += dsk;

        if (n == 1 || cpu > max_cpu) { max_cpu = cpu; max_cpu_t = ts }
        if (n == 1 || cpu < min_cpu) { min_cpu = cpu; min_cpu_t = ts }
        if (n == 1 || mem > max_mem) { max_mem = mem; max_mem_t = ts }
        if (n == 1 || mem < min_mem) { min_mem = mem; min_mem_t = ts }
        if (n == 1 || dsk > max_dsk) { max_dsk = dsk; max_dsk_t = ts }
        if (n == 1 || dsk < min_dsk) { min_dsk = dsk; min_dsk_t = ts }
    }
    END {
        print "====== STATISTICS REPORT ======";
        if (n == 0) {
            print "  No samples in the given range.";
            exit 0;
        }
        printf "  [CPU]\n";
        printf "    Average : %.1f%%\n", acc_cpu / n;
        printf "    Maximum : %.1f%% at %s\n", max_cpu, max_cpu_t;
        printf "    Minimum : %.1f%% at %s\n", min_cpu, min_cpu_t;
        printf "  [Memory]\n";
        printf "    Average : %.1f%%\n", acc_mem / n;
        printf "    Maximum : %.1f%% at %s\n", max_mem, max_mem_t;
        printf "    Minimum : %.1f%% at %s\n", min_mem, min_mem_t;
        printf "  [Disk]\n";
        printf "    Average : %.1f%%\n", acc_dsk / n;
        printf "    Maximum : %.0f%% at %s\n", max_dsk, max_dsk_t;
        printf "    Minimum : %.0f%% at %s\n", min_dsk, min_dsk_t;
        printf "  [Samples]\n";
        printf "    Data Points: %d samples\n", n;
    }
' "$LOG_FILE"
