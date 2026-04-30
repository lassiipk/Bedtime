"""
config.py — Bedtime config loader and validator.

Supports YAML, JSON, and INI formats.
Priority: YAML > JSON > INI
"""

import os
import json
import configparser
from pathlib import Path

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

# ── Defaults ──────────────────────────────────────────────────────────────────

DEFAULTS = {
    "schedule": {
        "time": "22:00",
        "mode": "daily",
        "days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "date": "",
    },
    "action": {
        "action": "shutdown",
        "custom_command": "",
    },
    "warnings": {
        "enabled": True,
        "intervals": [300, 60, 5],
        "message": "Your PC will {action} in {time_left}. Please save your work!",
    },
    "notifications": {
        "popup": True,
        "terminal": True,
        "sound": True,
        "sound_file": "",
    },
    "control": {
        "allow_cancel": True,
        "allow_snooze": True,
        "snooze_duration": 300,
        "max_snoozes": 3,
    },
}

VALID_ACTIONS = {"shutdown", "restart", "sleep", "logoff", "lock", "custom"}
VALID_DAYS = {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}
VALID_MODES = {"daily", "once"}


# ── Loaders ───────────────────────────────────────────────────────────────────

def _load_yaml(path: Path) -> dict:
    if not YAML_AVAILABLE:
        raise ImportError("PyYAML is not installed. Run: pip install PyYAML")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_ini(path: Path) -> dict:
    parser = configparser.ConfigParser()
    parser.read(path, encoding="utf-8")
    result = {}
    for section in parser.sections():
        result[section] = dict(parser[section])
    return result


def _find_config(base_dir: Path):
    """Find the first available config file in priority order."""
    candidates = [
        (base_dir / "bedtime.config.yaml", "yaml"),
        (base_dir / "bedtime.config.yml",  "yaml"),
        (base_dir / "bedtime.config.json", "json"),
        (base_dir / "bedtime.config.ini",  "ini"),
        (base_dir / "bedtime.config",      "ini"),
    ]
    for path, fmt in candidates:
        if path.exists():
            return path, fmt
    return None, None


# ── Deep merge ────────────────────────────────────────────────────────────────

def _deep_merge(base: dict, override: dict) -> dict:
    """Merge override into base, returning a new dict."""
    result = dict(base)
    for key, val in override.items():
        if isinstance(val, dict) and key in result and isinstance(result[key], dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = val
    return result


# ── INI type coercion ─────────────────────────────────────────────────────────

def _coerce_ini(raw: dict) -> dict:
    """INI values are all strings; cast them to the right types."""
    def to_bool(v):
        return str(v).strip().lower() in ("true", "1", "yes")

    def to_int(v):
        return int(str(v).strip())

    def to_list_str(v):
        return [x.strip() for x in str(v).split(",") if x.strip()]

    def to_list_int(v):
        return [int(x.strip()) for x in str(v).split(",") if x.strip()]

    coerced = {}

    s = raw.get("schedule", {})
    coerced["schedule"] = {
        "time":  s.get("time", DEFAULTS["schedule"]["time"]),
        "mode":  s.get("mode", DEFAULTS["schedule"]["mode"]),
        "days":  to_list_str(s["days"]) if "days" in s else DEFAULTS["schedule"]["days"],
        "date":  s.get("date", ""),
    }

    a = raw.get("action", {})
    coerced["action"] = {
        "action":         a.get("action", DEFAULTS["action"]["action"]),
        "custom_command": a.get("custom_command", ""),
    }

    w = raw.get("warnings", {})
    coerced["warnings"] = {
        "enabled":   to_bool(w["enabled"]) if "enabled" in w else DEFAULTS["warnings"]["enabled"],
        "intervals": to_list_int(w["intervals"]) if "intervals" in w else DEFAULTS["warnings"]["intervals"],
        "message":   w.get("message", DEFAULTS["warnings"]["message"]),
    }

    n = raw.get("notifications", {})
    coerced["notifications"] = {
        "popup":      to_bool(n["popup"])    if "popup"    in n else DEFAULTS["notifications"]["popup"],
        "terminal":   to_bool(n["terminal"]) if "terminal" in n else DEFAULTS["notifications"]["terminal"],
        "sound":      to_bool(n["sound"])    if "sound"    in n else DEFAULTS["notifications"]["sound"],
        "sound_file": n.get("sound_file", ""),
    }

    c = raw.get("control", {})
    coerced["control"] = {
        "allow_cancel":    to_bool(c["allow_cancel"])  if "allow_cancel"  in c else DEFAULTS["control"]["allow_cancel"],
        "allow_snooze":    to_bool(c["allow_snooze"])  if "allow_snooze"  in c else DEFAULTS["control"]["allow_snooze"],
        "snooze_duration": to_int(c["snooze_duration"]) if "snooze_duration" in c else DEFAULTS["control"]["snooze_duration"],
        "max_snoozes":     to_int(c["max_snoozes"])    if "max_snoozes"   in c else DEFAULTS["control"]["max_snoozes"],
    }

    return coerced


# ── Validation ────────────────────────────────────────────────────────────────

def _validate(cfg: dict):
    errors = []

    # Time format
    t = cfg["schedule"]["time"]
    try:
        _parse_time_string(t)
    except ValueError:
        errors.append(f"schedule.time '{t}' is invalid. Use HH:MM (24h) or HH:MM AM/PM.")

    # Mode
    mode = cfg["schedule"]["mode"]
    if mode not in VALID_MODES:
        errors.append(f"schedule.mode '{mode}' is invalid. Use 'daily' or 'once'.")

    # Days
    for d in cfg["schedule"]["days"]:
        if d not in VALID_DAYS:
            errors.append(f"schedule.days contains invalid day '{d}'. Use Mon/Tue/Wed/Thu/Fri/Sat/Sun.")

    # Once mode needs a date
    if mode == "once" and not cfg["schedule"]["date"]:
        errors.append("schedule.date is required when mode is 'once'. Format: YYYY-MM-DD.")

    # Action
    action = cfg["action"]["action"]
    if action not in VALID_ACTIONS:
        errors.append(f"action.action '{action}' is invalid. Choose from: {', '.join(sorted(VALID_ACTIONS))}.")

    if action == "custom" and not cfg["action"]["custom_command"].strip():
        errors.append("action.custom_command must be set when action is 'custom'.")

    # Intervals must be positive ints
    for i in cfg["warnings"]["intervals"]:
        if not isinstance(i, int) or i <= 0:
            errors.append(f"warnings.intervals contains invalid value '{i}'. Must be positive integers (seconds).")

    # Snooze duration
    if cfg["control"]["snooze_duration"] <= 0:
        errors.append("control.snooze_duration must be greater than 0.")

    if cfg["control"]["max_snoozes"] < 0:
        errors.append("control.max_snoozes must be 0 or greater.")

    if errors:
        raise ValueError("Bedtime config has errors:\n" + "\n".join(f"  • {e}" for e in errors))


# ── Public API ────────────────────────────────────────────────────────────────

def load_config(base_dir: Path = None) -> dict:
    """
    Load, merge with defaults, and validate the config.
    Returns the final config dict.
    """
    if base_dir is None:
        base_dir = Path(__file__).parent.parent  # project root

    path, fmt = _find_config(base_dir)

    if path is None:
        raise FileNotFoundError(
            "No config file found. Run `python src/main.py init` to create one."
        )

    raw = {}
    if fmt == "yaml":
        raw = _load_yaml(path)
    elif fmt == "json":
        raw = _load_json(path)
    elif fmt == "ini":
        raw = _coerce_ini(_load_ini(path))

    cfg = _deep_merge(DEFAULTS, raw)
    _validate(cfg)
    return cfg


def _parse_time_string(time_str: str):
    """Parse HH:MM or HH:MM AM/PM into (hour, minute). Raises ValueError if invalid."""
    import re
    time_str = time_str.strip()
    # 24-hour
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", time_str)
    if m:
        h, mn = int(m.group(1)), int(m.group(2))
        if 0 <= h <= 23 and 0 <= mn <= 59:
            return h, mn
        raise ValueError(f"Invalid 24h time: {time_str}")
    # 12-hour
    m = re.fullmatch(r"(\d{1,2}):(\d{2})\s*(AM|PM)", time_str, re.IGNORECASE)
    if m:
        h, mn, period = int(m.group(1)), int(m.group(2)), m.group(3).upper()
        if period == "PM" and h != 12:
            h += 12
        elif period == "AM" and h == 12:
            h = 0
        if 0 <= h <= 23 and 0 <= mn <= 59:
            return h, mn
        raise ValueError(f"Invalid 12h time: {time_str}")
    raise ValueError(f"Cannot parse time: '{time_str}'")
