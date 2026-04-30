"""
utils.py — Shared helpers for Bedtime.
"""

import platform
import sys
from datetime import datetime, timedelta


# ── OS Detection ──────────────────────────────────────────────────────────────

def get_os() -> str:
    """Return 'windows', 'macos', or 'linux'."""
    s = platform.system().lower()
    if s == "windows":
        return "windows"
    elif s == "darwin":
        return "macos"
    else:
        return "linux"


def require_os(*allowed):
    """Raise if the current OS is not in the allowed list."""
    current = get_os()
    if current not in allowed:
        raise OSError(
            f"This operation is only supported on {', '.join(allowed)}. "
            f"Detected OS: {current}"
        )


# ── Time helpers ──────────────────────────────────────────────────────────────

def format_seconds(seconds: int) -> str:
    """Turn seconds into a human-readable string: '5 minutes', '1 minute', '30 seconds'."""
    if seconds >= 120:
        mins = seconds // 60
        return f"{mins} minutes"
    elif seconds == 60:
        return "1 minute"
    elif seconds > 1:
        return f"{seconds} seconds"
    else:
        return "1 second"


def next_run_datetime(time_str: str, mode: str, days: list, date_str: str) -> datetime:
    """
    Calculate the next datetime when Bedtime should fire.

    Args:
        time_str: e.g. "22:00" or "10:00 PM"
        mode: "daily" or "once"
        days: list of day abbreviations e.g. ["Mon", "Wed"]
        date_str: "YYYY-MM-DD" (only used when mode == "once")

    Returns:
        datetime of the next scheduled run
    """
    from src.config import _parse_time_string
    hour, minute = _parse_time_string(time_str)
    now = datetime.now()

    if mode == "once":
        from datetime import date
        y, m, d = map(int, date_str.split("-"))
        run_dt = datetime(y, m, d, hour, minute)
        if run_dt < now:
            raise ValueError(f"Scheduled time {run_dt} is in the past.")
        return run_dt

    # Daily: find the next matching weekday at the given time
    day_map = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}
    allowed = {day_map[d] for d in days if d in day_map}

    candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    for i in range(8):  # check up to 7 days ahead
        check = candidate + timedelta(days=i)
        if check.weekday() in allowed and check > now:
            return check

    raise ValueError("Could not find a valid next run time. Check your days/time config.")


def seconds_until(target: datetime) -> int:
    """Return whole seconds until target datetime."""
    delta = target - datetime.now()
    return max(0, int(delta.total_seconds()))


# ── Console output ────────────────────────────────────────────────────────────

try:
    from rich.console import Console
    from rich.text import Text
    _console = Console()
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

def print_info(msg: str):
    if RICH_AVAILABLE:
        _console.print(f"[bold cyan]ℹ[/bold cyan]  {msg}")
    else:
        print(f"[INFO]  {msg}")

def print_success(msg: str):
    if RICH_AVAILABLE:
        _console.print(f"[bold green]✔[/bold green]  {msg}")
    else:
        print(f"[OK]    {msg}")

def print_warning(msg: str):
    if RICH_AVAILABLE:
        _console.print(f"[bold yellow]⚠[/bold yellow]  {msg}")
    else:
        print(f"[WARN]  {msg}")

def print_error(msg: str):
    if RICH_AVAILABLE:
        _console.print(f"[bold red]✖[/bold red]  {msg}", err=True)
    else:
        print(f"[ERROR] {msg}", file=sys.stderr)

def print_banner():
    if RICH_AVAILABLE:
        _console.print(
            "\n[bold magenta]🌙  Bedtime[/bold magenta]  "
            "[dim]— Your PC, on a schedule.[/dim]\n"
        )
    else:
        print("\n🌙  Bedtime — Your PC, on a schedule.\n")
