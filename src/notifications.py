"""
notifications.py — Deliver warnings to the user via popup, terminal, and/or sound.
"""

import sys
import threading
from src.utils import get_os, print_warning, print_error, format_seconds


# ── Message formatting ─────────────────────────────────────────────────────────

def format_message(template: str, action: str, time_left_seconds: int, scheduled_time: str) -> str:
    """Fill in placeholders in the warning message template."""
    return template.format(
        action=action,
        time_left=format_seconds(time_left_seconds),
        time=scheduled_time,
    )


# ── Terminal notification ──────────────────────────────────────────────────────

def notify_terminal(message: str):
    """Print a prominent warning to the terminal."""
    try:
        from rich.console import Console
        from rich.panel import Panel
        console = Console()
        console.print(
            Panel(
                f"[bold yellow]{message}[/bold yellow]",
                title="[bold red]⏰  Bedtime Warning[/bold red]",
                border_style="red",
            )
        )
    except ImportError:
        border = "=" * 60
        print(f"\n{border}")
        print(f"  ⏰  BEDTIME WARNING")
        print(f"  {message}")
        print(f"{border}\n")


# ── Popup notification ─────────────────────────────────────────────────────────

def notify_popup(message: str, title: str = "Bedtime Warning"):
    """Show a native OS desktop notification (non-blocking)."""
    os_name = get_os()

    def _show():
        try:
            if os_name == "windows":
                _popup_windows(title, message)
            elif os_name == "macos":
                _popup_macos(title, message)
            else:
                _popup_linux(title, message)
        except Exception as e:
            print_error(f"Pop-up notification failed: {e}")

    # Run in background thread so it doesn't block the countdown
    t = threading.Thread(target=_show, daemon=True)
    t.start()


def _popup_windows(title: str, message: str):
    try:
        from plyer import notification
        notification.notify(title=title, message=message, app_name="Bedtime", timeout=10)
    except Exception:
        # Fallback: use PowerShell toast
        import subprocess
        ps_script = (
            f'[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, '
            f'ContentType = WindowsRuntime] > $null;'
            f'$template = [Windows.UI.Notifications.ToastNotificationManager]'
            f'::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02);'
            f'$template.SelectSingleNode("//text[@id=1]").InnerText = "{title}";'
            f'$template.SelectSingleNode("//text[@id=2]").InnerText = "{message}";'
            f'$toast = [Windows.UI.Notifications.ToastNotification]::new($template);'
            f'[Windows.UI.Notifications.ToastNotificationManager]'
            f'::CreateToastNotifier("Bedtime").Show($toast);'
        )
        subprocess.run(["powershell", "-Command", ps_script], capture_output=True)


def _popup_macos(title: str, message: str):
    import subprocess
    script = f'display notification "{message}" with title "{title}"'
    subprocess.run(["osascript", "-e", script], capture_output=True)


def _popup_linux(title: str, message: str):
    import subprocess
    try:
        subprocess.run(["notify-send", "--urgency=critical", title, message], check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        try:
            from plyer import notification
            notification.notify(title=title, message=message, app_name="Bedtime", timeout=10)
        except Exception as e:
            print_error(f"Linux popup failed: {e}")


# ── Sound notification ─────────────────────────────────────────────────────────

def notify_sound(sound_file: str = ""):
    """Play a sound alert. Uses custom file if provided, else system beep."""
    def _play():
        if sound_file and sound_file.strip():
            _play_file(sound_file.strip())
        else:
            _system_beep()

    t = threading.Thread(target=_play, daemon=True)
    t.start()


def _play_file(path: str):
    import os
    if not os.path.exists(path):
        print_error(f"Sound file not found: {path}. Falling back to system beep.")
        _system_beep()
        return
    try:
        # Try playsound first
        from playsound import playsound
        playsound(path)
        return
    except ImportError:
        pass
    # Try pygame
    try:
        import pygame
        pygame.mixer.init()
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        import time
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        return
    except ImportError:
        pass
    # Fallback
    _system_beep()


def _system_beep():
    os_name = get_os()
    try:
        if os_name == "windows":
            import winsound
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        elif os_name == "macos":
            import subprocess
            subprocess.run(["afplay", "/System/Library/Sounds/Ping.aiff"], capture_output=True)
        else:
            # Write BEL character to terminal
            sys.stdout.write("\a")
            sys.stdout.flush()
    except Exception:
        sys.stdout.write("\a")
        sys.stdout.flush()


# ── Combined send ─────────────────────────────────────────────────────────────

def send_warning(
    message: str,
    action: str,
    time_left_seconds: int,
    scheduled_time: str,
    cfg_notifications: dict,
    cfg_warnings: dict,
):
    """
    Send all enabled warning notifications at once.

    Args:
        message: Raw message template from config
        action: The action name (for display)
        time_left_seconds: Seconds until the action
        scheduled_time: e.g. "22:00"
        cfg_notifications: The notifications section of the config
        cfg_warnings: The warnings section of the config
    """
    text = format_message(
        template=cfg_warnings["message"],
        action=action,
        time_left_seconds=time_left_seconds,
        scheduled_time=scheduled_time,
    )

    if cfg_notifications.get("terminal", True):
        notify_terminal(text)

    if cfg_notifications.get("popup", True):
        notify_popup(text)

    if cfg_notifications.get("sound", True):
        notify_sound(cfg_notifications.get("sound_file", ""))
