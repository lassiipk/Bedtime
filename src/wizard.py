"""
wizard.py — Interactive CLI wizard to generate a bedtime.config.yaml.
"""

import sys
from pathlib import Path

try:
    import questionary
    from questionary import Style
    QUESTIONARY_AVAILABLE = True
except ImportError:
    QUESTIONARY_AVAILABLE = False

from src.utils import print_info, print_success, print_error, print_warning

STYLE = None
if QUESTIONARY_AVAILABLE:
    STYLE = Style([
        ("qmark",     "fg:#00bfff bold"),
        ("question",  "bold"),
        ("answer",    "fg:#00ff99 bold"),
        ("pointer",   "fg:#00bfff bold"),
        ("highlighted","fg:#00bfff bold"),
        ("selected",  "fg:#00ff99"),
        ("separator", "fg:#444444"),
        ("instruction","fg:#888888"),
    ])


def _ask(prompt_fn, *args, **kwargs):
    """Wrap questionary prompts; fall back to input() if not available."""
    if QUESTIONARY_AVAILABLE:
        return prompt_fn(*args, **kwargs, style=STYLE).ask()
    return None  # handled by fallback paths


# ── Main wizard ───────────────────────────────────────────────────────────────

def run_wizard(output_path: Path = None):
    """
    Run the interactive setup wizard.
    Writes a bedtime.config.yaml to output_path (defaults to project root).
    """
    if output_path is None:
        output_path = Path(__file__).parent.parent / "bedtime.config.yaml"

    try:
        from rich.console import Console
        Console().print(
            "\n[bold magenta]🌙  Bedtime Setup Wizard[/bold magenta]\n"
            "[dim]Answer a few questions and we'll generate your config.[/dim]\n"
        )
    except ImportError:
        print("\n🌙  Bedtime Setup Wizard\n")

    if not QUESTIONARY_AVAILABLE:
        print_warning(
            "questionary is not installed. Falling back to plain input().\n"
            "Install for a better experience: pip install questionary"
        )

    cfg = {}

    # ── Schedule ──────────────────────────────────────────────────────────────
    _section("Schedule")

    cfg["time"] = _prompt_text(
        "What time should Bedtime run? (e.g. 22:00 or 10:00 PM)",
        default="22:00",
        validate=_validate_time,
    )

    cfg["mode"] = _prompt_select(
        "Should this run every day (daily) or just once?",
        choices=["daily", "once"],
        default="daily",
    )

    if cfg["mode"] == "daily":
        all_days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        cfg["days"] = _prompt_checkbox(
            "Which days? (space to select, enter to confirm)",
            choices=all_days,
            default=all_days,
        )
    else:
        cfg["days"] = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        cfg["date"] = _prompt_text(
            "What date should it run? (YYYY-MM-DD)",
            default="",
            validate=_validate_date,
        )

    # ── Action ────────────────────────────────────────────────────────────────
    _section("Action")

    cfg["action"] = _prompt_select(
        "What should happen at that time?",
        choices=["shutdown", "restart", "sleep", "logoff", "lock", "custom"],
        default="shutdown",
    )

    if cfg["action"] == "custom":
        cfg["custom_command"] = _prompt_text(
            "Enter the custom command to run:",
            validate=lambda v: bool(v.strip()) or "Command cannot be empty.",
        )
    else:
        cfg["custom_command"] = ""

    # ── Warnings ──────────────────────────────────────────────────────────────
    _section("Warnings")

    cfg["warnings_enabled"] = _prompt_confirm(
        "Enable warnings before the action?", default=True
    )

    if cfg["warnings_enabled"]:
        raw_intervals = _prompt_text(
            "Warning intervals in seconds, comma-separated (e.g. 300,60,5 = 5min, 1min, 5sec)",
            default="300,60,5",
            validate=_validate_intervals,
        )
        cfg["intervals"] = [int(x.strip()) for x in raw_intervals.split(",")]

        cfg["message"] = _prompt_text(
            "Warning message (use {action}, {time_left}, {time} as placeholders):",
            default="Your PC will {action} in {time_left}. Please save your work!",
        )
    else:
        cfg["intervals"] = [300, 60, 5]
        cfg["message"] = "Your PC will {action} in {time_left}. Please save your work!"

    # ── Notifications ─────────────────────────────────────────────────────────
    _section("Notifications")

    cfg["popup"]    = _prompt_confirm("Show pop-up notifications?", default=True)
    cfg["terminal"] = _prompt_confirm("Print warnings to terminal?", default=True)
    cfg["sound"]    = _prompt_confirm("Play a sound alert?",         default=True)

    cfg["sound_file"] = ""
    if cfg["sound"]:
        custom_sound = _prompt_confirm("Use a custom sound file?", default=False)
        if custom_sound:
            cfg["sound_file"] = _prompt_text(
                "Path to sound file (.wav or .mp3):",
                validate=_validate_sound_file,
            )

    # ── Control ───────────────────────────────────────────────────────────────
    _section("Cancel & Snooze")

    cfg["allow_cancel"] = _prompt_confirm("Allow the user to cancel the action?", default=True)
    cfg["allow_snooze"] = _prompt_confirm("Allow the user to snooze the action?", default=True)

    if cfg["allow_snooze"]:
        raw_snooze = _prompt_text(
            "How many seconds to snooze?",
            default="300",
            validate=lambda v: v.isdigit() and int(v) > 0 or "Must be a positive number.",
        )
        cfg["snooze_duration"] = int(raw_snooze)

        raw_max = _prompt_text(
            "Maximum number of snoozes allowed?",
            default="3",
            validate=lambda v: v.isdigit() or "Must be a number.",
        )
        cfg["max_snoozes"] = int(raw_max)
    else:
        cfg["snooze_duration"] = 300
        cfg["max_snoozes"] = 3

    # ── Write config ──────────────────────────────────────────────────────────
    _write_yaml(cfg, output_path)
    print_success(f"Config written to: {output_path}")
    print_info("Run `python setup.py` to activate Bedtime.")


# ── YAML writer ───────────────────────────────────────────────────────────────

def _write_yaml(cfg: dict, path: Path):
    days_yaml = "\n".join(f"    - {d}" for d in cfg.get("days", []))
    intervals_yaml = "\n".join(f"    - {i}" for i in cfg.get("intervals", [300, 60, 5]))

    date_line = f'  date: "{cfg.get("date", "")}"'

    content = f"""# ============================================================
#  Bedtime Configuration File (generated by wizard)
#  Edit this file to customize. Run `python setup.py` to apply.
# ============================================================

schedule:
  time: "{cfg['time']}"
  mode: {cfg['mode']}
  days:
{days_yaml}
{date_line}

action:
  action: {cfg['action']}
  custom_command: "{cfg['custom_command']}"

warnings:
  enabled: {str(cfg['warnings_enabled']).lower()}
  intervals:
{intervals_yaml}
  message: "{cfg['message']}"

notifications:
  popup: {str(cfg['popup']).lower()}
  terminal: {str(cfg['terminal']).lower()}
  sound: {str(cfg['sound']).lower()}
  sound_file: "{cfg['sound_file']}"

control:
  allow_cancel: {str(cfg['allow_cancel']).lower()}
  allow_snooze: {str(cfg['allow_snooze']).lower()}
  snooze_duration: {cfg['snooze_duration']}
  max_snoozes: {cfg['max_snoozes']}
"""
    path.write_text(content, encoding="utf-8")


# ── Validators ────────────────────────────────────────────────────────────────

def _validate_time(v):
    try:
        from src.config import _parse_time_string
        _parse_time_string(v)
        return True
    except ValueError:
        return "Invalid time. Use HH:MM (e.g. 22:00) or HH:MM AM/PM (e.g. 10:00 PM)."


def _validate_date(v):
    import re
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
        return True
    return "Invalid date. Use YYYY-MM-DD format."


def _validate_intervals(v):
    try:
        parts = [int(x.strip()) for x in v.split(",")]
        if all(p > 0 for p in parts):
            return True
        return "All values must be positive integers."
    except ValueError:
        return "Must be comma-separated integers (e.g. 300,60,5)."


def _validate_sound_file(v):
    import os
    if os.path.exists(v.strip()):
        return True
    return f"File not found: {v}"


# ── Prompt helpers ────────────────────────────────────────────────────────────

def _section(title: str):
    try:
        from rich.console import Console
        Console().print(f"\n[bold cyan]── {title} ──[/bold cyan]")
    except ImportError:
        print(f"\n── {title} ──")


def _prompt_text(question: str, default: str = "", validate=None):
    if QUESTIONARY_AVAILABLE:
        kwargs = {"default": default}
        if validate:
            kwargs["validate"] = validate
        return questionary.text(question, **kwargs, style=STYLE).ask() or default
    prompt = f"{question} [{default}]: " if default else f"{question}: "
    while True:
        val = input(prompt).strip() or default
        if validate:
            result = validate(val)
            if result is not True:
                print(f"  ✖ {result}")
                continue
        return val


def _prompt_select(question: str, choices: list, default: str = None):
    if QUESTIONARY_AVAILABLE:
        return questionary.select(
            question, choices=choices, default=default, style=STYLE
        ).ask() or default
    print(f"{question}")
    for i, c in enumerate(choices, 1):
        print(f"  {i}. {c}")
    while True:
        val = input("Choice [1]: ").strip() or "1"
        if val.isdigit() and 1 <= int(val) <= len(choices):
            return choices[int(val) - 1]
        print("  ✖ Invalid choice.")


def _prompt_checkbox(question: str, choices: list, default: list = None):
    if QUESTIONARY_AVAILABLE:
        selected = questionary.checkbox(
            question, choices=choices, default=default or choices, style=STYLE
        ).ask()
        return selected if selected else (default or choices)
    print(f"{question} (comma-separated, e.g. Mon,Wed,Fri)")
    print(f"  Available: {', '.join(choices)}")
    raw = input(f"  [{','.join(default or choices)}]: ").strip()
    if not raw:
        return default or choices
    return [x.strip() for x in raw.split(",") if x.strip() in choices]


def _prompt_confirm(question: str, default: bool = True):
    if QUESTIONARY_AVAILABLE:
        return questionary.confirm(question, default=default, style=STYLE).ask()
    suffix = " [Y/n]: " if default else " [y/N]: "
    val = input(f"{question}{suffix}").strip().lower()
    if not val:
        return default
    return val in ("y", "yes")
