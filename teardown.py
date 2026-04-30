#!/usr/bin/env python3
"""
teardown.py — Bedtime teardown script (cross-platform).

What this does:
  1. Removes Bedtime from the OS scheduler (cancels all tasks)
  2. Asks whether to keep or delete your config file
  3. Removes the skip flag if present
  4. Optionally uninstalls Bedtime dependencies

Usage:
  python teardown.py
"""

import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT))

try:
    from src.utils import print_banner, print_info, print_success, print_error, print_warning
except ImportError:
    def print_info(m):    print(f"[INFO]  {m}")
    def print_success(m): print(f"[OK]    {m}")
    def print_error(m):   print(f"[ERROR] {m}", file=sys.stderr)
    def print_warning(m): print(f"[WARN]  {m}")
    def print_banner():   print("\n🌙  Bedtime Teardown\n")

print_banner()
print_info("Removing Bedtime...\n")

anything_removed = False

# ── 1. Remove OS scheduler task ───────────────────────────────────────────────
print_info("Step 1: Removing scheduled task from OS...")
try:
    from src.scheduler import remove_task, task_is_registered
    if task_is_registered():
        remove_task()
        anything_removed = True
    else:
        print_warning("No registered task found. Skipping.")
except Exception as e:
    print_warning(f"Could not remove task (may not exist): {e}")

# ── 2. Config file — ask the user ─────────────────────────────────────────────
print()
config_names = [
    "bedtime.config.yaml",
    "bedtime.config.yml",
    "bedtime.config.json",
    "bedtime.config.ini",
    "bedtime.config",
]
found_configs = [ROOT / name for name in config_names if (ROOT / name).exists()]

if found_configs:
    print_info("Step 2: Config file(s) found:")
    for p in found_configs:
        print(f"         • {p.name}")
    print()
    print("  Your config has your scheduled time, action, and warning settings.")
    print("  If you keep it, you can re-activate Bedtime later by running setup.py.")
    print()
    delete_config = input(
        "  Delete config file(s)? [y/N]: "
    ).strip().lower()

    if delete_config in ("y", "yes"):
        for p in found_configs:
            p.unlink()
            print_success(f"Deleted: {p.name}")
        anything_removed = True
    else:
        print_success("Config file(s) kept. Re-activate anytime with: python setup.py")
else:
    print_info("Step 2: No config files found. Skipping.")

# ── 3. Remove skip flag ───────────────────────────────────────────────────────
skip_file = ROOT / ".bedtime_skip"
if skip_file.exists():
    skip_file.unlink()
    print_success("Removed skip flag.")

# ── 4. Optionally uninstall dependencies ─────────────────────────────────────
print()
remove_deps = input(
    "  Uninstall Bedtime dependencies (PyYAML, questionary, rich, plyer)? [y/N]: "
).strip().lower()

DEPS = ["PyYAML", "questionary", "rich", "plyer"]

if remove_deps in ("y", "yes"):
    print_info("\nStep 3: Uninstalling dependencies...")
    for pkg in DEPS:
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "uninstall", pkg, "-y", "--quiet"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print_success(f"Uninstalled: {pkg}")
        except Exception:
            print_warning(f"Could not uninstall {pkg} (may not have been installed by Bedtime).")
else:
    print_info("Step 3: Dependencies kept.")

# ── Done ──────────────────────────────────────────────────────────────────────
print()
if anything_removed or remove_deps in ("y", "yes"):
    print_success("Bedtime has been completely removed from your system.")
else:
    print_info("Nothing was found to remove. Bedtime was not active.")

print_info("Thanks for using Bedtime 🌙")
