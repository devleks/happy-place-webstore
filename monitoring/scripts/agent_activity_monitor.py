#!/usr/bin/env python3

import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


@dataclass(frozen=True)
class AgentEvent:
    agent: str
    event: str  # "selected" | "used"
    detected_via: str  # "reports" | "blackbox"
    generated_at: Optional[str] = None
    duration_seconds: Optional[int] = None


AGENT_PURPOSE: Dict[str, str] = {
    "LintGuard": "Static analysis (Python Ruff/Bandit + JS ESLint)",
    "PerfSmith": "Performance analysis (hotspots/bundle)",
    "SchemaSage": "Database audit (schema/indexes/explain)",
    "ShieldProbe": "Security & privacy scanning (pip/npm audit + secrets)",
    "AtlasReporter": "Consolidation/digest across agent outputs",
}

REPORT_FILES: Dict[str, Path] = {
    "LintGuard": Path("reports/lintguard.json"),
    "PerfSmith": Path("reports/perfsmith_summary.json"),
    "SchemaSage": Path("reports/db_audit.md"),
    "ShieldProbe": Path("reports/security_findings.json"),
    "AtlasReporter": Path("reports/weekly_agent_digest.json"),
}

BLACKBOX_AGENT_KEYWORDS = {
    "LintGuard": re.compile(r"\\bLintGuard\\b", re.IGNORECASE),
    "PerfSmith": re.compile(r"\\bPerfSmith\\b", re.IGNORECASE),
    "SchemaSage": re.compile(r"\\bSchemaSage\\b", re.IGNORECASE),
    "ShieldProbe": re.compile(r"\\bShieldProbe\\b", re.IGNORECASE),
    "AtlasReporter": re.compile(r"\\bAtlasReporter\\b", re.IGNORECASE),
}

BLACKBOX_CI_ALL_AGENTS_KEYWORDS = re.compile(
    r"\\brun_ci_agents\\b|\\bCI co-?worker agents\\b|\\brun (?:the )?CI (?:co-?worker )?agents\\b",
    re.IGNORECASE,
)

BLACKBOX_GENERIC_KEYWORDS = re.compile(r"\\bagent(s)?\\b|co-?worker|handoff|AGENT_TEAMS", re.IGNORECASE)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def project_root() -> Path:
    # monitoring/scripts/agent_activity_monitor.py -> project root
    return Path(__file__).resolve().parents[2]


def safe_read_text(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return None


def read_active_session_id(root: Path) -> Optional[str]:
    p = root / ".windsurf-blackbox" / ".temp" / "current-session"
    text = safe_read_text(p)
    if not text:
        return None
    session_id = text.strip()
    return session_id or None


def parse_blackbox_timeline_rows(session_log_text: str) -> List[Tuple[str, str, str]]:
    # Rows look like: | 03:34 | ACTION | Team Leaders established |
    rows: List[Tuple[str, str, str]] = []
    for line in session_log_text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        # Skip header/separator
        if line.lower().startswith("| time ") or set(line.replace("|", "").strip()) <= {"-"}:
            continue

        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 3:
            continue
        t, typ, desc = parts[0], parts[1], parts[2]
        # Basic validation
        if not re.match(r"^\\d{2}:\\d{2}$", t):
            continue
        rows.append((t, typ, desc))
    return rows


def detect_agents_from_blackbox(rows: Iterable[Tuple[str, str, str]]) -> List[AgentEvent]:
    detected: List[AgentEvent] = []
    for _t, _typ, desc in rows:
        matched_any_specific = False
        for agent, rx in BLACKBOX_AGENT_KEYWORDS.items():
            if rx.search(desc):
                detected.append(AgentEvent(agent=agent, event="selected", detected_via="blackbox"))
                matched_any_specific = True

        # If the timeline says we're running CI agents but doesn't name them,
        # treat this as an explicit selection of the whole CI agent set.
        if not matched_any_specific and BLACKBOX_CI_ALL_AGENTS_KEYWORDS.search(desc):
            for agent in REPORT_FILES.keys():
                detected.append(AgentEvent(agent=agent, event="selected", detected_via="blackbox"))
            matched_any_specific = True

        # If it says "agents" but not which, we don't guess.
        if not matched_any_specific and BLACKBOX_GENERIC_KEYWORDS.search(desc):
            # represent as generic selection signal (no specific agent)
            detected.append(AgentEvent(agent="(unspecified)", event="selected", detected_via="blackbox"))
    return detected


def read_json_fields(path: Path) -> Tuple[Optional[str], Optional[int]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None, None

    generated_at = None
    duration = None

    if isinstance(data, dict):
        ga = data.get("generated_at") or data.get("timestamp")
        if isinstance(ga, str):
            generated_at = ga

        dur = data.get("execution_time_seconds")
        if isinstance(dur, int):
            duration = dur
        else:
            # sometimes stored as string
            try:
                duration = int(dur)
            except Exception:
                duration = None

    return generated_at, duration


def read_markdown_generated_at(path: Path) -> Optional[str]:
    text = safe_read_text(path)
    if not text:
        return None

    # SchemaSage writes: **Generated:** 2025-...
    m = re.search(r"^\\*\\*Generated:\\*\\*\\s*(.+?)\\s*$", text, re.MULTILINE)
    if m:
        return m.group(1).strip()

    # fallback
    m = re.search(r"^Generated:\\s*(.+?)\\s*$", text, re.MULTILINE)
    if m:
        return m.group(1).strip()

    return None


def detect_agents_from_reports(root: Path, last_mtime: Dict[str, float]) -> List[AgentEvent]:
    detected: List[AgentEvent] = []

    for agent, rel in REPORT_FILES.items():
        path = root / rel
        if not path.exists():
            continue

        mtime = path.stat().st_mtime
        if mtime <= last_mtime.get(agent, 0.0):
            continue

        last_mtime[agent] = mtime

        generated_at: Optional[str] = None
        duration: Optional[int] = None

        if path.suffix.lower() == ".json":
            generated_at, duration = read_json_fields(path)
        elif path.suffix.lower() in {".md", ".markdown"}:
            generated_at = read_markdown_generated_at(path)

        detected.append(
            AgentEvent(
                agent=agent,
                event="used",
                detected_via="reports",
                generated_at=generated_at,
                duration_seconds=duration,
            )
        )

    return detected


def format_duration(runs: List[AgentEvent]) -> str:
    parts: List[str] = []
    total = 0
    have_any = False

    for r in runs:
        if r.duration_seconds is None:
            continue
        have_any = True
        total += r.duration_seconds
        parts.append(f"{r.agent} {r.duration_seconds}s")

    if not have_any:
        return "-"

    if len(parts) == 1:
        return parts[0]

    return "; ".join(parts) + f"; total {total}s"


def format_purpose(agents: List[str]) -> str:
    purposes = []
    for a in agents:
        p = AGENT_PURPOSE.get(a)
        if p:
            purposes.append(f"{a}: {p}")
    return " | ".join(purposes) if purposes else "-"


def print_update_table(agent_use: bool, collaboration: str, selection: str, frequency: str, duration: str, purpose: str) -> None:
    print(f"\nChecked at: {utc_now_iso()}")
    print("| Agent use | Agent collaboration | Agent selection | Frequency of agent selection | Duration | Purpose |")
    print("|---|---|---|---|---|---|")
    print(f"| {('Yes' if agent_use else 'No')} | {collaboration} | {selection} | {frequency} | {duration} | {purpose} |")


def main() -> int:
    root = project_root()
    interval = int(os.environ.get("AGENT_MONITOR_INTERVAL_SECS", "300"))

    # State
    last_mtime: Dict[str, float] = {k: 0.0 for k in REPORT_FILES.keys()}
    last_blackbox_row_count = 0
    total_selected_counts: Dict[str, int] = {}
    total_used_counts: Dict[str, int] = {}

    print(f"Agent Activity Monitor started ({utc_now_iso()})")
    print(f"Project root: {root}")
    print(f"Interval: {interval}s (set AGENT_MONITOR_INTERVAL_SECS to override)")

    while True:
        interval_selected_counts: Dict[str, int] = {}
        interval_used_counts: Dict[str, int] = {}
        events: List[AgentEvent] = []

        # Detect from reports
        events.extend(detect_agents_from_reports(root, last_mtime))

        # Detect from blackbox session log (only new rows)
        session_log = root / ".windsurf-blackbox" / ".temp" / "session-log"
        session_text = safe_read_text(session_log) or ""
        rows = parse_blackbox_timeline_rows(session_text)

        new_rows = rows[last_blackbox_row_count:]
        last_blackbox_row_count = len(rows)

        events.extend(detect_agents_from_blackbox(new_rows))

        # Summarize selection vs usage
        selected_named = [e.agent for e in events if e.agent in REPORT_FILES.keys()]
        used_named = [e.agent for e in events if e.event == "used" and e.agent in REPORT_FILES.keys()]

        selected_agents_sorted = sorted(set(selected_named))
        used_agents_sorted = sorted(set(used_named))

        agent_use = len(used_agents_sorted) > 0

        # Collaboration: reflect execution if possible, otherwise planned selection
        collaboration = "No"
        if len(used_agents_sorted) > 1:
            collaboration = "Yes"
        elif len(selected_agents_sorted) > 1 and len(used_agents_sorted) <= 1:
            collaboration = "Planned"

        # Frequency
        # - selected: counted once per agent per interval if there was an explicit selection
        #   OR (if no explicit selection) there was an observed usage.
        # - used: counted per observed usage event per interval.
        interval_selected_flag: Dict[str, bool] = {}
        interval_used_event_count: Dict[str, int] = {}

        for e in events:
            if e.agent not in REPORT_FILES.keys():
                continue

            if e.event == "selected":
                interval_selected_flag[e.agent] = True
            elif e.event == "used":
                interval_used_event_count[e.agent] = interval_used_event_count.get(e.agent, 0) + 1

        freq_agents_set = set(selected_agents_sorted) | set(used_agents_sorted)
        for agent in freq_agents_set:
            # Selection (once per interval)
            selected_this_interval = interval_selected_flag.get(agent, False) or interval_used_event_count.get(agent, 0) > 0
            if selected_this_interval:
                interval_selected_counts[agent] = interval_selected_counts.get(agent, 0) + 1
                total_selected_counts[agent] = total_selected_counts.get(agent, 0) + 1

            # Usage (per event)
            used_n = interval_used_event_count.get(agent, 0)
            if used_n > 0:
                interval_used_counts[agent] = interval_used_counts.get(agent, 0) + used_n
                total_used_counts[agent] = total_used_counts.get(agent, 0) + used_n

        # Handle generic selection signals (no specific agent names)
        has_unspecified_selection = any(e.agent == "(unspecified)" and e.event == "selected" for e in events)

        if not selected_agents_sorted and not has_unspecified_selection:
            selection = "-"
            frequency = "-"
            duration = "-"
            purpose = "-"
        else:
            if selected_agents_sorted:
                selection = f"selected: {', '.join(selected_agents_sorted)}"
            else:
                selection = "selected: (unspecified)"

            if used_agents_sorted:
                selection = f"{selection} | used: {', '.join(used_agents_sorted)}"
            else:
                selection = f"{selection} | used: -"

            freq_agents = sorted(set(selected_agents_sorted) | set(used_agents_sorted))
            interval_sel_bits = [f"{a}={interval_selected_counts.get(a, 0)}" for a in freq_agents]
            interval_used_bits = [f"{a}={interval_used_counts.get(a, 0)}" for a in freq_agents]
            total_sel_bits = [f"{a}={total_selected_counts.get(a, 0)}" for a in freq_agents]
            total_used_bits = [f"{a}={total_used_counts.get(a, 0)}" for a in freq_agents]

            frequency = (
                f"interval selected: {'; '.join(interval_sel_bits)} | interval used: {'; '.join(interval_used_bits)}"
                f" | total selected: {'; '.join(total_sel_bits)} | total used: {'; '.join(total_used_bits)}"
            )

            used_events = [e for e in events if e.event == "used"]
            duration = format_duration(used_events)
            purpose = format_purpose(selected_agents_sorted)

        print_update_table(
            agent_use=agent_use,
            collaboration=collaboration,
            selection=selection,
            frequency=frequency,
            duration=duration,
            purpose=purpose,
        )

        time.sleep(interval)


if __name__ == "__main__":
    raise SystemExit(main())
