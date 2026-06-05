# 관제 자동화 실습 환경 (Ubuntu 22.04 LTS).
# systemd 없이 sshd/cron/ufw 를 수동 기동하는 컨테이너 랩.
# UFW 활성화에는 런타임에서 --cap-add NET_ADMIN --cap-add NET_RAW 가 필요하다.
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# 관제/보안 실습에 필요한 패키지.
#  - openssh-server : SSH 포트/Root 차단 실습
#  - ufw            : 방화벽 정책
#  - cron           : monitor.sh 주기 실행
#  - acl            : setfacl/getfacl (공유 vs 보안 디렉터리 분리)
#  - iproute2       : ss (포트 LISTEN 점검)
#  - procps         : pgrep/ps (프로세스 점검)
RUN apt-get update && apt-get install -y --no-install-recommends \
        openssh-server \
        ufw \
        cron \
        acl \
        iproute2 \
        procps \
        sudo \
        gzip \
        findutils \
        ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 # ufw 가 동작하려면 nft 가 아닌 legacy iptables 백엔드가 필요(컨테이너 환경).
 # ip6tables 는 건드리지 않는다(건드리면 ufw status 가 깨진다).
 && update-alternatives --set iptables /usr/sbin/iptables-legacy

# 앱 바이너리와 스크립트를 이미지에 베이크(재현성 — 호스트 마운트에 의존하지 않음).
COPY agent-app-linux-x86 /opt/agent/agent-app-linux-x86
COPY scripts/ /opt/agent/scripts/

# 실행 권한 부여 + CRLF 방지(Windows 호스트에서 작성될 수 있으므로).
RUN chmod +x /opt/agent/agent-app-linux-x86 \
 && sed -i 's/\r$//' /opt/agent/scripts/*.sh \
 && chmod +x /opt/agent/scripts/*.sh

# PID 1 로 컨테이너를 유지; 실제 구성은 setup_lab.sh 를 exec 로 수행한다.
CMD ["sleep", "infinity"]
