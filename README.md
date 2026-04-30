# 🌙 Bedtime

> Schedule your PC to shut down, restart, sleep, or run any custom command — at the exact time you choose. With warnings.

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## What it does

Bedtime lets you schedule a system action (shutdown, restart, sleep, etc.) at a time you set. Before the action runs, it warns you at your chosen intervals — via pop-up, terminal message, and sound — so you have time to save your work. You can cancel or snooze right from the notification.

Everything is controlled by a config file. **Nothing is hardcoded.**

---

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/lassiipk/bedtime.git
cd bedtime
```

### 2. Run setup

**Windows:**
```powershell
.\setup.ps1
# or
python setup.py
```

**macOS / Linux:**
```bash
bash setup.sh
# or
python3 setup.py
```

Setup will:
- Check your Python version
- Install dependencies
- Run the interactive wizard (if no config exists)
- Register the task with your OS scheduler

### 3. Done

Bedtime is now active. Your PC will run the configured action at the scheduled time, with warnings.

---

## Configuration

Edit `bedtime.config.yaml` (created by the wizard, or copy from below):

```yaml
schedule:
  time: "22:00"        # HH:MM (24h) or HH:MM AM/PM
  mode: daily          # daily | once
  days:                # ignored when mode is "once"
    - Mon
    - Tue
    - Wed
    - Thu
    - Fri
    - Sat
    - Sun
  date: ""             # YYYY-MM-DD, only used when mode is "once"

action:
  action: shutdown     # shutdown | restart | sleep | logoff | lock | custom
  custom_command: ""   # required when action is "custom"

warnings:
  enabled: true
  intervals:           # seconds before action to warn (e.g. 300 = 5 min)
    - 300
    - 60
    - 5
  message: "Your PC will {action} in {time_left}. Please save your work!"

notifications:
  popup: true          # GUI pop-up
  terminal: true       # print to terminal
  sound: true          # play a sound
  sound_file: ""       # path to .wav/.mp3, leave empty for system beep

control:
  allow_cancel: true   # user can cancel during countdown
  allow_snooze: true   # user can snooze during countdown
  snooze_duration: 300 # seconds to delay when snoozing
  max_snoozes: 3       # max number of snoozes allowed
```

After editing, re-run `python setup.py` to apply changes.

---

## Supported Config Formats

Bedtime reads whichever format you prefer. Priority: **YAML > JSON > INI**

| File                      | Format |
|---------------------------|--------|
| `bedtime.config.yaml`     | YAML   |
| `bedtime.config.json`     | JSON   |
| `bedtime.config.ini`      | INI    |

---

## Supported Actions

| Action    | What it does                        |
|-----------|-------------------------------------|
| `shutdown`  | Shuts down the computer           |
| `restart`   | Restarts the computer             |
| `sleep`     | Puts the computer to sleep        |
| `logoff`    | Logs off the current user         |
| `lock`      | Locks the screen                  |
| `custom`    | Runs your own command or script   |

---

## CLI Commands

```bash
python src/main.py init        # Run the setup wizard
python src/main.py status      # Show current schedule and next run time
python src/main.py run         # Manually trigger countdown + action (for testing)
python src/main.py cancel      # Skip today's action (one-time)
python src/main.py edit        # Open config in your text editor
```

---

## Warning Message Placeholders

| Placeholder    | Example output        |
|----------------|-----------------------|
| `{action}`     | `shutdown`            |
| `{time_left}`  | `5 minutes`           |
| `{time}`       | `22:00`               |

---

## Cancel & Snooze

During the warning countdown, you can type in the terminal:

- **`c`** or **`cancel`** — Skip today's action
- **`s`** or **`snooze`** — Delay the action by `snooze_duration` seconds

Both options can be turned on/off in the config. When `allow_snooze` is enabled, a user can snooze up to `max_snoozes` times.

---

## Remove Bedtime

**Windows:**
```powershell
.\teardown.ps1
# or
python teardown.py
```

**macOS / Linux:**
```bash
bash teardown.sh
# or
python3 teardown.py
```

Teardown will:
- Cancel all scheduled tasks
- Delete your config file
- Optionally uninstall dependencies

---

## Requirements

- Python 3.8 or higher
- Dependencies (auto-installed by setup): `PyYAML`, `questionary`, `rich`, `plyer`

---

## Platform Details

| OS      | Scheduler Used     |
|---------|--------------------|
| Windows | Task Scheduler     |
| macOS   | launchd            |
| Linux   | cron               |

---

## License

MIT — see [LICENSE](LICENSE)
