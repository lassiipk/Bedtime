"""
main.py — Bedtime CLI entry point.

Usage:
  python src/main.py init        → Interactive wizard to generate config
  python src/main.py run         → Run the warning countdown + action now
  python src/main.py status      → Show current schedule and next run time
  python src/main.py cancel      → Cancel today's action (one-time skip)
  python src/main.py edit        → Open the config file in your text editor
"""

import sys
import os
from pathlib import Path

# Make sure project root is on PYTHONPATH when run directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import print_banner, print_info, print_success, print_error, print_warning, get_os


# ── Command dispatch ──────────────────────────────────────────────────────────

def cmd_init():
    """Run the interactive wizard to create a config file."""
    from src.wizard import run_wizard
    run_wizard()


def cmd_run():
    """
    Load config, compute the next run datetime, start the warning countdown,
    then execute the configured action.
    """
    from src.config import load_config
    from src.utils import next_run_datetime, seconds_until
    from src.countdown import run_countdown
    from src.actions import run_action
    from datetime import datetime

    try:
        cfg = load_config()
    except (FileNotFoundError, ValueError) as e:
        print_error(str(e))
        sys.exit(1)

    sched = cfg["schedule"]
    action_cfg = cfg["action"]

    try:
        target_dt = next_run_datetime(
            time_str=sched["time"],
            mode=sched["mode"],
            days=sched["days"],
            date_str=sched.get("date", ""),
        )
    except ValueError as e:
        print_error(str(e))
        sys.exit(1)

    secs = seconds_until(target_dt)
    print_info(
        f"Action [{action_cfg['action']}] scheduled for "
        f"{target_dt.strftime('%Y-%m-%d %H:%M')} "
        f"({secs}s from now)"
    )

    # Run the warning countdown
    should_proceed = run_countdown(cfg, target_dt)

    if should_proceed:
        run_action(
            action=action_cfg["action"],
            custom_command=action_cfg.get("custom_command", ""),
        )
    else:
        print_warning("Action was cancelled. Nothing happened.")


def cmd_status():
    """Show the current schedule and next run time."""
    from src.config import load_config
    from src.utils import next_run_datetime, format_seconds, seconds_until
    from src.scheduler import task_is_registered
    from datetime import datetime

    try:
        cfg = load_config()
    except FileNotFoundError:
        print_error("No config found. Run `python src/main.py init` first.")
        sys.exit(1)
    except ValueError as e:
        print_error(str(e))
        sys.exit(1)

    sched = cfg["schedule"]
    action = cfg["action"]["action"]
    registered = task_is_registered()

    try:
        next_dt = next_run_datetime(
            time_str=sched["time"],
            mode=sched["mode"],
            days=sched["days"],
            date_str=sched.get("date", ""),
        )
        secs = seconds_until(next_dt)
        next_str = f"{next_dt.strftime('%Y-%m-%d %H:%M')}  ({format_seconds(secs)} from now)"
    except ValueError as e:
        next_str = f"Could not compute: {e}"

    try:
        from rich.table import Table
        from rich.console import Console
        t = Table(title="🌙  Bedtime Status", show_header=False, box=None, padding=(0, 2))
        t.add_row("[dim]Action[/dim]",    f"[bold]{action}[/bold]")
        t.add_row("[dim]Time[/dim]",      sched["time"])
        t.add_row("[dim]Mode[/dim]",      sched["mode"])
        if sched["mode"] == "daily":
            t.add_row("[dim]Days[/dim]",  ", ".join(sched["days"]))
        else:
            t.add_row("[dim]Date[/dim]",  sched.get("date", ""))
        t.add_row("[dim]Next run[/dim]",  next_str)
        t.add_row("[dim]Registered[/dim]", "✔ Yes" if registered else "✖ No (run setup.py)")
        intervals = cfg["warnings"]["intervals"]
        t.add_row("[dim]Warnings at[/dim]", ", ".join(f"{i}s" for i in intervals))
        Console().print(t)
    except ImportError:
        print(f"  Action:     {action}")
        print(f"  Time:       {sched['time']}")
        print(f"  Mode:       {sched['mode']}")
        print(f"  Next run:   {next_str}")
        print(f"  Registered: {'Yes' if registered else 'No (run setup.py)'}")


def cmd_cancel():
    """Cancel today's scheduled action by writing a skip flag."""
    skip_file = Path(__file__).parent.parent / ".bedtime_skip"
    skip_file.write_text("skip", encoding="utf-8")
    print_success(
        "Today's action will be skipped. "
        "The skip clears automatically after the action time passes."
    )


def cmd_edit():
    """Open the config file in the system default text editor."""
    import subprocess
    root = Path(__file__).parent.parent

    for name in ["bedtime.config.yaml", "bedtime.config.json", "bedtime.config.ini", "bedtime.config"]:
        p = root / name
        if p.exists():
            _open_editor(p)
            return

    print_error("No config file found. Run `python src/main.py init` first.")
    sys.exit(1)


def _open_editor(path: Path):
    os_name = get_os()
    import subprocess
    if os_name == "windows":
        os.startfile(str(path))
    elif os_name == "macos":
        subprocess.run(["open", "-t", str(path)])
    else:
        editor = os.environ.get("EDITOR", "nano")
        subprocess.run([editor, str(path)])
    print_info(f"Opening {path}")


# ── Help ──────────────────────────────────────────────────────────────────────

def print_help():
    try:
        from rich.console import Console
        from rich.table import Table
        t = Table(title="🌙  Bedtime Commands", box=None, padding=(0, 2))
        t.add_column("Command", style="bold cyan", no_wrap=True)
        t.add_column("Description")
        t.add_row("init",   "Interactive wizard to create your config")
        t.add_row("run",    "Start the countdown and run the scheduled action")
        t.add_row("status", "Show current config and next scheduled run")
        t.add_row("cancel", "Skip today's action (one-time)")
        t.add_row("edit",   "Open the config file in your text editor")
        Console().print(t)
    except ImportError:
        print("Commands: init | run | status | cancel | edit")


# ── Entry ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print_banner()

    command = sys.argv[1] if len(sys.argv) > 1 else "help"

    commands = {
        "init":   cmd_init,
        "run":    cmd_run,
        "status": cmd_status,
        "cancel": cmd_cancel,
        "edit":   cmd_edit,
        "help":   print_help,
    }

    fn = commands.get(command)
    if fn is None:
        print_error(f"Unknown command: '{command}'")
        print_help()
        sys.exit(1)

    fn()
