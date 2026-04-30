"""
countdown.py — Warning countdown engine.

Fires notifications at configured intervals before the action,
and handles cancel/snooze input from the user.
"""

import time
import sys
import threading
from datetime import datetime, timedelta
from src.utils import print_info, print_warning, print_success, format_seconds
from src.notifications import send_warning


class CountdownEngine:
    """
    Manages the warning countdown loop.

    Fires warnings at each interval, then executes the action unless the
    user cancels or snoozes (if those options are enabled).
    """

    def __init__(self, cfg: dict, target_dt: datetime):
        self.cfg = cfg
        self.target_dt = target_dt
        self.cancelled = False
        self.snooze_count = 0
        self._lock = threading.Lock()

    # ── Public entry point ────────────────────────────────────────────────────

    def run(self) -> bool:
        """
        Run the countdown. Returns True if the action should proceed,
        False if the user cancelled.
        """
        w = self.cfg["warnings"]

        if not w.get("enabled", True):
            print_info("Warnings are disabled. Action will run immediately.")
            return True

        intervals = sorted(w.get("intervals", [300, 60, 5]), reverse=True)
        action = self.cfg["action"]["action"]
        sched_time = self.cfg["schedule"]["time"]

        # Start input listener in background (for cancel/snooze in terminal)
        self._start_input_listener()

        while True:
            now = datetime.now()
            seconds_left = max(0, int((self.target_dt - now).total_seconds()))

            if self.cancelled:
                print_warning("Action cancelled by user.")
                return False

            # Fire any pending warnings
            for interval in intervals:
                window_start = interval + 2   # 2-sec grace window
                window_end   = interval - 2
                if window_end <= seconds_left <= window_start:
                    send_warning(
                        message=w["message"],
                        action=action,
                        time_left_seconds=interval,
                        scheduled_time=sched_time,
                        cfg_notifications=self.cfg["notifications"],
                        cfg_warnings=w,
                    )
                    self._show_control_options(seconds_left)

            if seconds_left <= 0:
                if self.cancelled:
                    print_warning("Action cancelled by user.")
                    return False
                print_success("Countdown complete. Running action now.")
                return True

            time.sleep(1)

    # ── Snooze ────────────────────────────────────────────────────────────────

    def snooze(self):
        ctrl = self.cfg["control"]
        max_snoozes = ctrl.get("max_snoozes", 3)
        snooze_secs = ctrl.get("snooze_duration", 300)

        with self._lock:
            if self.snooze_count >= max_snoozes:
                print_warning(
                    f"Maximum snoozes ({max_snoozes}) reached. Action will proceed."
                )
                return
            self.snooze_count += 1
            self.target_dt = datetime.now() + timedelta(seconds=snooze_secs)

        print_info(
            f"Snoozed! Action delayed by {format_seconds(snooze_secs)}. "
            f"({self.snooze_count}/{max_snoozes} snoozes used)"
        )

    # ── Cancel ────────────────────────────────────────────────────────────────

    def cancel(self):
        with self._lock:
            self.cancelled = True
        print_warning("Cancelling action...")

    # ── Control options display ───────────────────────────────────────────────

    def _show_control_options(self, seconds_left: int):
        ctrl = self.cfg["control"]
        allow_cancel = ctrl.get("allow_cancel", True)
        allow_snooze = ctrl.get("allow_snooze", True)
        max_snoozes  = ctrl.get("max_snoozes", 3)

        can_snooze = allow_snooze and self.snooze_count < max_snoozes

        if not allow_cancel and not can_snooze:
            return  # Nothing to show

        parts = []
        if allow_cancel:
            parts.append("[C] Cancel")
        if can_snooze:
            snooze_secs = ctrl.get("snooze_duration", 300)
            parts.append(f"[S] Snooze {format_seconds(snooze_secs)}")

        try:
            from rich.console import Console
            Console().print(
                f"  [dim]Options: {' | '.join(parts)}  (type in terminal)[/dim]"
            )
        except ImportError:
            print(f"  Options: {' | '.join(parts)}  (type in terminal)")

    # ── Background input listener ─────────────────────────────────────────────

    def _start_input_listener(self):
        ctrl = self.cfg["control"]
        if not ctrl.get("allow_cancel", True) and not ctrl.get("allow_snooze", True):
            return  # No point listening

        def _listen():
            while not self.cancelled and datetime.now() < self.target_dt + timedelta(seconds=10):
                try:
                    line = input().strip().lower()
                    if line in ("c", "cancel"):
                        if ctrl.get("allow_cancel", True):
                            self.cancel()
                            return
                        else:
                            print_warning("Cancel is disabled in your config.")
                    elif line in ("s", "snooze"):
                        if ctrl.get("allow_snooze", True):
                            self.snooze()
                        else:
                            print_warning("Snooze is disabled in your config.")
                except (EOFError, KeyboardInterrupt):
                    return

        t = threading.Thread(target=_listen, daemon=True)
        t.start()


# ── Convenience function ──────────────────────────────────────────────────────

def run_countdown(cfg: dict, target_dt: datetime) -> bool:
    """
    Run the full warning countdown.
    Returns True if the action should proceed, False if cancelled.
    """
    engine = CountdownEngine(cfg, target_dt)
    return engine.run()
