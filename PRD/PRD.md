# Bedtime — Product Requirements Document

**GitHub:** [lassiipk/bedtime](https://github.com/lassiipk/bedtime)  
**Version:** v1.0  
**Status:** Draft  
**Author:** lassiipk  
**Last Updated:** 2026-04-29

---

## Table of Contents

1. [Overview](#1-overview)
2. [Goals & Non-Goals](#2-goals--non-goals)
3. [User Personas](#3-user-personas)
4. [How It Works — Big Picture](#4-how-it-works--big-picture)
5. [Supported Platforms](#5-supported-platforms)
6. [Supported Actions](#6-supported-actions)
7. [Configuration System](#7-configuration-system)
8. [Warning & Notification System](#8-warning--notification-system)
9. [Scheduling System](#9-scheduling-system)
10. [Setup & Teardown](#10-setup--teardown)
11. [Cancel & Snooze](#11-cancel--snooze)
12. [Tech Stack](#12-tech-stack)
13. [File & Folder Structure](#13-file--folder-structure)
14. [CLI Reference](#14-cli-reference)
15. [Error Handling](#15-error-handling)
16. [Future Ideas (Out of Scope for v1.0)](#16-future-ideas-out-of-scope-for-v10)

---

## 1. Overview

**Bedtime** is a cross-platform, fully configurable PC automation tool. It lets users schedule system-level actions — like shutdown, restart, or sleep — at a specific time. Before the action runs, it warns the user through multiple channels so they have time to save their work.

Everything in Bedtime is controlled by a config file. Nothing is hardcoded. The user decides the action, the time, the warning intervals, the warning messages, the notification style, and whether they can snooze or cancel.

Bedtime is set up by running a single setup script and can be completely removed by running a teardown script.

---

## 2. Goals & Non-Goals

### Goals

- Let users schedule any supported system action at a specific time.
- Warn the user before the action runs — at custom time intervals they define.
- Support one-time and recurring (daily) schedules.
- Work on Windows, macOS, and Linux.
- Be fully configured through a file — no hardcoded values anywhere.
- Be installable via a single setup script and completely removable via a teardown script.
- Allow the user to cancel or snooze an action during the warning countdown (configurable).

### Non-Goals

- No cloud sync or remote control in v1.0.
- No built-in GUI settings editor in v1.0 (config is edited in a file).
- No support for multiple simultaneous scheduled tasks in v1.0 (one active schedule at a time).
- No mobile support.

---

## 3. User Personas

### The Night-Owl Developer
Forgets to shut down their PC before going to bed. Wants their machine to shut down at 11 PM every night and be warned 10 minutes before so they can save their work.

### The Cautious Power User
Wants full control. Uses a custom command (e.g. a backup script) before sleep and wants to be able to snooze the action if they're still busy.

### The Sysadmin
Wants to set up Bedtime on multiple machines quickly using a config file, then roll it back cleanly with a teardown script.

---

## 4. How It Works — Big Picture

```
User edits bedtime.config
        │
        ▼
User runs setup script (setup.sh / setup.ps1 / setup.py)
        │
        ▼
Bedtime registers a scheduled task with the OS scheduler
(Task Scheduler on Windows, cron/launchd on macOS/Linux)
        │
        ▼
At the scheduled time, Bedtime starts the warning countdown
        │
        ├── Sends warnings at each interval defined in config
        │   (pop-up, terminal message, sound)
        │
        ├── User can cancel or snooze (if enabled in config)
        │
        ▼
Bedtime executes the configured action
(shutdown / restart / sleep / logoff / lock / custom command)
        │
        ▼
User runs teardown script to remove everything
```

---

## 5. Supported Platforms

| Platform | OS Scheduler Used         | Notes                          |
|----------|---------------------------|--------------------------------|
| Windows  | Task Scheduler            | Uses `schtasks` or PowerShell  |
| macOS    | launchd                   | Uses `.plist` files            |
| Linux    | cron                      | Uses `crontab`                 |

The same `bedtime.config` file works on all three platforms. The setup script detects the OS and registers the task appropriately.

---

## 6. Supported Actions

The user picks one of these actions in the config file:

| Action Key         | What It Does                              |
|--------------------|-------------------------------------------|
| `shutdown`         | Shuts down the computer                   |
| `restart`          | Restarts the computer                     |
| `sleep`            | Puts the computer to sleep / hibernate    |
| `logoff`           | Logs off the current user                 |
| `lock`             | Locks the screen                          |
| `custom`           | Runs a user-defined command or script     |

When `action` is set to `custom`, the user must also provide a `custom_command` value in the config.

---

## 7. Configuration System

### Overview

Bedtime supports **four ways** to configure it. All of them ultimately produce or modify the same `bedtime.config` file, which is the single source of truth.

| Method               | How It Works                                                    |
|----------------------|-----------------------------------------------------------------|
| `.ini` / `.txt` file | User manually edits `bedtime.config` in a text editor          |
| `JSON` file          | User edits `bedtime.config.json` (alternative format)          |
| `YAML` file          | User edits `bedtime.config.yaml` (alternative format)          |
| Interactive CLI      | User runs `bedtime init` and answers prompts; config is generated automatically |

> At runtime, Bedtime reads whichever format is present. If multiple formats exist, priority is: `YAML > JSON > INI`.

---

### Config Fields

Below is the full list of config fields. Every field is optional and has a default value so the tool always works even with a minimal config.

#### `[schedule]` — When to run

| Field         | Type     | Default       | Description                                                  |
|---------------|----------|---------------|--------------------------------------------------------------|
| `time`        | string   | `"22:00"`     | Time to run the action. Format: `HH:MM` (24hr) or `HH:MM AM/PM` |
| `mode`        | string   | `"daily"`     | `"daily"` = every day, `"once"` = run one time only          |
| `days`        | list     | all days      | Only used when `mode` is `daily`. e.g. `["Mon","Tue","Wed"]` |
| `date`        | string   | none          | Only used when `mode` is `"once"`. Format: `YYYY-MM-DD`      |

#### `[action]` — What to do

| Field            | Type   | Default      | Description                                              |
|------------------|--------|--------------|----------------------------------------------------------|
| `action`         | string | `"shutdown"` | One of: `shutdown`, `restart`, `sleep`, `logoff`, `lock`, `custom` |
| `custom_command` | string | none         | Required if `action` is `"custom"`. The command to run.  |

#### `[warnings]` — The countdown

| Field              | Type    | Default              | Description                                                     |
|--------------------|---------|----------------------|-----------------------------------------------------------------|
| `enabled`          | bool    | `true`               | Turn warnings on or off entirely                                |
| `intervals`        | list    | `[300, 60, 5]`       | List of seconds before action to send a warning. e.g. `300` = 5 min warning |
| `message`          | string  | `"PC will {action} in {time_left}. Save your work!"` | Warning message template. `{action}` and `{time_left}` are replaced automatically |

#### `[notifications]` — How to warn

| Field         | Type | Default | Description                        |
|---------------|------|---------|------------------------------------|
| `popup`       | bool | `true`  | Show a GUI pop-up notification     |
| `terminal`    | bool | `true`  | Print warning to terminal/CLI      |
| `sound`       | bool | `true`  | Play a sound alert                 |
| `sound_file`  | str  | built-in beep | Path to a custom `.wav` or `.mp3` file to play |

#### `[control]` — User control during countdown

| Field              | Type | Default | Description                                              |
|--------------------|------|---------|----------------------------------------------------------|
| `allow_cancel`     | bool | `true`  | Show a Cancel button/option during the countdown         |
| `allow_snooze`     | bool | `true`  | Show a Snooze button/option during the countdown         |
| `snooze_duration`  | int  | `300`   | How many seconds to snooze (delay the action)            |
| `max_snoozes`      | int  | `3`     | Maximum number of times the user can snooze              |

---

### Example Config (YAML)

```yaml
schedule:
  time: "22:00"
  mode: daily
  days: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

action:
  action: shutdown

warnings:
  enabled: true
  intervals: [300, 60, 5]
  message: "Your PC will {action} in {time_left}. Please save your work!"

notifications:
  popup: true
  terminal: true
  sound: true
  sound_file: ""

control:
  allow_cancel: true
  allow_snooze: true
  snooze_duration: 300
  max_snoozes: 3
```

### Example Config (INI)

```ini
[schedule]
time = 22:00
mode = daily
days = Mon,Tue,Wed,Thu,Fri,Sat,Sun

[action]
action = shutdown

[warnings]
enabled = true
intervals = 300,60,5
message = Your PC will {action} in {time_left}. Please save your work!

[notifications]
popup = true
terminal = true
sound = true
sound_file =

[control]
allow_cancel = true
allow_snooze = true
snooze_duration = 300
max_snoozes = 3
```

---

## 8. Warning & Notification System

### How It Works

When the scheduled time approaches, Bedtime calculates all warning trigger points based on the `intervals` list. For example, if the action is at 22:00 and intervals are `[300, 60, 5]`, warnings fire at 21:55, 21:59, and 21:59:55.

At each warning point, Bedtime delivers all enabled notification types simultaneously.

### Notification Types

**Pop-up (GUI)**
A native OS notification or dialog box appears with the warning message. On Windows this uses `win10toast` or `tkinter`. On macOS it uses `osascript`. On Linux it uses `notify-send`.

**Terminal / CLI**
A message is printed to the terminal if one is open, or to a log file if no terminal is attached.

**Sound**
A sound is played. If `sound_file` is empty, a built-in system beep is used. If a path is provided, that audio file is played.

### Message Template

The `message` field supports these placeholders:

| Placeholder    | Replaced With                        |
|----------------|--------------------------------------|
| `{action}`     | The name of the action (e.g. "shutdown") |
| `{time_left}`  | Human-readable time left (e.g. "5 minutes", "1 minute", "5 seconds") |
| `{time}`       | The exact scheduled time (e.g. "22:00") |

---

## 9. Scheduling System

### One-Time Schedule (`mode: once`)

The action runs once on a specific `date` at the specified `time`. After it runs, the scheduled task is automatically removed.

### Recurring Daily Schedule (`mode: daily`)

The action runs every day (or on specified `days`) at the given `time`. The task stays registered with the OS scheduler until the user runs the teardown script.

### OS Scheduler Integration

Bedtime does not implement its own background daemon. It registers a task with the native OS scheduler:

| OS      | Method                              |
|---------|-------------------------------------|
| Windows | `schtasks` / Task Scheduler XML     |
| macOS   | `launchd` `.plist` in `~/Library/LaunchAgents/` |
| Linux   | `crontab` entry                     |

This means Bedtime works even after a reboot without any manual intervention.

---

## 10. Setup & Teardown

### Setup

Running the setup script does the following:

1. Detects the operating system.
2. Checks for required dependencies and installs them if missing.
3. Reads `bedtime.config` (or generates one via interactive CLI if none exists).
4. Validates the config — shows clear errors for any invalid values.
5. Registers the scheduled task with the OS scheduler.
6. Confirms success with a message showing when the next action will run.

**Setup scripts:**

| Platform      | Script              |
|---------------|---------------------|
| Windows       | `setup.ps1`         |
| macOS / Linux | `setup.sh`          |
| Any platform  | `setup.py` (Python) |

### Teardown

Running the teardown script does the following:

1. Cancels all scheduled Bedtime tasks from the OS scheduler.
2. Deletes the `bedtime.config` file (and all format variants).
3. Removes any installed Bedtime dependencies (if they were installed by setup).
4. Confirms that everything has been cleanly removed.

**Teardown scripts:**

| Platform      | Script                |
|---------------|-----------------------|
| Windows       | `teardown.ps1`        |
| macOS / Linux | `teardown.sh`         |
| Any platform  | `teardown.py` (Python)|

> The teardown script must be safe to run multiple times (idempotent). Running it when nothing is installed should not crash — it should just report that nothing was found.

---

## 11. Cancel & Snooze

Both cancel and snooze are **optional** and controlled by the config. The user can turn either or both off.

### Cancel

If `allow_cancel` is `true`, when a warning notification appears, the user sees a **Cancel** option. Clicking/pressing it cancels the scheduled action for that session. The recurring schedule remains active (next day it will run again unless cancelled again).

### Snooze

If `allow_snooze` is `true`, the user sees a **Snooze** option. Clicking it delays the action by `snooze_duration` seconds. The warning countdown restarts from the snooze point. The user can snooze up to `max_snoozes` times. After that, the snooze option disappears and the action will run.

### Snooze vs Cancel Summary

| Feature    | What it does                              | Resets next day? |
|------------|-------------------------------------------|------------------|
| Cancel     | Skips the action for today                | Yes              |
| Snooze     | Delays the action by `snooze_duration`    | Yes              |

---

## 12. Tech Stack

**Recommended: Python**

Python is chosen because it works natively on Windows, macOS, and Linux, has libraries for all needed features, and produces clean CLI tools.

| Need                        | Library / Tool                    |
|-----------------------------|-----------------------------------|
| Config parsing (YAML)       | `PyYAML`                          |
| Config parsing (JSON)       | Built-in `json`                   |
| Config parsing (INI)        | Built-in `configparser`           |
| Interactive CLI wizard      | `questionary` or `rich`           |
| GUI pop-up notifications    | `plyer` (cross-platform)          |
| Sound playback              | `playsound` or `pygame`           |
| OS scheduler registration   | `subprocess` + OS-native commands |
| Terminal output / styling   | `rich`                            |
| Packaging / distribution    | `pipx` or standalone scripts      |

> The setup and teardown scripts are provided in both `.sh` (macOS/Linux) and `.ps1` (Windows) for users who prefer not to use Python directly. The Python `setup.py` / `teardown.py` versions work on all platforms.

---

## 13. File & Folder Structure

```
bedtime/
│
├── README.md                  # How to install and use Bedtime
├── PRD.md                     # This document
│
├── bedtime.config.yaml        # User config (YAML format)
├── bedtime.config.json        # User config (JSON format, alternative)
├── bedtime.config.ini         # User config (INI format, alternative)
│
├── setup.sh                   # Setup script for macOS / Linux
├── setup.ps1                  # Setup script for Windows
├── setup.py                   # Setup script for any platform (Python)
│
├── teardown.sh                # Teardown script for macOS / Linux
├── teardown.ps1               # Teardown script for Windows
├── teardown.py                # Teardown script for any platform (Python)
│
└── src/
    ├── main.py                # Entry point — runs the warning + action logic
    ├── config.py              # Config loader and validator
    ├── scheduler.py           # OS scheduler registration / removal
    ├── warnings.py            # Warning countdown logic
    ├── notifications.py       # Pop-up, terminal, and sound notifications
    ├── actions.py             # All system actions (shutdown, restart, etc.)
    └── utils.py               # Shared helpers (time formatting, OS detection, etc.)
```

---

## 14. CLI Reference

```
bedtime init              → Interactive wizard to generate config
bedtime status            → Show current schedule and next run time
bedtime run               → Manually trigger the warning + action now (for testing)
bedtime cancel            → Cancel today's scheduled action (one-time skip)
bedtime edit              → Open the config file in the default text editor
```

Setup and teardown are run as scripts, not CLI commands:

```
python setup.py           → Register Bedtime with the OS scheduler
python teardown.py        → Remove Bedtime completely
```

---

## 15. Error Handling

| Situation                                      | Behaviour                                                    |
|------------------------------------------------|--------------------------------------------------------------|
| Config file missing at setup                  | Prompt user to run `bedtime init` to create one              |
| Invalid config value (e.g. bad time format)   | Show a clear error message pointing to the exact field       |
| Action fails (e.g. shutdown is blocked by OS) | Log the error and show a notification to the user            |
| Teardown run when nothing is installed        | Print "Nothing to remove" and exit cleanly                   |
| Snooze limit reached                          | Hide snooze button, action proceeds at next warning          |
| `custom_command` is empty but action is `custom` | Show an error at setup time, refuse to register the task |
| Sound file path is invalid                    | Fall back to built-in system beep, log a warning             |

---

## 16. Future Ideas (Out of Scope for v1.0)

These are ideas that came up but are intentionally left out of v1.0 to keep the scope focused.

- **Multiple schedules** — run different actions at different times (e.g. lock at 11 PM, shutdown at midnight).
- **GUI settings editor** — a graphical app to edit the config without touching the file.
- **Remote control** — cancel or snooze from your phone.
- **Inactivity detection** — only run the action if the user has been inactive for N minutes.
- **Pre-action script** — run a custom command (e.g. save backup) before the main action.
- **Notification history log** — keep a log of all warnings and actions taken.
- **Dark/light mode pop-ups** — match the OS theme in GUI notifications.

---

*Bedtime v1.0 — lassiipk/bedtime*
