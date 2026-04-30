#!/usr/bin/env bash
# teardown.sh — Bedtime teardown for macOS and Linux
# Usage: bash teardown.sh

echo ""
echo "🌙  Bedtime Teardown (macOS / Linux)"
echo "──────────────────────────────────────"
echo ""

PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        PYTHON="$cmd"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "⚠  Python not found. Attempting manual cleanup..."

    # Remove crontab entry
    if crontab -l 2>/dev/null | grep -q "bedtime-managed"; then
        crontab -l | grep -v "bedtime-managed" | crontab -
        echo "✔  Crontab entry removed."
    fi

    # Remove launchd plist (macOS)
    PLIST="$HOME/Library/LaunchAgents/com.lassiipk.bedtime.plist"
    if [ -f "$PLIST" ]; then
        launchctl unload "$PLIST" 2>/dev/null
        rm -f "$PLIST"
        echo "✔  launchd agent removed."
    fi

    echo "⚠  Could not remove config files (Python required)."
    exit 0
fi

"$PYTHON" teardown.py
