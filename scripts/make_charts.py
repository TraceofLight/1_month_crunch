#!/usr/bin/env python3
"""make_charts.py — 수집된 evidence 로그로부터 분석용 PNG 차트를 생성한다.

생성물(evidence/charts/):
  - oom_rss.png        : monitor.sh 가 관측한 RSS(MB) 추이 (128/256/512 비교)
  - cpu_load.png       : 앱 자체 보고 CPU Load(%) 추이 + 워치독 임계선(50%)
  - deadlock_activity.png : 교착(RSS 정지) vs 정상(RSS 상승) 활동량 대비

각 차트는 README 의 해당 케이스 Evidence 절에서 인용한다. 외부 의존성은
matplotlib 하나뿐이며, 파싱은 표준 라이브러리(re, datetime)만 사용한다.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # 헤드리스(디스플레이 없음) 환경용 백엔드
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
EVID = ROOT / "evidence"
CHARTS = EVID / "charts"
CHARTS.mkdir(parents=True, exist_ok=True)

# monitor 라인: [2026-06-07 20:46:36] PROCESS:... RSS:150MB ...
MON_RE = re.compile(r"\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)\].*RSS:(\d+)MB")
# 앱 로그 CPU Load: 2026-06-07 20:48:54,761 [INFO] [CpuWorker] Current Load: 5.00%
LOAD_RE = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),\d+.*Current Load: ([\d.]+)%")


def parse_monitor_rss(path: Path):
    """monitor 로그에서 (경과초, RSS_MB) 시계열을 뽑는다."""
    xs, ys, t0 = [], [], None
    if not path.exists():
        return xs, ys
    for line in path.read_text(errors="ignore").splitlines():
        m = MON_RE.search(line)
        if not m:
            continue
        t = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
        if t0 is None:
            t0 = t
        xs.append((t - t0).total_seconds())
        ys.append(int(m.group(2)))
    return xs, ys


def parse_load(path: Path):
    """앱 로그에서 (경과초, Current Load %) 시계열을 뽑는다."""
    xs, ys, t0 = [], [], None
    if not path.exists():
        return xs, ys
    for line in path.read_text(errors="ignore").splitlines():
        m = LOAD_RE.match(line)
        if not m:
            continue
        t = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
        if t0 is None:
            t0 = t
        xs.append((t - t0).total_seconds())
        ys.append(float(m.group(2)))
    return xs, ys


def chart_oom():
    fig, ax = plt.subplots(figsize=(9, 5))
    series = [
        ("oom/monitor_before.log", "MEMORY_LIMIT=128 (killed)", "tab:red"),
        ("oom/monitor_mid.log", "MEMORY_LIMIT=256 (killed)", "tab:orange"),
        ("oom/monitor_after.log", "MEMORY_LIMIT=512 (recovered/survived)", "tab:green"),
    ]
    plotted = False
    for rel, label, color in series:
        xs, ys = parse_monitor_rss(EVID / rel)
        if xs:
            ax.plot(xs, ys, marker="o", ms=3, label=label, color=color)
            plotted = True
    ax.set_title("OOM: monitor.sh observed RSS over time")
    ax.set_xlabel("elapsed time (s)")
    ax.set_ylabel("RSS (MB, max across launcher+worker)")
    ax.grid(True, alpha=0.3)
    if plotted:
        ax.legend()
    fig.tight_layout()
    fig.savefig(CHARTS / "oom_rss.png", dpi=110)
    plt.close(fig)


def chart_cpu():
    fig, ax = plt.subplots(figsize=(9, 5))
    for rel, label, color in [
        ("cpu/app_before.log", "CPU_MAX_OCCUPY=95 (watchdog kill)", "tab:red"),
        ("cpu/app_after.log", "CPU_MAX_OCCUPY=30 (safe)", "tab:green"),
    ]:
        xs, ys = parse_load(EVID / rel)
        if xs:
            ax.plot(xs, ys, marker="o", ms=3, label=label, color=color)
    ax.axhline(50, color="black", ls="--", lw=1.2, label="watchdog threshold (50%)")
    ax.set_title("CPU: app-reported Current Load vs fixed 50% watchdog threshold")
    ax.set_xlabel("elapsed time (s)")
    ax.set_ylabel("Current Load (%) — app self-reported metric")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(CHARTS / "cpu_load.png", dpi=110)
    plt.close(fig)


def chart_deadlock():
    fig, ax = plt.subplots(figsize=(9, 5))
    for rel, label, color in [
        ("deadlock/monitor_before.log", "THREAD=true (deadlock: RSS frozen)", "tab:red"),
        ("deadlock/monitor_after.log", "THREAD=false (normal: RSS rising)", "tab:green"),
    ]:
        xs, ys = parse_monitor_rss(EVID / rel)
        if xs:
            ax.plot(xs, ys, marker="o", ms=3, label=label, color=color)
    ax.set_title("Deadlock: RSS activity (frozen) vs normal (rising)")
    ax.set_xlabel("elapsed time (s)")
    ax.set_ylabel("RSS (MB)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(CHARTS / "deadlock_activity.png", dpi=110)
    plt.close(fig)


def main():
    chart_oom()
    chart_cpu()
    chart_deadlock()
    print("charts written to", CHARTS)


if __name__ == "__main__":
    main()
