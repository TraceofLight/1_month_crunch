#!/usr/bin/env bash
#
# rotate_logs.sh - 시간 기반 로그 보존 정책 (보너스 2)
#
# 1) /var/log/agent-app/*.log 중 7일 이상 경과 파일을 gzip 압축
# 2) 압축본(.gz)을 /var/log/monitor/agent-app/archive/ 로 이동
# 3) 아카이브 중 30일 이상 경과한 *.gz 삭제
#
# 디렉터리 미존재, 권한 부족, 대상 0개 등에서 "안전하게 종료/경고"한다(exit 0).
#
# 환경 변수(테스트용 재지정 가능):
#   SRC_DIR        원본 로그 디렉터리   (기본 /var/log/agent-app)
#   ARCHIVE_DIR    아카이브 디렉터리    (기본 /var/log/monitor/agent-app/archive)
#   COMPRESS_DAYS  압축 대상 경과일     (기본 7)
#   DELETE_DAYS    삭제 대상 경과일     (기본 30)

set -u

SRC_DIR="${SRC_DIR:-/var/log/agent-app}"
ARCHIVE_DIR="${ARCHIVE_DIR:-/var/log/monitor/agent-app/archive}"
COMPRESS_DAYS="${COMPRESS_DAYS:-7}"
DELETE_DAYS="${DELETE_DAYS:-30}"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# --- 사전 점검: 원본 디렉터리 ---
if [ ! -d "$SRC_DIR" ]; then
    log "[WARN] Source directory not found: $SRC_DIR (nothing to do)"
    exit 0
fi

# --- 아카이브 디렉터리 보장 ---
if [ ! -d "$ARCHIVE_DIR" ]; then
    if ! mkdir -p "$ARCHIVE_DIR" 2>/dev/null; then
        log "[WARN] Cannot create archive directory: $ARCHIVE_DIR (permission?) - skipping archive step"
    fi
fi

# --- 1) 7일 경과 *.log 압축 + 2) 아카이브 이동 ---
compressed=0
# 활성 파일에 대한 부분 압축을 피하기 위해 -mtime 으로 7일 이상 경과분만 대상.
while IFS= read -r -d '' f; do
    if [ ! -w "$f" ]; then
        log "[WARN] No write permission, skip: $f"
        continue
    fi
    if gzip -f "$f" 2>/dev/null; then
        gz="${f}.gz"
        if [ -d "$ARCHIVE_DIR" ] && [ -w "$ARCHIVE_DIR" ]; then
            if mv -f "$gz" "$ARCHIVE_DIR/" 2>/dev/null; then
                log "[INFO] Archived: $(basename "$gz") -> $ARCHIVE_DIR/"
                compressed=$((compressed + 1))
            else
                log "[WARN] Compressed but move failed (kept in place): $gz"
            fi
        else
            log "[WARN] Archive dir not writable; compressed in place: $gz"
        fi
    else
        log "[WARN] gzip failed: $f"
    fi
done < <(find "$SRC_DIR" -maxdepth 1 -type f -name '*.log' -mtime "+$COMPRESS_DAYS" -print0 2>/dev/null)

if [ "$compressed" -eq 0 ]; then
    log "[INFO] No log files older than ${COMPRESS_DAYS} days to compress."
fi

# --- 3) 30일 경과 아카이브 삭제 ---
deleted=0
if [ -d "$ARCHIVE_DIR" ]; then
    while IFS= read -r -d '' g; do
        if rm -f "$g" 2>/dev/null; then
            log "[INFO] Deleted old archive: $(basename "$g")"
            deleted=$((deleted + 1))
        else
            log "[WARN] Failed to delete: $g"
        fi
    done < <(find "$ARCHIVE_DIR" -maxdepth 1 -type f -name '*.gz' -mtime "+$DELETE_DAYS" -print0 2>/dev/null)
fi
if [ "$deleted" -eq 0 ]; then
    log "[INFO] No archives older than ${DELETE_DAYS} days to delete."
fi

log "[DONE] compressed=$compressed deleted=$deleted"
exit 0
