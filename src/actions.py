"""
actions.py — Execute system-level actions on Windows, macOS, and Linux.
"""

import subprocess
import sys
from src.utils import get_os, print_info, print_error


# ── Action dispatch ───────────────────────────────────────────────────────────

def run_action(action: str, custom_command: str = ""):
    """
    Execute the configured system action.

    Args:
        action: One of shutdown, restart, sleep, logoff, lock, custom
        custom_command: Shell command to run when action == 'custom'
    """
    os_name = get_os()
    print_info(f"Executing action: {action} on {os_name}")

    dispatch = {
        "shutdown": _shutdown,
        "restart":  _restart,
        "sleep":    _sleep,
        "logoff":   _logoff,
        "lock":     _lock,
        "custom":   lambda: _custom(custom_command),
    }

    func = dispatch.get(action)
    if func is None:
        print_error(f"Unknown action '{action}'. Check your config.")
        sys.exit(1)

    func()


# ── Implementations ───────────────────────────────────────────────────────────

def _run(cmd: list, shell: bool = False):
    """Run a subprocess command, printing the command first."""
    try:
        subprocess.run(cmd, shell=shell, check=True)
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print_error(f"Command not found: {e}")
        sys.exit(1)


def _shutdown():
    os_name = get_os()
    if os_name == "windows":
        _run(["shutdown", "/s", "/t", "0"])
    elif os_name == "macos":
        _run(["osascript", "-e", 'tell app "System Events" to shut down'])
    else:
        _run(["shutdown", "-h", "now"])


def _restart():
    os_name = get_os()
    if os_name == "windows":
        _run(["shutdown", "/r", "/t", "0"])
    elif os_name == "macos":
        _run(["osascript", "-e", 'tell app "System Events" to restart'])
    else:
        _run(["shutdown", "-r", "now"])


def _sleep():
    os_name = get_os()
    if os_name == "windows":
        # rundll32 is the standard way to sleep on Windows
        _run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
    elif os_name == "macos":
        _run(["pmset", "sleepnow"])
    else:
        # systemctl suspend is the modern approach; fall back to pm-suspend
        try:
            _run(["systemctl", "suspend"])
        except SystemExit:
            _run(["pm-suspend"])


def _logoff():
    os_name = get_os()
    if os_name == "windows":
        _run(["shutdown", "/l"])
    elif os_name == "macos":
        _run(["osascript", "-e", 'tell app "System Events" to log out'])
    else:
        # Works for most desktop environments via loginctl
        try:
            _run(["loginctl", "terminate-user", ""])
        except SystemExit:
            _run(["pkill", "-KILL", "-u", _current_user_linux()])


def _lock():
    os_name = get_os()
    if os_name == "windows":
        _run(["rundll32.exe", "user32.dll,LockWorkStation"])
    elif os_name == "macos":
        _run([
            "osascript", "-e",
            'tell application "System Events" to keystroke "q" '
            'using {command down, control down}'
        ])
    else:
        # Try common Linux lockers in order
        for cmd in [
            ["loginctl", "lock-session"],
            ["xdg-screensaver", "lock"],
            ["gnome-screensaver-command", "--lock"],
            ["xscreensaver-command", "-lock"],
            ["qdbus", "org.kde.screensaver", "/ScreenSaver", "Lock"],
        ]:
            try:
                subprocess.run(cmd, check=True, capture_output=True)
                return
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        print_error("Could not lock screen. No supported screen locker found.")
        sys.exit(1)


def _custom(command: str):
    if not command.strip():
        print_error("custom_command is empty. Check your config.")
        sys.exit(1)
    print_info(f"Running custom command: {command}")
    _run(command, shell=True)


def _current_user_linux() -> str:
    import os
    return os.environ.get("USER", os.environ.get("LOGNAME", ""))
