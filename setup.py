#!/usr/bin/env python3
"""
setup.py — Bedtime setup script (cross-platform).

What this does:
  1. Checks Python version
  2. Installs required dependencies
  3. Reads (or creates) your bedtime.config.yaml
  4. Validates the config
  5. Registers the task with the OS scheduler
  6. Confirms the next scheduled run

Usage:
  python setup.py
"""

import sys
import subprocess
from pathlib import Path

# ── Minimum Python version ────────────────────────────────────────────────────
if sys.version_info < (3, 8):
    print("✖  Bedtime requires Python 3.8 or higher.")
    print(f"   You have: Python {sys.version}")
    sys.exit(1)

# ── Ensure project root is on path ────────────────────────────────────────────
ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT))

# ── Install dependencies ───────────────────────────────────────────────────────
REQUIRED = ["PyYAML", "questionary", "rich", "plyer"]

def install_deps():
    print("📦  Checking dependencies...")
    for pkg in REQUIRED:
        try:
            __import__(pkg.lower().replace("-", "_"))
        except ImportError:
            print(f"    Installing {pkg}...")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", pkg, "--quiet"]
            )
    print("    All dependencies ready.\n")

install_deps()

# ── Now import everything ─────────────────────────────────────────────────────
from src.utils import print_banner, print_info, print_success, print_error, print_warning
from src.config import load_config
from src.scheduler import register_task, task_is_registered
from src.utils import next_run_datetime, format_until, seconds_until

# ── Banner ────────────────────────────────────────────────────────────────────
print_banner()
print_info("Setting up Bedtime...\n")

# ── Load or create config ─────────────────────────────────────────────────────
config_exists = any(
    (ROOT / name).exists()
    for name in ["bedtime.config.yaml", "bedtime.config.json", "bedtime.config.ini", "bedtime.config"]
)

if not config_exists:
    print_warning("No config file found.")
    create = input("  Would you like to create one now with the wizard? [Y/n]: ").strip().lower()
    if create in ("", "y", "yes"):
        from src.wizard import run_wizard
        run_wizard()
    else:
        print_error(
            "Cannot continue without a config. "
            "Copy bedtime.config.yaml from the repo and edit it, then re-run setup.py."
        )
        sys.exit(1)

try:
    cfg = load_config(ROOT)
except ValueError as e:
    print_error(f"Config validation failed:\n{e}")
    sys.exit(1)
except FileNotFoundError as e:
    print_error(str(e))
    sys.exit(1)

print_success("Config loaded and validated.\n")

# ── Show what will be scheduled ───────────────────────────────────────────────
sched  = cfg["schedule"]
action = cfg["action"]["action"]

try:
    next_dt = next_run_datetime(
        time_str=sched["time"],
        mode=sched["mode"],
        days=sched["days"],
        date_str=sched.get("date", ""),
    )
    secs     = seconds_until(next_dt)
    day_name = next_dt.strftime("%A")
    next_str = f"{next_dt.strftime('%Y-%m-%d %H:%M')} ({day_name}, {format_until(secs)})"
except ValueError as e:
    print_error(f"Could not compute next run time: {e}")
    sys.exit(1)

print_info(f"Action     : {action}")
print_info(f"Schedule   : {sched['time']}  [{sched['mode']}]")
print_info(f"Next run   : {next_str}\n")

# ── Register with OS scheduler ────────────────────────────────────────────────
print_info("Registering with OS scheduler...")
try:
    register_task(cfg)
except Exception as e:
    print_error(f"Failed to register task: {e}")
    sys.exit(1)

# ── Done ──────────────────────────────────────────────────────────────────────
print()
print_success("Bedtime is active!")
print_info(f"Next scheduled action: {action.upper()} at {next_str}")
print_info("To remove Bedtime at any time, run: python teardown.py")
