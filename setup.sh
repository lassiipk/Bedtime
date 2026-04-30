#!/usr/bin/env bash
# setup.sh — Bedtime setup for macOS and Linux
# Usage: bash setup.sh

echo ""
echo "🌙  Bedtime Setup (macOS / Linux)"
echo "──────────────────────────────────"
echo ""

# ── Find Python 3 ─────────────────────────────────────────────────────────────
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        VERSION=$("$cmd" --version 2>&1)
        # Require 3.8+
        MAJOR=$("$cmd" -c "import sys; print(sys.version_info.major)")
        MINOR=$("$cmd" -c "import sys; print(sys.version_info.minor)")
        if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 8 ]; then
            PYTHON="$cmd"
            echo "✔  Found: $VERSION"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "✖  Python 3.8+ is required but not found."
    echo ""
    echo "   Install it with your package manager:"
    echo "     macOS:  brew install python3"
    echo "     Ubuntu: sudo apt install python3"
    echo "     Fedora: sudo dnf install python3"
    exit 1
fi

# ── Run Python setup ──────────────────────────────────────────────────────────
echo ""
echo "→  Running Python setup script..."
echo ""
"$PYTHON" setup.py
