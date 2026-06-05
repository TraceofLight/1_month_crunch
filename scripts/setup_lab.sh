#!/usr/bin/env bash
#
# setup_lab.sh - 관제 실습 환경 일괄 구성 (컨테이너 내부, root 로 실행)
#
# 요구사항 §1~§4 의 "한 번만 수행하는 설정"을 멱등적으로 구성한다:
#   - SSH 포트 20022 / Root 원격 로그인 차단
#   - UFW 활성화, 20022·15034/tcp 만 허용
#   - 계정/그룹(agent-admin/dev/test, agent-common/core)
#   - 디렉터리 구조 + 소유/권한 + ACL(공유 vs 보안 분리)
#   - 환경 변수 파일, API 키 파일
#   - 앱 바이너리 및 monitor.sh/report.sh/rotate_logs.sh 배치
#   - sshd / cron 데몬 기동(컨테이너에 systemd 가 없으므로 수동 기동)
#
# 입력 파일은 이미지 빌드 시 /opt/agent 에 복사되어 있다고 가정한다.

set -euo pipefail

SRC=/opt/agent
AGENT_HOME=/home/agent-admin/agent-app
LOG_DIR=/var/log/agent-app

echo "############ [setup_lab] START ############"

# ---------------------------------------------------------------------------
# 1. SSH: 포트 20022, Root 원격 로그인 차단
# ---------------------------------------------------------------------------
echo "## [1] SSH hardening"
sed -i -E 's/^#?Port .*/Port 20022/' /etc/ssh/sshd_config
grep -q '^Port 20022' /etc/ssh/sshd_config || echo 'Port 20022' >> /etc/ssh/sshd_config
sed -i -E 's/^#?PermitRootLogin .*/PermitRootLogin no/' /etc/ssh/sshd_config
grep -q '^PermitRootLogin no' /etc/ssh/sshd_config || echo 'PermitRootLogin no' >> /etc/ssh/sshd_config
ssh-keygen -A >/dev/null 2>&1
mkdir -p /run/sshd
pgrep -x sshd >/dev/null 2>&1 || /usr/sbin/sshd
echo "   sshd configured & started on port 20022"

# ---------------------------------------------------------------------------
# 2. 계정 / 그룹 (최소 권한 협업 체계)
# ---------------------------------------------------------------------------
echo "## [2] Accounts & groups"
getent group agent-common >/dev/null || groupadd agent-common
getent group agent-core   >/dev/null || groupadd agent-core
for u in agent-admin agent-dev agent-test; do
    id "$u" >/dev/null 2>&1 || useradd -m -s /bin/bash "$u"
done
# agent-common: admin, dev, test  /  agent-core: admin, dev
usermod -aG agent-common,agent-core agent-admin
usermod -aG agent-common,agent-core agent-dev
usermod -aG agent-common            agent-test
echo "   users: agent-admin/dev/test, groups: agent-common(admin,dev,test) agent-core(admin,dev)"

# ---------------------------------------------------------------------------
# 3. 디렉터리 구조 + 소유/권한 + ACL
# ---------------------------------------------------------------------------
echo "## [3] Directories, permissions, ACL"
install -d -o agent-admin -g agent-common -m 0750 "$AGENT_HOME"
install -d -o agent-admin -g agent-core   -m 0750 "$AGENT_HOME/bin"
install -d -o agent-admin -g agent-common -m 2770 "$AGENT_HOME/upload_files"
install -d -o agent-admin -g agent-core   -m 2770 "$AGENT_HOME/api_keys"
install -d -o agent-admin -g agent-core   -m 2770 "$LOG_DIR"

# useradd -m 이 만든 /home/agent-admin 은 0700 이라 agent-common 멤버가 진입(traverse) 불가.
# 공유 디렉터리 정책이 성립하려면 홈과 AGENT_HOME 의 "실행(x)" 권한이 필요하다.
setfacl -m g:agent-common:x /home/agent-admin
setfacl -m g:agent-common:x "$AGENT_HOME"

# upload_files: agent-common 그룹 R/W (공유). 신규 파일도 그룹 권한 상속(default ACL).
setfacl    -m g:agent-common:rwx "$AGENT_HOME/upload_files"
setfacl -d -m g:agent-common:rwx "$AGENT_HOME/upload_files"

# api_keys / 로그: agent-core 그룹만 R/W (보안). others 는 완전 차단.
setfacl    -m g:agent-core:rwx "$AGENT_HOME/api_keys"
setfacl -d -m g:agent-core:rwx "$AGENT_HOME/api_keys"
setfacl    -m o::0             "$AGENT_HOME/api_keys"
setfacl    -m g:agent-core:rwx "$LOG_DIR"
setfacl -d -m g:agent-core:rwx "$LOG_DIR"
setfacl    -m o::0             "$LOG_DIR"
echo "   ACL applied (upload_files=common rwx, api_keys/log=core only)"

# ---------------------------------------------------------------------------
# 4. API 키 파일 + 환경 변수 파일
# ---------------------------------------------------------------------------
echo "## [4] Key file & environment"
# 제공 바이너리는 AGENT_KEY_PATH 를 '디렉터리'로 받고 그 안의 secret.key 를 검증한다.
printf 'agent_api_key_test' > "$AGENT_HOME/api_keys/secret.key"
# 요구사항 문서가 명시한 파일명(t_secret.key)도 호환을 위해 동일 내용으로 둔다.
printf 'agent_api_key_test' > "$AGENT_HOME/api_keys/t_secret.key"
chown agent-admin:agent-core "$AGENT_HOME/api_keys/secret.key" "$AGENT_HOME/api_keys/t_secret.key"
chmod 0640 "$AGENT_HOME/api_keys/secret.key" "$AGENT_HOME/api_keys/t_secret.key"

cat > "$AGENT_HOME/agent.env" <<EOF
# agent 앱 실행 환경 변수
export AGENT_HOME=$AGENT_HOME
export AGENT_PORT=15034
export AGENT_UPLOAD_DIR=$AGENT_HOME/upload_files
export AGENT_KEY_PATH=$AGENT_HOME/api_keys
export AGENT_LOG_DIR=$LOG_DIR
EOF
chown agent-admin:agent-common "$AGENT_HOME/agent.env"
chmod 0640 "$AGENT_HOME/agent.env"
echo "   secret.key + t_secret.key created; agent.env written"

# ---------------------------------------------------------------------------
# 5. 앱 바이너리 + 관제 스크립트 배치
# ---------------------------------------------------------------------------
echo "## [5] App binary & scripts"
install -o agent-admin -g agent-common -m 0755 "$SRC/agent-app-linux-x86" "$AGENT_HOME/agent-app-linux-x86"

# monitor.sh : 소유자 agent-dev, 그룹 agent-core, 권한 750
install -o agent-dev -g agent-core -m 0750 "$SRC/scripts/monitor.sh" "$AGENT_HOME/bin/monitor.sh"
# 보너스 스크립트도 동일 정책으로 배치
install -o agent-dev -g agent-core -m 0750 "$SRC/scripts/report.sh"      "$AGENT_HOME/bin/report.sh"
install -o agent-dev -g agent-core -m 0750 "$SRC/scripts/rotate_logs.sh" "$AGENT_HOME/bin/rotate_logs.sh"
echo "   monitor.sh owner=agent-dev group=agent-core mode=750"

# ---------------------------------------------------------------------------
# 6. 방화벽(UFW): 활성화 + 20022/15034 tcp 만 허용
# ---------------------------------------------------------------------------
echo "## [6] UFW firewall"
ufw --force reset >/dev/null 2>&1 || true
ufw default deny incoming  >/dev/null
ufw default allow outgoing >/dev/null
ufw allow 20022/tcp >/dev/null
ufw allow 15034/tcp >/dev/null
ufw --force enable  >/dev/null
echo "   UFW enabled; allow 20022/tcp, 15034/tcp"

# ---------------------------------------------------------------------------
# 7. cron 데몬 기동
# ---------------------------------------------------------------------------
echo "## [7] cron daemon"
pgrep -x cron >/dev/null 2>&1 || cron
echo "   cron started"

echo "############ [setup_lab] DONE ############"
