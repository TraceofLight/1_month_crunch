# 시스템 관제 자동화 스크립트 개발

다중 사용자 리눅스 서버를 운영자 관점에서 직접 구성한 결과물이다. 기본 보안(SSH·방화벽),
역할 기반 계정·그룹·ACL, 애플리케이션 실행 환경, 그리고 시스템 상태를 주기적으로 수집·기록하는
관제 자동화 스크립트(`monitor.sh`)와 로그 보존 정책까지를 하나의 재현 가능한 실습 환경으로 묶었다.

모든 설정·명령과 검증 결과는 `evidence/lab/` 아래에 텍스트로 보존되어 있으며, 본문의 각 항목은
해당 증거 파일을 직접 인용한다.

---

## 1. 산출물 구성과 재현 방법

### 1.1 파일 구성

| 경로 | 역할 |
|------|------|
| `scripts/monitor.sh` | **핵심 산출물.** 프로세스/포트 헬스 체크 + 방화벽 점검 + 자원 수집 + 로그 누적 |
| `scripts/report.sh` | (보너스 1) `monitor.log` 분석 — CPU/MEM/DISK 평균·최대·최소·샘플 수 |
| `scripts/rotate_logs.sh` | (보너스 2) 시간 기반 로그 보존 — 7일 압축·아카이브, 30일 삭제 |
| `scripts/setup_lab.sh` | 요구사항 §1~§4의 "일회성 환경 구성"을 멱등적으로 수행 |
| `scripts/run_lab.sh` | 빌드→구성→앱 부팅→관제→cron→보너스까지 전 과정을 1회 실행하고 증거 저장 |
| `Dockerfile` | Ubuntu 22.04 LTS 실습 컨테이너 (systemd 없이 sshd/cron/ufw 수동 기동) |
| `agent-app-linux-x86` | 제공된 실행 대상 애플리케이션 (PyInstaller ELF, 실행 대상) |
| `evidence/lab/*.txt` | 모든 검증 산출물(콘솔 캡처) |

### 1.2 한 줄 재현

```bash
bash scripts/run_lab.sh
```

이 명령 하나로 이미지 빌드 → 컨테이너 기동 → `setup_lab.sh`(보안/계정/권한/환경) → 앱 부팅 →
`monitor.sh` 실행 → cron 매분 등록 및 자동 누적 확인(약 80초 대기) → `report.sh`/`rotate_logs.sh`
시연이 순서대로 수행되고, 각 단계 결과가 `evidence/lab/01_setup.txt` ~ `11_rotate.txt` 에 저장된다.
전체 콘솔 로그는 `evidence/lab/_run_full.log` 에 통합 보존된다.

### 1.3 실습 환경

- 베이스: `ubuntu:22.04` (요구사항의 Ubuntu 22.04 LTS와 동일)
- 방화벽(UFW)이 컨테이너에서 동작하려면 런타임에 `--cap-add NET_ADMIN --cap-add NET_RAW` 가 필요하고,
  nft 가 아닌 legacy iptables 백엔드를 사용해야 한다. `Dockerfile` 에서
  `update-alternatives --set iptables /usr/sbin/iptables-legacy` 로 고정했다.
- 컨테이너에는 systemd 가 없으므로 `sshd`/`cron` 은 `setup_lab.sh` 에서 직접 기동한다.

---

## 2. 보안과 접근 통제

서버 보안의 출발점은 외부에서 도달 가능한 면(공격 표면)을 줄이고, 내부에서는 각 주체에게 역할에 꼭
필요한 권한만 부여하는 것이다. SSH 접속 포트를 옮기고 Root 원격 로그인을 막아 네트워크 노출을 좁힌
뒤, 역할 기반 계정·그룹과 ACL 로 공유 작업 공간과 보안 자원(API 키·로그)을 분리했다.

### 2.1 SSH 포트 변경(20022)과 Root 원격 로그인 차단

`/etc/ssh/sshd_config` 를 다음과 같이 변경했다(`setup_lab.sh` [1] 단계).

```bash
# 포트 22 → 20022
sed -i -E 's/^#?Port .*/Port 20022/' /etc/ssh/sshd_config
grep -q '^Port 20022' /etc/ssh/sshd_config || echo 'Port 20022' >> /etc/ssh/sshd_config
# Root 원격 로그인 차단
sed -i -E 's/^#?PermitRootLogin .*/PermitRootLogin no/' /etc/ssh/sshd_config
grep -q '^PermitRootLogin no' /etc/ssh/sshd_config || echo 'PermitRootLogin no' >> /etc/ssh/sshd_config
ssh-keygen -A            # 호스트 키 생성(신규 컨테이너)
/usr/sbin/sshd           # 데몬 기동
```

`sed` 의 정규식 `^#?Port` 는 주석 처리된 `#Port 22` 와 활성 `Port 22` 를 모두 잡아 한 줄로
치환하고, 혹시 해당 라인이 없을 경우를 대비해 `grep || echo >>` 로 멱등성을 보장한다.

**확인 (`evidence/lab/02_ssh.txt`)**

```
# sshd_config 핵심 설정
Port 20022
PermitRootLogin no

# sshd LISTEN 상태(ss)
tcp   LISTEN 0  128   0.0.0.0:20022   0.0.0.0:*   users:(("sshd",pid=21,fd=3))
tcp   LISTEN 0  128      [::]:20022      [::]:*   users:(("sshd",pid=21,fd=4))
```

설정 파일의 값과 실제 LISTEN 포트(20022)가 일치하며, 22번에서는 더 이상 수신하지 않는다.

이 두 설정이 "기본 보안"인 이유는 위협 모델 관점에서 분명하다.

- **포트 22 → 20022 변경.** 인터넷에 노출된 22번은 봇넷의 대량 스캐닝·브루트포스가 끊임없이
  두드리는 1순위 표적이다. 포트를 옮기는 것은 암호학적 방어가 아니라 **공격 표면(노이즈) 축소**다 —
  자동화 스캐너의 무차별 시도와 인증 로그 오염을 크게 줄여, 진짜 표적 공격을 로그에서 식별하기 쉬워진다.
  (보안성 자체는 키 인증·fail2ban 으로 보강해야 하며, 포트 변경만으로 안전해지는 것은 아니다 —
  "security by obscurity" 의 한계를 명확히 인지하고 보조 수단으로만 쓴다.)
- **Root 원격 로그인 차단(`PermitRootLogin no`).** root 는 이름이 고정되어 있고 전권을 가지므로,
  허용 시 공격자는 "비밀번호 하나만" 뚫으면 즉시 시스템 전체를 장악한다. 차단하면 (1) 공격자가
  유효한 일반 계정명까지 추가로 알아내야 하고(공격 난이도 상승), (2) 일반 계정 로그인 → `sudo` 승격의
  2단계를 강제해 **누가 무엇을 했는지 감사 추적**이 남으며, (3) 권한 분리(최소 권한)의 출발점이 된다.
  공유 root 세션은 행위자를 특정할 수 없어 사고 대응·책임 추적이 불가능하다는 점이 핵심 위협이다.

### 2.2 방화벽(UFW) — 필요 포트만 허용

요구사항 "택1" 중 **UFW** 를 선택했다(Ubuntu 기본 제공, 규칙 표현이 직관적). 정책은
"기본 인바운드 차단 + SSH(20022)·APP(15034)만 허용"이다(`setup_lab.sh` [6] 단계).

```bash
ufw --force reset
ufw default deny incoming      # 들어오는 연결 전부 차단(기본)
ufw default allow outgoing     # 나가는 연결 허용
ufw allow 20022/tcp            # SSH
ufw allow 15034/tcp            # APP
ufw --force enable
```

`default deny incoming` 으로 화이트리스트 방식(명시 허용한 두 포트 외 전부 차단)을 만든다.
이것이 "필요 포트만 허용"의 핵심으로, 새 서비스가 떠도 방화벽을 명시적으로 열기 전에는 외부에서
도달할 수 없다.

**확인 (`evidence/lab/03_firewall.txt`)**

```
Status: active
Default: deny (incoming), allow (outgoing), deny (routed)

To                  Action      From
--                  ------      ----
20022/tcp           ALLOW IN    Anywhere
15034/tcp           ALLOW IN    Anywhere
20022/tcp (v6)      ALLOW IN    Anywhere (v6)
15034/tcp (v6)      ALLOW IN    Anywhere (v6)
```

`Status: active`, 기본 인바운드 `deny`, 허용 규칙은 20022/15034 두 개(+IPv6)뿐임을 확인했다.

### 2.3 역할 기반 계정과 그룹

| 구분 | 이름 | 구성/역할 |
|------|------|-----------|
| 계정 | `agent-admin` | 운영/관리, **cron 실행자** |
| 계정 | `agent-dev` | 개발/운영, **`monitor.sh` 작성·소유자** |
| 계정 | `agent-test` | QA/테스트 |
| 그룹 | `agent-common` | admin, dev, test (공유 협업 그룹) |
| 그룹 | `agent-core` | admin, dev (보안 자원 접근 그룹) |

```bash
groupadd agent-common; groupadd agent-core
useradd -m -s /bin/bash agent-admin   # dev, test 동일
usermod -aG agent-common,agent-core agent-admin
usermod -aG agent-common,agent-core agent-dev
usermod -aG agent-common            agent-test     # test 는 core 에 미포함
```

**확인 (`evidence/lab/04_accounts.txt`)**

```
uid=1000(agent-admin) gid=1002(agent-admin) groups=...,1000(agent-common),1001(agent-core)
uid=1001(agent-dev)   gid=1003(agent-dev)   groups=...,1000(agent-common),1001(agent-core)
uid=1002(agent-test)  gid=1004(agent-test)  groups=...,1000(agent-common)

agent-common:x:1000:agent-admin,agent-dev,agent-test
agent-core:x:1001:agent-admin,agent-dev
```

`agent-test` 는 `agent-common` 에만 속하고 `agent-core` 에는 없다 — 이것이 뒤의 보안 디렉터리
접근 통제에서 결정적으로 작동한다.

### 2.4 디렉터리 구조·소유권·ACL과 최소 권한

`AGENT_HOME=/home/agent-admin/agent-app` 기준 구조와 권한(`setup_lab.sh` [3] 단계):

```bash
install -d -o agent-admin -g agent-common -m 0750 $AGENT_HOME
install -d -o agent-admin -g agent-core   -m 0750 $AGENT_HOME/bin
install -d -o agent-admin -g agent-common -m 2770 $AGENT_HOME/upload_files
install -d -o agent-admin -g agent-core   -m 2770 $AGENT_HOME/api_keys
install -d -o agent-admin -g agent-core   -m 2770 /var/log/agent-app

# 홈/AGENT_HOME 의 traverse(x) 만 공유 그룹에 부여 (디렉터리 진입용 최소 권한)
setfacl -m g:agent-common:x /home/agent-admin
setfacl -m g:agent-common:x $AGENT_HOME

# 공유: upload_files = agent-common R/W, 신규 파일도 그룹 권한 상속(default ACL)
setfacl    -m g:agent-common:rwx $AGENT_HOME/upload_files
setfacl -d -m g:agent-common:rwx $AGENT_HOME/upload_files

# 보안: api_keys / 로그 = agent-core ONLY R/W, others 완전 차단
setfacl    -m g:agent-core:rwx $AGENT_HOME/api_keys;  setfacl -d -m g:agent-core:rwx $AGENT_HOME/api_keys
setfacl    -m o::0             $AGENT_HOME/api_keys
setfacl    -m g:agent-core:rwx /var/log/agent-app;     setfacl -d -m g:agent-core:rwx /var/log/agent-app
setfacl    -m o::0             /var/log/agent-app
```

권한 모드 `2770` 의 앞자리 `2` 는 **setgid** 로, 이 디렉터리에서 새로 만들어지는 파일·하위
디렉터리가 부모의 그룹을 자동 상속하게 한다(공유 협업의 핵심). `default ACL`(`-d`)은 신규 생성물에도
그룹 R/W 가 그대로 적용되도록 보장한다.

**확인 (`evidence/lab/05_directories.txt`)**

```
drwxr-x---+ agent-admin agent-common  /home/agent-admin/agent-app
drwxrws---+ agent-admin agent-common  .../upload_files     (공유)
drwxrws---+ agent-admin agent-core    .../api_keys         (보안)
drwxr-x---  agent-admin agent-core    .../bin
drwxrws---+ agent-admin agent-core    /var/log/agent-app   (보안)

# bin 내부 (monitor.sh 권한 정책 — '스크립트 권한 정책과 실행자' 참고)
-rwxr-x--- agent-dev agent-core  monitor.sh
-rwxr-x--- agent-dev agent-core  report.sh
-rwxr-x--- agent-dev agent-core  rotate_logs.sh
```

`getfacl` 결과상 `upload_files` 는 `group:agent-common:rwx` + `other::---`,
`api_keys`·`/var/log/agent-app` 는 `group:agent-core:rwx` + `other::---` 로,
공유 vs 보안이 그룹 단위로 명확히 분리되어 있다(끝의 `default:` 항목으로 신규 파일까지 상속).

이 구성은 최소 권한(least privilege) 원칙 — "각 주체에게 그 역할에 꼭 필요한 권한만" 부여하는 원칙
— 을 그룹 분리 + ACL 로 구현한 것이다.

- **공유 vs 보안 분리.** `upload_files` 는 협업 그룹 `agent-common`(admin/dev/test) 전원이 R/W
  하는 공유 작업 공간, `api_keys`·`/var/log/agent-app` 는 `agent-core`(admin/dev)만 R/W 하는
  보안 공간으로 명확히 나눴다. QA 역할인 `agent-test` 는 core 에 없으므로 API 키나 로그에 절대 접근하지
  못한다(아래 실증에서 `Permission denied` 로 확인). 키가 유출되거나 test 계정이 탈취돼도 보안 자원은
  지켜진다 — 권한 경계가 곧 침해 격리(blast radius) 경계가 된다.
- **`other` 완전 차단(`o::0`).** 두 보안 디렉터리는 그룹 외 사용자에게 어떤 권한도 주지 않는다.
- **traverse(x) 만 최소 부여.** 공유 정책이 성립하려면 `agent-common` 멤버가 `/home/agent-admin`
  와 `AGENT_HOME` 을 "통과"할 수 있어야 한다. 읽기(r)·쓰기(w)는 주지 않고 실행(x)만 ACL 로 부여해,
  디렉터리 목록 열람이나 변경은 막으면서 하위 공유 디렉터리 진입만 허용했다(딱 필요한 만큼만).
- **setgid + default ACL.** 공유 디렉터리에서 새로 만들어지는 파일이 자동으로 올바른 그룹·권한을
  상속하게 해, 사람이 매번 `chgrp`/`chmod` 하지 않아도 정책이 유지된다(운영 실수 방지).

### 2.5 공유와 보안 디렉터리 분리 실증

권한이 "설정대로 실제로 작동하는지"를 서로 다른 계정으로 직접 시도해 확인했다
(`evidence/lab/05b_access_control.txt`).

```
# agent-test (common 멤버, core 비멤버) → upload_files 쓰기
RESULT: write OK (expected)                      ← 공유 디렉터리는 쓰기 성공

# agent-test (core 비멤버) → api_keys/secret.key 읽기
cat: .../api_keys/secret.key: Permission denied
RESULT exit=1 (Permission denied 기대)            ← 보안 디렉터리는 차단

# agent-dev (core 멤버) → api_keys/secret.key 읽기
agent_api_key_test <- read OK (expected)         ← core 멤버는 허용
```

`agent-test` 는 공유 디렉터리에는 쓸 수 있지만 보안 디렉터리(키)는 거부되고, `agent-core` 멤버인
`agent-dev` 는 키를 읽을 수 있다. 그룹 분리(common/core)가 의도대로 동작함을 증명한다.

---

## 3. 애플리케이션 실행 환경

제공된 Python 앱(`agent-app-linux-x86`)은 실행 대상이며, 키 위치·포트·로그 경로를 환경 변수로
고정한 뒤 일반 계정으로 부팅해 5단계 Boot Sequence 통과와 `0.0.0.0:15034` LISTEN 을 확인했다.

### 3.1 환경 변수와 키 파일

`AGENT_HOME/agent.env` 에 실행 환경을 고정했다(`setup_lab.sh` [4] 단계).

```bash
export AGENT_HOME=/home/agent-admin/agent-app
export AGENT_PORT=15034
export AGENT_UPLOAD_DIR=$AGENT_HOME/upload_files
export AGENT_KEY_PATH=$AGENT_HOME/api_keys      # 아래 주의 참고
export AGENT_LOG_DIR=/var/log/agent-app
```

키 파일은 `agent_api_key_test`(1줄)을 담아 `api_keys/` 에 둔다.

> **AGENT_KEY_PATH 관련 주의.** 요구사항 문서는 키 경로를 파일(`.../api_keys/t_secret.key`)로
> 예시하지만, 제공된 바이너리(`agent-app-linux-x86`)는 실제로는 `AGENT_KEY_PATH` 를 **디렉터리**로
> 받아 그 안의 `secret.key` 를 검증한다(부트 로그의 `Verified 'secret.key'` 가 근거). 따라서
> `AGENT_KEY_PATH` 는 `api_keys` 디렉터리로 지정하고, 호환을 위해 `secret.key` 와 `t_secret.key` 를
> 동일 내용으로 함께 생성했다. 환경 변수로 실행 환경을 "고정"하는 이유가 바로 이것이다 — 키 위치·포트·
> 로그 경로가 코드가 아니라 환경에 묶여 있어, 같은 바이너리를 환경만 바꿔 일관되게 재현·검증할 수 있다.

### 3.2 일반 계정 부팅과 성공 기준

루트가 아닌 `agent-admin` 으로 실행한다(`run_lab.sh`).

```bash
docker exec -u agent-admin -d <container> bash -lc \
  "source $AGENT_HOME/agent.env; cd \$AGENT_HOME; exec ./agent-app-linux-x86 ..."
```

**확인 (`evidence/lab/06_boot_sequence.txt`)** — 5단계 모두 `[OK]`, 마지막 `Agent READY`,
그리고 `0.0.0.0:15034` LISTEN:

```
>>> Starting Agent Boot Sequence...
[1/5] Checking User Account               [OK]   ... Running as service user 'agent-admin' (uid=1000)
[2/5] Verifying Environment Variables     [OK]   ... All required Envs correct
[3/5] Checking Required Files             [OK]   ... Verified 'secret.key' with correct key string.
[4/5] Checking Port Availability          [OK]   ... Port 15034 is available.
[5/5] Verifying Log Permission            [OK]   ... Log directory is writable: /var/log/agent-app
------------------------------------------------------------
All Boot Checks Passed!
Agent READY

# ss -tlnp 'sport = :15034'
LISTEN 0  1  0.0.0.0:15034  0.0.0.0:*
```

User Account(일반 계정)·환경 변수·키 파일·포트·로그 권한 5단계가 모두 통과했고, `0.0.0.0:15034` 로
LISTEN 중이므로 외부 인터페이스에서 접근 가능한 상태다. 앱 종료는 `Ctrl+C` 로 수행한다.

---

## 4. 시스템 관제 자동화 (monitor.sh)

`monitor.sh` 는 이 과제의 핵심 산출물로, 앱 가용성(프로세스·포트)을 점검하고 방화벽·자원 상태를
수집한 뒤 한 줄을 로그에 누적한다. Bash 로만 작성했고, cron 으로 매분 독립 실행된다.

### 4.1 동작 개요와 콘솔 출력

`monitor.sh` 는 다음 순서로 동작한다.

1. **[HEALTH CHECK]** — 앱 프로세스 + 포트 LISTEN. 둘 중 하나라도 실패하면 `exit 1`.
2. **[STATUS CHECK]** — 방화벽 활성 여부. 비활성이면 `[WARNING]` 만 출력하고 계속.
3. **[RESOURCE MONITORING]** — CPU/MEM/DISK 수집.
4. **임계값 경고** — CPU>20 / MEM>10 / DISK>80 초과 시 `[WARNING]`(종료하지 않음).
5. **로그 기록** — 필요 시 회전 후 `monitor.log` 에 한 줄 append.

**확인 (`evidence/lab/07_monitor_console.txt`)**

```
====== SYSTEM MONITOR RESULT ======

[HEALTH CHECK]
Checking process 'agent-app-linux-x86'... [OK] (PID: 371)
Checking port 15034... [OK]

[STATUS CHECK]
Checking firewall... [OK]

[RESOURCE MONITORING]
CPU Usage  : 0.6%
MEM Usage  : 9.3%
DISK Used  : 7%

[INFO] Log appended: /var/log/agent-app/monitor.log
```

캡처 시점 자원이 모두 임계값 이하(CPU 0.6≤20, MEM 9.3≤10, DISK 7≤80)라 경고 라인이 없다.
임계값은 요구사항이 지정한 값(20/10/80)을 그대로 사용했다. 헬스 체크가 모두 `[OK]` 이므로
종료 코드는 0이다.

> 요구사항의 예시 출력에는 monitor.sh 결과에 통계(STATISTICS REPORT)가 함께 보이지만, 기능 요구
> 자체는 monitor.sh 에 수집·로깅까지만 명시한다. 통계 분석은 책임을 분리해 보너스 1의 `report.sh`
> 가 담당하도록 했다(단일 책임 — monitor.sh 는 "수집기", report.sh 는 "분석기").

### 4.2 프로세스 식별·포트 확인 — 명령 선택과 이유

```bash
app_pids()         { pgrep -f "$APP_NAME"; }                       # APP_NAME=agent-app-linux-x86
port_is_listening(){ ss -ltn "sport = :$APP_PORT" | grep -q LISTEN; }
port_owner_pid()   { ss -ltnp "sport = :$APP_PORT" | grep -o 'pid=[0-9]*' | head -1 | cut -d= -f2; }
```

- **`pgrep -f` 를 쓰는 이유.** 제공 앱은 PyInstaller 로 묶인 ELF(`agent-app-linux-x86`)이고
  런처/워커로 프로세스가 갈라질 수 있다. `-f` 는 명령행 전체를 매칭하므로 인터프리터 래핑·인자
  차이와 무관하게 잡는다. `ps -ef | grep` 대비 `pgrep` 은 자기 자신(grep 프로세스)을 결과에 포함하지
  않아 오탐이 없고, 정수 PID 만 깔끔하게 반환한다.
- **`ss` 를 쓰는 이유.** `netstat` 은 비권장(net-tools deprecated)이며 `ss` 가 표준이다.
  `sport = :15034` 필터로 커널에서 바로 해당 포트만 조회해 `grep` 파이프보다 정확하고 빠르다.
  `-ltn` = LISTEN 중인 TCP 를 숫자 포트로(이름 해석 비용 제거).
- **`port_owner_pid()` 의 의미.** 로그에 남길 대표 PID 는 "실제로 그 포트를 LISTEN 하는 워커"가
  가장 의미 있다. `ss -ltnp` 로 소켓 소유 PID 를 얻되, 비root(agent-admin) 실행 시 PID 노출이
  막히면 빈 값이 되므로 그때는 `pgrep` 첫 PID 로 폴백한다.

### 4.3 자원 값 추출·파싱과 로그 포맷

| 지표 | 소스 | 계산 |
|------|------|------|
| CPU | `/proc/stat` 의 `cpu` 라인 | 1초 간격 2회 샘플 → `(Δtotal − Δidle)/Δtotal × 100` |
| MEM | `/proc/meminfo` | `(MemTotal − MemAvailable)/MemTotal × 100` |
| DISK | `df -P /` | 2번째 줄 5번째 컬럼(`Used%`)에서 `%` 제거 |

```bash
cpu_usage() {                       # top 의 로캘 의존 출력을 피하고 커널 카운터로 직접 계산
    a=$(grep '^cpu ' /proc/stat); sleep 1; b=$(grep '^cpu ' /proc/stat)
    awk -v a="$a" -v b="$b" 'BEGIN{
        split(a,A," "); split(b,B," ");
        for(i=2;i<=10;i++){t1+=A[i];t2+=B[i]}      # user..steal 합 = total
        idle1=A[5]+A[6]; idle2=B[5]+B[6];          # idle + iowait
        dt=t2-t1; di=idle2-idle1;
        printf "%.1f", (dt-di)/dt*100 }'
}
mem_usage() { awk '/^MemTotal:/{t=$2}/^MemAvailable:/{a=$2}END{printf "%.1f",(t-a)/t*100}' /proc/meminfo; }
disk_usage(){ df -P / | awk 'NR==2{gsub("%","",$5);print $5}'; }
```

- **CPU 를 `/proc/stat` 델타로 계산하는 이유.** `top -bn1` 한 번 호출 값은 부팅 이후 누적
  평균이라 "현재" 사용률이 아니고, 출력 포맷이 로캘/버전에 따라 흔들린다. 커널 카운터를 1초 간격으로
  두 번 읽어 차분을 내면 이식성 높고 정확한 순간 사용률이 된다. `idle` 에 `iowait` 를 포함해 I/O
  대기를 유휴로 본다.
- **MEM 을 `MemAvailable` 기준으로 계산하는 이유.** `MemFree` 만 보면 재확보 가능한 페이지
  캐시까지 "사용 중"으로 과대 계상된다. 커널이 추정한 `MemAvailable` 을 빼야 실제 압박 수준이 나온다.
- **DISK 는 루트(`/`) 파티션의 `Used%`** 만 정수로 취한다. `df -P` 의 POSIX 모드로 컬럼이 한 줄로
  유지되어 `awk` 파싱이 안정적이다.

**로그 한 줄 포맷** (요구사항 그대로):

```
[YYYY-MM-DD HH:MM:SS] PID:<pid> CPU:<f>% MEM:<f>% DISK_USED:<i>%
```

대괄호 타임스탬프 + 공백 구분 `KEY:VALUE` 형태라 사람이 읽기 쉽고, `report.sh` 의 `awk` 가
`$1 $2`(시각), `$4/$5/$6`(지표)로 단순 분해할 수 있다. CPU/MEM 은 소수 1자리, DISK 는 정수다.

### 4.4 경고(WARNING)와 종료(exit) 항목 분리 — 운영 이유

`monitor.sh` 는 점검 항목을 두 등급으로 나눈다.

- **종료 항목(exit 1):** 앱 프로세스 미존재, 포트 15034 미LISTEN. → "서비스가 죽었다"는 사실 자체로,
  더 수집할 의미가 없고 즉시 장애로 인지·복구해야 한다. cron 환경에서 비0 종료는 상위(메일/모니터링)에
  실패 신호로 전달된다.
- **경고 항목(WARNING, 계속 진행):** 방화벽 비활성, CPU/MEM/DISK 임계값 초과. → 서비스는 살아 있고
  "추세를 봐야 하는" 신호다. 여기서 종료해 버리면 정작 임계값을 넘던 시점의 자원 값이 로그에 남지
  않는다. 경고로만 표시하고 끝까지 수집·기록해야, 임계 초과가 일시 스파이크였는지 지속 상승이었는지를
  나중에 `report.sh` 로 분석할 수 있다.

핵심은 "**가용성(살아있나) = 즉시 중단·복구**" vs "**상태/추세 = 기록·관찰**"을 섞지 않는 것이다.
모든 것을 종료로 처리하면 노이즈로 알림 피로가 생기고, 모든 것을 경고로 처리하면 진짜 다운을 놓친다.

### 4.5 로그 누적과 용량 관리

매 실행마다 로그 디렉터리를 보장하고, 필요 시 회전한 뒤 한 줄을 덧붙인다.

```bash
mkdir -p "$AGENT_LOG_DIR"
rotate_log_if_needed
line="[$(date '+%F %T')] PID:$pid CPU:${cpu}% MEM:${mem}% DISK_USED:${disk}%"
echo "$line" >> "$LOG_FILE"
```

**확인 (`evidence/lab/08_monitor_log.txt`)** — 수동 1회 실행 직후:

```
[2026-06-05 15:39:54] PID:371 CPU:0.6% MEM:9.3% DISK_USED:7%
--- (wc -l) 1 ...
```

이후 cron 으로 라인이 누적되는 모습은 'cron 자동 실행'에서 확인한다.

**리다이렉션 기호 차이(`>` vs `>>`)와 누적 필요성.**

- `>` 는 **truncate-and-write**: 대상 파일을 0바이트로 비운 뒤 기록한다(없으면 생성).
- `>>` 는 **append**: 기존 내용 끝에 덧붙인다(없으면 생성).

`monitor.sh` 가 로그를 남길 때 `>>` 를 쓰는 이유는, 이 스크립트가 **cron 으로 매분 새 프로세스로
독립 실행**되기 때문이다. 만약 `>` 를 썼다면 매 실행마다 `monitor.log` 가 초기화되어 항상 "마지막
1줄"만 남고, 추세 분석(평균/최대/최소)의 근거가 되는 시계열이 통째로 사라진다. 누적이 곧 관제의
가치이므로 append 가 필수다. 반대로 로그 **회전** 시 현재 파일을 비울 때는 의도적으로 `: > "$LOG_FILE"`
(truncate)를 쓴다 — 회전 시점에만, 의도적으로, 새 파일을 시작하기 위해서다. 같은 기호라도 "매 실행
누적"과 "회전 시 초기화"라는 정반대 목적에 맞춰 구분해 사용한다.

**로그 용량 관리 (size 기반 회전).** 요구사항의 "최대 10MB / 10개 파일"을 스크립트 로직으로
구현했다(logrotate 데몬 의존 없이 cron 한 번에 끝나도록).

```bash
MAX_SIZE=$((10*1024*1024))   # 10MB (테스트 시 MONITOR_MAX_SIZE 로 축소 가능)
MAX_FILES=10                 # 현재 파일 + 회전본 .1~.9 = 최대 10개
rotate_log_if_needed() {
    [ -f "$LOG_FILE" ] || return 0
    size=$(stat -c %s "$LOG_FILE")
    [ "$size" -ge "$MAX_SIZE" ] || return 0
    rm -f "${LOG_FILE}.$((MAX_FILES-1))"                 # 가장 오래된 .9 제거
    for ((i=MAX_FILES-2; i>=1; i--)); do                 # .8→.9 ... .1→.2
        [ -f "${LOG_FILE}.$i" ] && mv -f "${LOG_FILE}.$i" "${LOG_FILE}.$((i+1))"
    done
    mv -f "$LOG_FILE" "${LOG_FILE}.1"                     # 현재 → .1
    : > "$LOG_FILE"                                       # 새 빈 파일 시작
}
```

매 실행 직전 `stat -c %s` 로 현재 크기를 재고, 10MB 이상이면 가장 오래된 회전본을 버리고 한 칸씩
밀어내는 방식이다. 그래서 디스크 점유는 항상 `10MB × 10 = 100MB` 로 상한이 묶인다.

**확인 (`evidence/lab/11_rotate.txt`, size 회전 부분)** — 임계값을 100바이트로 낮춰 5회 실행:

```
--- /tmp/rotdemo ---
-rw-r--r-- monitor.log     61    (현재, 회전 직후 새 파일)
-rw-r--r-- monitor.log.1   122
-rw-r--r-- monitor.log.2   122
```

100바이트 임계를 넘을 때마다 `.1`, `.2` 로 회전되며 현재 파일이 새로 시작됨을 확인했다.

> **logrotate 대안.** 동일 정책을 `/etc/logrotate.d/agent-app` 에
> `size 10M / rotate 9 / compress / missingok / copytruncate` 로도 구성할 수 있으나, 본 과제는
> "방법 자유"이고 cron 한 줄로 자기완결적이도록 스크립트 내장 회전을 택했다.

### 4.6 스크립트 권한 정책과 실행자

| 항목 | 값 | 근거 |
|------|-----|------|
| 경로 | `$AGENT_HOME/bin/monitor.sh` | 요구사항 |
| 소유자 | `agent-dev` | 스크립트 작성자 |
| 그룹 | `agent-core` | 보안 그룹(읽기·실행 허용 대상) |
| 권한 | `750` (`rwxr-x---`) | 소유자 전권, 그룹 읽기·실행, others 차단 |
| cron 실행자 | `agent-admin` | `agent-core` 멤버이므로 그룹 권한으로 실행 가능 |

`750` 에서 그룹 비트 `r-x` 는 "agent-core 멤버는 읽고 실행할 수 있다"는 뜻이다. cron 실행자인
`agent-admin` 은 `agent-core` 에 속하므로(계정 구성의 `id` 결과: `1001(agent-core)`) 소유자가 아니어도
그룹 자격으로 `monitor.sh` 를 실행할 수 있다. 동시에 `others` 는 모든 권한이 없어, core 밖의 계정은
스크립트를 읽지도 실행하지도 못한다. `bin` 디렉터리 역시 `0750 agent-core` 라 agent-admin 이
경로를 통과(traverse)해 스크립트에 도달할 수 있다. 또한 monitor.sh 가 기록하는
`/var/log/agent-app` 는 `agent-core` 그룹 R/W(디렉터리 권한 구성)이므로 agent-admin 이 로그를 남길 수 있다 —
**작성자(dev)·실행자(admin)·로그 디렉터리 권한이 모두 agent-core 한 축으로 정합**한다.

증거: `evidence/lab/05_directories.txt`(`-rwxr-x--- agent-dev agent-core monitor.sh`),
`evidence/lab/04_accounts.txt`(agent-admin ∈ agent-core).

### 4.7 cron 자동 실행

`agent-admin` 의 crontab 에 매분 실행을 등록한다.

```bash
echo '* * * * * /home/agent-admin/agent-app/bin/monitor.sh >/dev/null 2>&1' \
    | crontab -u agent-admin -
```

cron 은 거의 빈 환경(짧은 `PATH`, 로그인 셸 없음)에서 동작하므로, `monitor.sh` 는
**① 절대 경로로 등록**하고 **② 스크립트 내부에서 모든 환경 변수에 기본값**
(`AGENT_LOG_DIR`, `AGENT_PORT`, `AGENT_APP_NAME`)을 두어 환경이 없어도 정상 동작하도록 작성했다.

**확인 (`evidence/lab/09_cron.txt`)** — 등록 후 약 80초 대기:

```
# crontab -l
* * * * * /home/agent-admin/agent-app/bin/monitor.sh >/dev/null 2>&1

# 자동 누적 (대기 전/후)
lines before=1  after=3
[2026-06-05 15:39:54] PID:371 CPU:0.6% MEM:9.3% DISK_USED:7%   (수동 실행)
[2026-06-05 15:40:02] PID:371 CPU:0.5% MEM:9.4% DISK_USED:7%   (cron 자동)
[2026-06-05 15:41:02] PID:371 CPU:0.5% MEM:9.5% DISK_USED:7%   (cron 자동)
```

라인 수가 1 → 3 으로 늘고, 분 경계(`:40:02`, `:41:02`)마다 새 라인이 자동으로 누적됨을 확인했다.
cron 의 매분 실행이 정상 동작한다.

---

## 5. 운영 가이드

관제 스크립트를 다른 환경에 옮기거나 장애를 마주했을 때의 판단 기준이다. 재사용 시 바꿔야 할
지점, 프로세스·포트 신호가 어긋날 때의 진단 순서, 로그가 급증할 때의 대응 순서로 이어진다.

### 5.1 다른 앱·포트로 재사용할 때 점검 포인트

다른 앱/포트를 관제하도록 `monitor.sh` 를 재사용할 때 점검할 지점:

1. **프로세스 식별자.** `AGENT_APP_NAME`(=`pgrep -f` 매칭 문자열)을 새 프로세스명으로 바꾼다.
   이때 매칭이 **너무 넓으면**(예: `python`) 무관한 프로세스까지 잡혀 오탐이 나고, **너무 좁으면**
   런처/워커 분리 시 놓친다. 다른 프로세스 명령행과 겹치지 않는 고유 부분 문자열을 골라야 한다.
2. **포트.** `AGENT_PORT` 를 새 LISTEN 포트로 바꾼다(방화벽 허용 규칙·앱 설정과 반드시 일치).
3. **임계값.** CPU/MEM/DISK 기준(20/10/80)은 워크로드 특성에 맞게 재설정한다 — CPU 집약 서비스라면
   20%는 즉시 오탐 폭주를 부른다.
4. **로그 포맷 ↔ 파서 동기화.** 로그 한 줄 포맷을 바꾸면 `report.sh` 의 `awk` 필드 인덱스(`$4/$5/$6`)도
   같이 고쳐야 통계가 깨지지 않는다.
5. **권한·실행자·경로.** 소유자/그룹/모드(`agent-dev:agent-core 750`), cron 실행 계정의 그룹 자격,
   로그 디렉터리 쓰기 권한이 새 환경에서도 정합하는지 확인한다.

### 5.2 프로세스·포트 상태 불일치 진단

`monitor.sh` 가 프로세스를 먼저, 포트를 그다음에 점검하는 것은 인과 순서(프로세스가 떠야 포트가
열린다)를 따른 것이다. 두 신호가 어긋나는 두 경우:

**(A) 프로세스는 있는데 포트가 LISTEN 이 아님** — 가장 흔한 부분 장애.
- 가능한 원인: ① 앱이 아직 부팅 중(바인드 전), ② 포트 충돌로 바인드 실패(`EADDRINUSE`),
  ③ `0.0.0.0` 이 아니라 `127.0.0.1` 등 다른 인터페이스에 바인드, ④ 워커는 죽고 런처만 살아있음,
  ⑤ 설정상 포트(`AGENT_PORT`)와 실제 바인드 포트 불일치.
- 확인 순서: `ss -ltnp 'sport = :15034'`(정말 안 떴는지) → 앱 로그(`app.boot.log`/`agent_app.log`)에서
  바인드 에러·부팅 단계 확인 → `ps -p <pid> -o stat,comm,args`(좀비/런처만인지) → 환경변수
  `AGENT_PORT` 와 바인드 주소(`0.0.0.0`) 대조 → 필요 시 재기동.

**(B) 포트는 LISTEN 인데 프로세스 매칭이 안 됨**
- 가능한 원인: ① 바이너리/프로세스명이 바뀌어 `pgrep -f` 패턴이 빗나감, ② 다른(엉뚱한) 프로세스가
  같은 포트를 선점, ③ 모니터링 권한 부족으로 PID 가 안 보임.
- 확인 순서: `ss -ltnp 'sport = :15034'` 로 **포트 소유 PID 를 먼저** 얻고 →
  `ps -p <pid> -o comm,args` 로 그 PID 의 정체 확인 → 기대한 앱이면 `AGENT_APP_NAME` 패턴을 실제
  명령행에 맞게 교정, 엉뚱한 프로세스면 포트 선점 사고로 처리.

핵심 원칙: **포트의 실제 소유 PID(`ss -p`)를 사실의 기준점으로 삼고**, 프로세스명 매칭(`pgrep`)은
그 PID 와 대조해 검증하는 보조 수단으로 다룬다.

### 5.3 로그 급증 시 대응

`monitor.log`(또는 앱 로그)가 비정상적으로 빠르게 커질 때:

1. **무엇이 급증하는지 먼저 식별.** `ls -lS`/`du -sh` 로 어느 파일인지, `tail -f` 로 어떤 라인이
   반복되는지 본다. 대개 ① 앱 에러 루프(같은 예외 반복), ② cron 중복 등록으로 monitor 가 다중 실행,
   ③ 디버그 로그 레벨 방치, ④ 외부 요청 폭주가 원인이다.
2. **디스크 풀(full) 사고 예방.** 디스크가 차면 앱·DB 까지 동반 장애가 난다. 즉시 회전·압축으로
   공간을 회수한다 — `monitor.sh` 의 size 회전 임계를 낮추거나 `rotate_logs.sh` 를 수동 실행,
   급하면 오래된 회전본을 압축/삭제. `monitor.log` 는 이미 10MB×10개 = 100MB 상한이 걸려 있어
   monitor 자체로는 무한 증가하지 않는다.
3. **근본 원인 차단.** 에러 루프면 앱을 재기동/롤백하고, cron 중복이면 `crontab -l` 로 중복 항목을
   제거하고, 로그 레벨이 과도하면 낮춘다(증상 억제가 아니라 발생량 자체를 줄이는 것이 우선).
4. **보존 정책·알림 재조정.** 회전 임계/개수와 시간 기반 보존(7일 압축/30일 삭제)을 점검하고,
   `DISK_USED>80%` 경고가 조기에 뜨도록 임계·알림 경로를 정비해 다음 급증을 사전에 잡는다.

핵심은 "①공간 회수(응급) → ②근본 원인 제거 → ③재발 방지(정책·알림)" 순서로, 디스크 고갈이 2차
장애로 번지기 전에 끊는 것이다.

---

## 6. 보너스 과제

### 6.1 (보너스 1) report.sh — 요약 리포트

`monitor.log` 를 `awk` 로 분석해 CPU/MEM/DISK 의 평균·최대(시각)·최소(시각)와 샘플 수를 출력한다.
선택적으로 시작/종료 시각을 인자로 받아 해당 구간만 분석한다(ISO 형식이라 문자열 비교가 곧 시간 비교).

```bash
report.sh                                          # 전체 구간
report.sh "2026-06-05 15:40:00" "2026-06-05 15:41:00"  # 구간 지정
```

**확인 (`evidence/lab/10_report.txt`)**

```
====== STATISTICS REPORT ======
  [CPU]
    Average : 0.5%
    Maximum : 0.6% at 2026-06-05 15:39:54
    Minimum : 0.5% at 2026-06-05 15:40:02
  [Memory]
    Average : 9.4%
    Maximum : 9.5% at 2026-06-05 15:41:02
    Minimum : 9.3% at 2026-06-05 15:39:54
  [Disk]
    Average : 7.0% ...
  [Samples]
    Data Points: 3 samples
```

cron 으로 누적된 3개 샘플이 그대로 통계로 집계되었다.

### 6.2 (보너스 2) rotate_logs.sh — 시간 기반 보존 정책

1. `/var/log/agent-app/*.log` 중 **7일 이상 경과** 파일을 `gzip` 압축
2. 압축본(`.gz`)을 `/var/log/monitor/agent-app/archive/` 로 이동
3. 아카이브의 `*.gz` 중 **30일 이상 경과** 파일 삭제

예외 처리: 원본 디렉터리 미존재 → 경고 후 `exit 0`, 아카이브 디렉터리 생성 실패/쓰기 불가 → 압축은
제자리에 두고 경고, 쓰기 권한 없는 파일 → 건너뛰고 경고, 대상 0개 → "할 일 없음" 안내. 어떤 경우에도
스크립트가 비정상 종료하지 않고 안전하게 끝난다(`find ... -mtime` 로 경과일을 판정해 활성 로그를
건드리지 않음).

**확인 (`evidence/lab/11_rotate.txt`, 시간 기반 부분)** — 8일/3일 된 로그와 31일/5일 된 아카이브를
배치한 뒤 실행:

```
[INFO] Archived: old8.log.gz -> /var/log/monitor/agent-app/archive/
[INFO] Deleted old archive: old31.gz
[DONE] compressed=1 deleted=1
```

결과적으로 `old8.log`(8일) → 압축·아카이브 이동, `old31.gz`(31일) → 삭제, `old3.log`(3일)·
`old5.gz`(5일) → 그대로 유지되어 정책이 정확히 동작했다.

---

## 7. 증거 자료 인덱스

| 파일 | 내용 | 대응 요구사항 |
|------|------|----------------|
| `evidence/lab/01_setup.txt` | 전체 환경 구성(setup_lab.sh) 요약 | §1~§4 구성 |
| `evidence/lab/02_ssh.txt` | SSH 포트 20022 / PermitRootLogin no / ss LISTEN | §1 SSH |
| `evidence/lab/03_firewall.txt` | UFW active, 20022·15034 만 허용 | §1 방화벽 |
| `evidence/lab/04_accounts.txt` | id / getent — 계정·그룹 구성 | §2 계정/그룹 |
| `evidence/lab/05_directories.txt` | 디렉터리 권한 + getfacl(ACL) + bin 권한 | §2 권한/ACL |
| `evidence/lab/05b_access_control.txt` | 공유 쓰기 OK / 보안 읽기 차단·허용 실증 | §2 최소 권한 |
| `evidence/lab/06_boot_sequence.txt` | Boot 5단계 [OK] + Agent READY + 15034 LISTEN | §3 앱 부팅 |
| `evidence/lab/07_monitor_console.txt` | monitor.sh 콘솔(헬스/상태/자원) | §4 monitor.sh |
| `evidence/lab/08_monitor_log.txt` | monitor.log 누적 라인 | §4 로그 |
| `evidence/lab/09_cron.txt` | crontab 매분 등록 + 자동 누적(1→3) | §5 cron |
| `evidence/lab/10_report.txt` | report.sh 통계 | 보너스 1 |
| `evidence/lab/11_rotate.txt` | size 회전 + 시간 기반 보존 | §4 용량관리 / 보너스 2 |
| `evidence/lab/_run_full.log` | 빌드~보너스 전 과정 통합 로그 | 전체 |
