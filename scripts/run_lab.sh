#!/usr/bin/env bash
#
# run_lab.sh - 관제 자동화 실습 단일 엔트리포인트
#
# 이미지 빌드 → 컨테이너 기동 → 환경 구성(setup_lab.sh) → 앱 부팅 →
# monitor.sh 실행 → cron 등록/자동 누적 확인 → report.sh / rotate_logs.sh 시연까지
# 전 과정을 한 번에 수행하고, 모든 검증 산출물을 evidence/lab/ 에 저장한다.
#
# 사용법:  bash scripts/run_lab.sh
# 요구사항: Docker, 그리고 UFW 활성화를 위한 NET_ADMIN/NET_RAW capability.
#
set -uo pipefail

cd "$(dirname "$0")/.."        # 저장소 루트
IMAGE=agent-lab
NAME=agent-lab-run
EVID=evidence/lab
AGENT_HOME=/home/agent-admin/agent-app
APP=/home/agent-admin/agent-app/bin
mkdir -p "$EVID"

# 헤더와 함께 컨테이너 명령을 실행하고 콘솔+파일에 동시에 남기는 헬퍼.
cap() {  # cap <evidence-file> <title> -- <docker exec args...>
    local file="$1" title="$2"; shift 2
    [ "$1" = "--" ] && shift
    {
        echo "==================================================================="
        echo "# $title"
        echo "# \$ $*"
        echo "==================================================================="
        "$@"
        echo
    } 2>&1 | tee -a "$file"
}

echo ">>> [build] docker image: $IMAGE"
docker build -t "$IMAGE" . || { echo "build failed"; exit 1; }

echo ">>> [run] container: $NAME"
docker rm -f "$NAME" >/dev/null 2>&1 || true
docker run -d --name "$NAME" --hostname agent-lab \
    --cap-add NET_ADMIN --cap-add NET_RAW "$IMAGE" >/dev/null

# --- 환경 구성 ----------------------------------------------------------------
: > "$EVID/01_setup.txt"
cap "$EVID/01_setup.txt" "setup_lab.sh (전체 환경 구성)" -- \
    docker exec "$NAME" bash /opt/agent/scripts/setup_lab.sh

# --- 증거 1: SSH 포트 / Root 차단 ---------------------------------------------
: > "$EVID/02_ssh.txt"
cap "$EVID/02_ssh.txt" "sshd_config 핵심 설정" -- \
    docker exec "$NAME" grep -E '^(Port|PermitRootLogin)' /etc/ssh/sshd_config
cap "$EVID/02_ssh.txt" "sshd LISTEN 상태(ss)" -- \
    docker exec "$NAME" bash -c "ss -tulnp | grep sshd"

# --- 증거 2: 방화벽 -----------------------------------------------------------
: > "$EVID/03_firewall.txt"
cap "$EVID/03_firewall.txt" "ufw status verbose" -- \
    docker exec "$NAME" ufw status verbose

# --- 증거 3: 계정 / 그룹 ------------------------------------------------------
: > "$EVID/04_accounts.txt"
cap "$EVID/04_accounts.txt" "id agent-admin / agent-dev / agent-test" -- \
    docker exec "$NAME" bash -c "id agent-admin; id agent-dev; id agent-test"
cap "$EVID/04_accounts.txt" "그룹 멤버십(getent)" -- \
    docker exec "$NAME" bash -c "getent group agent-common; getent group agent-core"

# --- 증거 4: 디렉터리 구조 / 권한 / ACL ---------------------------------------
: > "$EVID/05_directories.txt"
cap "$EVID/05_directories.txt" "디렉터리 트리/권한" -- \
    docker exec "$NAME" bash -c "ls -ld $AGENT_HOME $AGENT_HOME/upload_files $AGENT_HOME/api_keys $AGENT_HOME/bin /var/log/agent-app; echo; ls -l $AGENT_HOME/bin"
cap "$EVID/05_directories.txt" "getfacl upload_files (공유)" -- \
    docker exec "$NAME" getfacl "$AGENT_HOME/upload_files"
cap "$EVID/05_directories.txt" "getfacl api_keys (보안)" -- \
    docker exec "$NAME" getfacl "$AGENT_HOME/api_keys"
cap "$EVID/05_directories.txt" "getfacl /var/log/agent-app (보안)" -- \
    docker exec "$NAME" getfacl /var/log/agent-app

# --- 증거 4b: 접근 통제 실증(공유 vs 보안 분리) -------------------------------
: > "$EVID/05b_access_control.txt"
cap "$EVID/05b_access_control.txt" "agent-test(common,비core): upload_files 쓰기 시도" -- \
    docker exec -u agent-test "$NAME" bash -c \
    "echo hello > $AGENT_HOME/upload_files/by_test.txt && echo 'RESULT: write OK (expected)'"
cap "$EVID/05b_access_control.txt" "agent-test(비core): api_keys/secret.key 읽기 시도(차단되어야 함)" -- \
    docker exec -u agent-test "$NAME" bash -c \
    "cat $AGENT_HOME/api_keys/secret.key 2>&1; echo \"RESULT exit=\$? (Permission denied 기대)\""
cap "$EVID/05b_access_control.txt" "agent-dev(core): api_keys/secret.key 읽기(허용되어야 함)" -- \
    docker exec -u agent-dev "$NAME" bash -c \
    "cat $AGENT_HOME/api_keys/secret.key && echo ' <- read OK (expected)'"

# --- 증거 5: 앱 Boot Sequence (일반 계정 agent-admin) -------------------------
echo ">>> [app] boot agent-app as agent-admin"
docker exec -u agent-admin -d "$NAME" bash -lc \
    "source $AGENT_HOME/agent.env; cd \$AGENT_HOME; exec ./agent-app-linux-x86 > /var/log/agent-app/app.boot.log 2>&1"
sleep 9
: > "$EVID/06_boot_sequence.txt"
cap "$EVID/06_boot_sequence.txt" "Boot Sequence 5단계 + Agent READY" -- \
    docker exec "$NAME" bash -c "sed -n '1,18p' /var/log/agent-app/app.boot.log"
cap "$EVID/06_boot_sequence.txt" "0.0.0.0:15034 LISTEN 확인" -- \
    docker exec "$NAME" bash -c "ss -tlnp 'sport = :15034'"

# --- 증거 6: monitor.sh 콘솔 실행 결과 ----------------------------------------
: > "$EVID/07_monitor_console.txt"
cap "$EVID/07_monitor_console.txt" "monitor.sh (agent-admin 실행)" -- \
    docker exec -u agent-admin "$NAME" "$APP/monitor.sh"

# --- 증거 7: monitor.log 누적 -------------------------------------------------
: > "$EVID/08_monitor_log.txt"
cap "$EVID/08_monitor_log.txt" "monitor.log 최근 라인(수동 실행 직후)" -- \
    docker exec "$NAME" bash -c "tail -n 5 /var/log/agent-app/monitor.log; echo '---'; wc -l /var/log/agent-app/monitor.log"

# --- 증거 8: cron 매분 등록 + 자동 누적 ---------------------------------------
echo ">>> [cron] register agent-admin crontab (every minute)"
docker exec "$NAME" bash -c \
    "echo '* * * * * $APP/monitor.sh >/dev/null 2>&1' | crontab -u agent-admin -"
: > "$EVID/09_cron.txt"
cap "$EVID/09_cron.txt" "agent-admin crontab -l" -- \
    docker exec "$NAME" crontab -u agent-admin -l
before=$(docker exec "$NAME" bash -c "wc -l < /var/log/agent-app/monitor.log")
echo "    monitor.log lines before wait: $before  (cron 자동 실행 대기 ~80s ...)"
sleep 80
after=$(docker exec "$NAME" bash -c "wc -l < /var/log/agent-app/monitor.log")
cap "$EVID/09_cron.txt" "cron 자동 누적 확인 (대기 전/후 라인 수 + 최근 라인)" -- \
    docker exec "$NAME" bash -c \
    "echo 'lines before=$before  after='\$(wc -l < /var/log/agent-app/monitor.log); echo '--- last 6 lines ---'; tail -n 6 /var/log/agent-app/monitor.log"

# --- 보너스 1: report.sh ------------------------------------------------------
: > "$EVID/10_report.txt"
cap "$EVID/10_report.txt" "report.sh (전체 구간 통계)" -- \
    docker exec -u agent-admin "$NAME" "$APP/report.sh"

# --- 보너스 2-a: size 기반 회전(별도 로그 디렉터리로 시연) --------------------
: > "$EVID/11_rotate.txt"
cap "$EVID/11_rotate.txt" "size 기반 회전: MONITOR_MAX_SIZE=100 으로 5회 실행" -- \
    docker exec -u agent-admin -e AGENT_LOG_DIR=/tmp/rotdemo -e MONITOR_MAX_SIZE=100 "$NAME" \
    bash -c "for i in 1 2 3 4 5; do $APP/monitor.sh >/dev/null; done; echo '--- /tmp/rotdemo ---'; ls -l /tmp/rotdemo/"

# --- 보너스 2-b: 시간 기반 보존 정책(7일 압축/이동, 30일 삭제) ----------------
docker exec "$NAME" bash -c '
  echo old8 > /var/log/agent-app/old8.log;  touch -d "8 days ago"  /var/log/agent-app/old8.log
  echo old3 > /var/log/agent-app/old3.log;  touch -d "3 days ago"  /var/log/agent-app/old3.log
  mkdir -p /var/log/monitor/agent-app/archive
  echo z | gzip > /var/log/monitor/agent-app/archive/old31.gz; touch -d "31 days ago" /var/log/monitor/agent-app/archive/old31.gz
  echo z | gzip > /var/log/monitor/agent-app/archive/old5.gz;  touch -d "5 days ago"  /var/log/monitor/agent-app/archive/old5.gz
'
cap "$EVID/11_rotate.txt" "시간 기반 보존: 실행 전 상태" -- \
    docker exec "$NAME" bash -c "echo '[src *.log]'; ls -l /var/log/agent-app/*.log; echo '[archive]'; ls -l /var/log/monitor/agent-app/archive/"
cap "$EVID/11_rotate.txt" "rotate_logs.sh 실행" -- \
    docker exec "$NAME" /home/agent-admin/agent-app/bin/rotate_logs.sh
cap "$EVID/11_rotate.txt" "시간 기반 보존: 실행 후 상태(old8→압축/아카이브, old31.gz 삭제, old3/old5 유지)" -- \
    docker exec "$NAME" bash -c "echo '[src *.log]'; ls -l /var/log/agent-app/*.log 2>&1; echo '[archive]'; ls -l /var/log/monitor/agent-app/archive/"

echo
echo ">>> DONE. 컨테이너 '$NAME' 는 점검을 위해 유지됩니다."
echo ">>> 정리:  docker rm -f $NAME"
