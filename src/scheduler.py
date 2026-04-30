"""
scheduler.py — Register and remove Bedtime tasks with the OS native scheduler.

Windows   → Task Scheduler (schtasks)
macOS     → launchd (~/Library/LaunchAgents/)
Linux     → cron (crontab)
"""

import subprocess
import sys
import os
import tempfile
from pathlib import Path
from src.utils import get_os, print_info, print_success, print_error, print_warning

TASK_NAME = "Bedtime"
PLIST_LABEL = "com.lassiipk.bedtime"
PLIST_PATH  = Path.home() / "Library" / "LaunchAgents" / f"{PLIST_LABEL}.plist"
CRON_MARKER = "# bedtime-managed"

# The Python interpreter being used right now
PYTHON = sys.executable

# Root of the bedtime project (one level above src/)
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
MAIN_SCRIPT  = PROJECT_ROOT / "src" / "main.py"


# ── Register ───────────────────────────────────────────────────────────────────

def register_task(cfg: dict):
    """Register the Bedtime scheduled task with the OS scheduler."""
    os_name = get_os()
    if os_name == "windows":
        _register_windows(cfg)
    elif os_name == "macos":
        _register_macos(cfg)
    else:
        _register_linux(cfg)


def _register_windows(cfg: dict):
    """Use schtasks to register a Windows Task Scheduler task."""
    time_str   = cfg["schedule"]["time"]
    mode       = cfg["schedule"]["mode"]
    days       = cfg["schedule"]["days"]
    date_str   = cfg["schedule"]["date"]

    # Parse time
    from src.config import _parse_time_string
    hour, minute = _parse_time_string(time_str)
    start_time = f"{hour:02d}:{minute:02d}"

    command = f'"{PYTHON}" "{MAIN_SCRIPT}" run'

    if mode == "once":
        start_date = date_str  # YYYY-MM-DD
        args = [
            "schtasks", "/create", "/tn", TASK_NAME,
            "/tr", command,
            "/sc", "once",
            "/st", start_time,
            "/sd", start_date.replace("-", "/"),
            "/f",
        ]
    else:
        # Daily or specific days
        day_map = {"Mon":"MON","Tue":"TUE","Wed":"WED","Thu":"THU",
                   "Fri":"FRI","Sat":"SAT","Sun":"SUN"}
        if len(days) == 7:
            schedule_type = "daily"
            args = [
                "schtasks", "/create", "/tn", TASK_NAME,
                "/tr", command,
                "/sc", "daily",
                "/st", start_time,
                "/f",
            ]
        else:
            day_str = ",".join(day_map[d] for d in days if d in day_map)
            args = [
                "schtasks", "/create", "/tn", TASK_NAME,
                "/tr", command,
                "/sc", "weekly",
                "/d", day_str,
                "/st", start_time,
                "/f",
            ]

    _run(args)
    print_success(f"Task '{TASK_NAME}' registered in Windows Task Scheduler.")


def _register_macos(cfg: dict):
    """Write a launchd plist and load it."""
    from src.config import _parse_time_string
    time_str = cfg["schedule"]["time"]
    hour, minute = _parse_time_string(time_str)
    mode = cfg["schedule"]["mode"]
    days = cfg["schedule"]["days"]

    day_map = {"Mon":1,"Tue":2,"Wed":3,"Thu":4,"Fri":5,"Sat":6,"Sun":0}

    # Build weekday array for plist
    if mode == "once":
        # Use StartCalendarInterval with a date
        import re
        y, m, d = cfg["schedule"]["date"].split("-")
        calendar_block = (
            f"<key>StartCalendarInterval</key>\n"
            f"<dict>\n"
            f"  <key>Year</key><integer>{y}</integer>\n"
            f"  <key>Month</key><integer>{int(m)}</integer>\n"
            f"  <key>Day</key><integer>{int(d)}</integer>\n"
            f"  <key>Hour</key><integer>{hour}</integer>\n"
            f"  <key>Minute</key><integer>{minute}</integer>\n"
            f"</dict>"
        )
    else:
        if len(days) == 7:
            calendar_block = (
                f"<key>StartCalendarInterval</key>\n"
                f"<dict>\n"
                f"  <key>Hour</key><integer>{hour}</integer>\n"
                f"  <key>Minute</key><integer>{minute}</integer>\n"
                f"</dict>"
            )
        else:
            entries = "\n".join(
                f"<dict>\n"
                f"  <key>Weekday</key><integer>{day_map[d]}</integer>\n"
                f"  <key>Hour</key><integer>{hour}</integer>\n"
                f"  <key>Minute</key><integer>{minute}</integer>\n"
                f"</dict>"
                for d in days if d in day_map
            )
            calendar_block = (
                f"<key>StartCalendarInterval</key>\n"
                f"<array>\n{entries}\n</array>"
            )

    plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>{PLIST_LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>{PYTHON}</string>
    <string>{MAIN_SCRIPT}</string>
    <string>run</string>
  </array>
  {calendar_block}
  <key>RunAtLoad</key>
  <false/>
  <key>StandardOutPath</key>
  <string>{PROJECT_ROOT}/bedtime.log</string>
  <key>StandardErrorPath</key>
  <string>{PROJECT_ROOT}/bedtime.log</string>
</dict>
</plist>
"""
    PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    PLIST_PATH.write_text(plist, encoding="utf-8")
    _run(["launchctl", "load", str(PLIST_PATH)])
    print_success(f"launchd agent loaded: {PLIST_PATH}")


def _register_linux(cfg: dict):
    """Add a crontab entry for Bedtime."""
    from src.config import _parse_time_string
    time_str = cfg["schedule"]["time"]
    hour, minute = _parse_time_string(time_str)
    mode = cfg["schedule"]["mode"]
    days = cfg["schedule"]["days"]

    day_map = {"Mon":"1","Tue":"2","Wed":"3","Thu":"4","Fri":"5","Sat":"6","Sun":"0"}

    if mode == "once":
        # cron doesn't support one-time jobs well; use at(1) if available
        _register_linux_once(cfg, hour, minute)
        return

    if len(days) == 7:
        dow = "*"
    else:
        dow = ",".join(day_map[d] for d in days if d in day_map)

    cron_line = f"{minute} {hour} * * {dow} {PYTHON} {MAIN_SCRIPT} run  {CRON_MARKER}"

    # Read existing crontab, strip old bedtime entries, add new one
    existing = _read_crontab()
    lines = [l for l in existing.splitlines() if CRON_MARKER not in l]
    lines.append(cron_line)
    _write_crontab("\n".join(lines) + "\n")
    print_success(f"crontab entry added: {cron_line}")


def _register_linux_once(cfg: dict, hour: int, minute: int):
    """Use the `at` command for a one-time Linux job."""
    date_str = cfg["schedule"]["date"]
    at_time  = f"{hour:02d}:{minute:02d} {date_str}"
    cmd      = f'"{PYTHON}" "{MAIN_SCRIPT}" run'
    try:
        proc = subprocess.run(
            ["at", at_time],
            input=cmd,
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0:
            print_success(f"One-time job scheduled via `at` for {at_time}.")
        else:
            print_error(f"`at` command failed: {proc.stderr}")
            _fallback_once_instructions(at_time, cmd)
    except FileNotFoundError:
        print_warning("`at` is not installed.")
        _fallback_once_instructions(at_time, cmd)


def _fallback_once_instructions(at_time: str, cmd: str):
    print_warning(
        f"Could not schedule one-time job automatically.\n"
        f"  Manually run this at {at_time}:\n  {cmd}"
    )


# ── Remove ─────────────────────────────────────────────────────────────────────

def remove_task():
    """Remove the Bedtime scheduled task from the OS scheduler."""
    os_name = get_os()
    if os_name == "windows":
        _remove_windows()
    elif os_name == "macos":
        _remove_macos()
    else:
        _remove_linux()


def _remove_windows():
    try:
        _run(["schtasks", "/delete", "/tn", TASK_NAME, "/f"])
        print_success(f"Task '{TASK_NAME}' removed from Windows Task Scheduler.")
    except SystemExit:
        print_warning(f"Task '{TASK_NAME}' was not found. Nothing to remove.")


def _remove_macos():
    if PLIST_PATH.exists():
        try:
            subprocess.run(["launchctl", "unload", str(PLIST_PATH)], capture_output=True)
        except Exception:
            pass
        PLIST_PATH.unlink()
        print_success(f"launchd agent removed: {PLIST_PATH}")
    else:
        print_warning(f"No launchd plist found at {PLIST_PATH}. Nothing to remove.")


def _remove_linux():
    existing = _read_crontab()
    if CRON_MARKER not in existing:
        print_warning("No Bedtime crontab entry found. Nothing to remove.")
        return
    cleaned = "\n".join(
        l for l in existing.splitlines() if CRON_MARKER not in l
    ) + "\n"
    _write_crontab(cleaned)
    print_success("Bedtime crontab entry removed.")


# ── Status ─────────────────────────────────────────────────────────────────────

def task_is_registered() -> bool:
    """Check if a Bedtime task currently exists in the OS scheduler."""
    try:
        os_name = get_os()
        if os_name == "windows":
            result = subprocess.run(
                ["schtasks", "/query", "/tn", TASK_NAME],
                capture_output=True, text=True
            )
            return result.returncode == 0
        elif os_name == "macos":
            return PLIST_PATH.exists()
        else:
            existing = _read_crontab()
            return CRON_MARKER in existing
    except Exception:
        return False


# ── Helpers ────────────────────────────────────────────────────────────────────

def _run(args: list):
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        print_error(f"Command failed: {' '.join(args)}\n{result.stderr}")
        sys.exit(1)


def _read_crontab() -> str:
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    if result.returncode != 0:
        return ""
    return result.stdout


def _write_crontab(content: str):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".cron", delete=False) as f:
        f.write(content)
        tmp = f.name
    subprocess.run(["crontab", tmp], check=True)
    os.unlink(tmp)
