# 🌙 Bedtime — Guide

This guide explains everything from scratch. What the files are, how to set it up, how to use it, and how to remove it.

---

## What is Bedtime?

Bedtime is a tool that runs on your computer and automatically performs an action — like shutting down your PC — at a time you choose.

Before it does anything, it **warns you** so you have time to save your work. You can also **cancel** or **snooze** the action if you're not ready.

---

## Understanding the Folder Structure

When you clone or download Bedtime, this is what you'll see:

```
bedtime/
│
├── 📄 bedtime.config.yaml     ← YOUR config file. This is where you set the time,
│                                 the action, the warnings, etc. You edit this.
│
├── 📄 README.md               ← Short overview of the project (for GitHub)
├── 📄 requirements.txt        ← List of Python packages Bedtime needs
│
├── ⚙️  setup.py               ← Run this ONCE to activate Bedtime on your PC
├── ⚙️  setup.sh               ← Same as setup.py but for macOS/Linux terminal shortcut
├── ⚙️  setup.ps1              ← Same as setup.py but for Windows PowerShell shortcut
│
├── 🗑️  teardown.py            ← Run this to completely REMOVE Bedtime from your PC
├── 🗑️  teardown.sh            ← Same as teardown.py but for macOS/Linux terminal shortcut
├── 🗑️  teardown.ps1           ← Same as teardown.py but for Windows PowerShell shortcut
│
└── src/                       ← The actual code. You don't need to touch anything in here.
    ├── main.py                ← The brain — handles all commands
    ├── config.py              ← Reads and checks your config file
    ├── countdown.py           ← Runs the warning countdown before the action
    ├── actions.py             ← Knows how to shut down, restart, sleep, etc.
    ├── notifications.py       ← Sends pop-ups, terminal messages, and sounds
    ├── scheduler.py           ← Registers the task with Windows/macOS/Linux
    ├── wizard.py              ← The setup wizard (when you run `init`)
    └── utils.py               ← Small helper functions used everywhere
```

### The simple rule:
- **You only ever interact with 3 things:**
  1. `bedtime.config.yaml` — to change your settings
  2. `setup.py` — to activate Bedtime
  3. `teardown.py` — to remove Bedtime
- **Everything inside `src/` is the engine. Leave it alone.**

---

## Step 1 — Requirements

You need **Python 3.8 or newer** installed on your computer.

**Check if you have it:**

Open a terminal (Command Prompt / PowerShell on Windows, Terminal on macOS/Linux) and type:

```bash
python --version
```

You should see something like `Python 3.11.2`. If you see an error or a version below 3.8, download Python from [python.org](https://www.python.org/downloads/).

---

## Step 2 — Download Bedtime

**Option A — Using Git (recommended):**

```bash
git clone https://github.com/lassiipk/bedtime.git
cd bedtime
```

**Option B — Download ZIP:**

Go to the GitHub page → click **Code** → **Download ZIP** → extract it → open the folder.

---

## Step 3 — Set Up Your Config

Open `bedtime.config.yaml` in any text editor (Notepad, VS Code, anything).

This is what it looks like:

```yaml
schedule:
  time: "22:00"      ← Change this to the time you want (24-hour format)
  mode: daily        ← "daily" = every day, "once" = one time only
  days:
    - Mon
    - Tue            ← Remove days you don't want it to run
    - Wed
    - Thu
    - Fri
    - Sat
    - Sun

action:
  action: shutdown   ← What to do: shutdown / restart / sleep / logoff / lock / custom

warnings:
  enabled: true
  intervals:
    - 300            ← Warn 300 seconds (5 minutes) before
    - 60             ← Warn 60 seconds (1 minute) before
    - 5              ← Warn 5 seconds before
  message: "Your PC will {action} in {time_left}. Please save your work!"

notifications:
  popup: true        ← Show a pop-up notification?
  terminal: true     ← Print a message in the terminal?
  sound: true        ← Play a sound?

control:
  allow_cancel: true     ← Can the user cancel the action?
  allow_snooze: true     ← Can the user snooze the action?
  snooze_duration: 300   ← How many seconds does a snooze delay the action?
  max_snoozes: 3         ← How many times can the user snooze?
```

**Save the file after editing.**

---

## Step 4 — Activate Bedtime (Run Setup)

Open a terminal in the `bedtime` folder and run:

**Windows:**
```bash
python setup.py
```
or in PowerShell:
```powershell
.\setup.ps1
```

**macOS / Linux:**
```bash
python3 setup.py
```
or:
```bash
bash setup.sh
```

### What setup does:
1. Checks your Python version is OK
2. Installs the required packages automatically (PyYAML, rich, etc.)
3. Reads your `bedtime.config.yaml`
4. Checks for any mistakes in your config
5. Registers Bedtime with your operating system's scheduler
6. Tells you when the next action will run

After setup, **you don't need to keep a terminal open**. Bedtime is now registered with your OS and will run automatically at the scheduled time, even after a reboot.

---

## Step 5 — How It Works at Runtime

When the scheduled time approaches, here is exactly what happens:

```
Example: You set time = 22:00, intervals = [300, 60, 5]

21:55:00 → ⚠️  WARNING: "Your PC will shutdown in 5 minutes. Please save your work!"
           Pop-up appears + sound plays + terminal message prints
           You can type C (cancel) or S (snooze) in the terminal

21:59:00 → ⚠️  WARNING: "Your PC will shutdown in 1 minute. Please save your work!"
           Same notifications again

21:59:55 → ⚠️  WARNING: "Your PC will shutdown in 5 seconds. Please save your work!"
           Same notifications again

22:00:00 → 💤  PC shuts down
```

---

## Using the CLI Commands

You can also control Bedtime manually from the terminal. Always run these from inside the `bedtime` folder.

---

### Check current status

See what's scheduled and when the next run is:

```bash
python src/main.py status
```

Output looks like:
```
  Action       shutdown
  Time         22:00
  Mode         daily
  Days         Mon, Tue, Wed, Thu, Fri, Sat, Sun
  Next run     2026-05-01 22:00  (3 hours from now)
  Registered   ✔ Yes
  Warnings at  300s, 60s, 5s
```

---

### Test it without waiting

Run the countdown and action right now (great for testing your config):

```bash
python src/main.py run
```

This will start the warning countdown immediately and then execute the action. Use this to make sure your warnings look right before relying on it at night.

---

### Skip tonight's action (one-time cancel)

If you want to stay up late and skip just tonight:

```bash
python src/main.py cancel
```

This creates a skip flag for today only. Tomorrow night, Bedtime runs as normal.

---

### Open the config in your editor

```bash
python src/main.py edit
```

Opens `bedtime.config.yaml` directly in your default text editor.

---

### Run the setup wizard

If you want to redo your config step by step with prompts:

```bash
python src/main.py init
```

This asks you questions and writes a fresh `bedtime.config.yaml` for you. Then run `python setup.py` again to apply the new config.

---

## Changing Your Settings

Whenever you want to change anything (the time, the action, the warning intervals, anything):

1. Open `bedtime.config.yaml` and edit it
2. Run `python setup.py` again

Setup re-registers the task with the new settings. You don't need to run teardown first.

---

## Removing Bedtime Completely

To uninstall Bedtime and remove everything:

**Windows:**
```bash
python teardown.py
```
or in PowerShell:
```powershell
.\teardown.ps1
```

**macOS / Linux:**
```bash
python3 teardown.py
```
or:
```bash
bash teardown.sh
```

### What teardown does:
1. Cancels and removes the scheduled task from your OS
2. **Asks you** whether to delete your config file (default is **keep it**)
3. Asks if you want to uninstall the Python packages too
4. Confirms everything is done

> **Tip:** If you say N to deleting the config, your settings are preserved. You can re-activate Bedtime at any time by running `python setup.py` again — no reconfiguring needed.

**Teardown is safe to run multiple times.** If Bedtime is already removed, it just says "nothing found" and exits cleanly.

---

## Common Examples

### Shutdown every weeknight at 11 PM

```yaml
schedule:
  time: "23:00"
  mode: daily
  days: [Mon, Tue, Wed, Thu, Fri]

action:
  action: shutdown
```

---

### Restart once on a specific date

```yaml
schedule:
  time: "03:00"
  mode: once
  date: "2026-06-01"

action:
  action: restart
```

---

### Lock the screen with no warnings

```yaml
schedule:
  time: "22:30"
  mode: daily

action:
  action: lock

warnings:
  enabled: false
```

---

### Run a custom backup script before sleeping

```yaml
action:
  action: custom
  custom_command: "python C:/Users/you/scripts/backup.py"

warnings:
  message: "Backup + sleep in {time_left}. Save your work!"
```

---

### Disable snooze but allow cancel

```yaml
control:
  allow_cancel: true
  allow_snooze: false
```

---

## Cancelling During a Warning

When a warning appears, if `allow_cancel` or `allow_snooze` are enabled, type into the terminal:

| Type this | What happens                        |
|-----------|-------------------------------------|
| `c`       | Cancels tonight's action            |
| `cancel`  | Same as `c`                         |
| `s`       | Snoozes — delays by `snooze_duration` seconds |
| `snooze`  | Same as `s`                         |

---

## Troubleshooting

**"No config file found"**
→ You haven't created a config yet. Run `python src/main.py init` to make one.

**"Command not found: python"**
→ Try `python3` instead of `python`. Or check that Python is installed.

**"Config validation failed"**
→ You have a typo in `bedtime.config.yaml`. Read the error — it tells you exactly which field is wrong.

**"Task registered but nothing happened at the scheduled time"**
→ Make sure your PC was on and not in sleep mode at the scheduled time. Also check the time format in your config is correct (use 24h format, e.g. `22:00` not `10:00`).

**Pop-up notifications not appearing on Linux**
→ Make sure `libnotify` is installed: `sudo apt install libnotify-bin`

**Sound not playing**
→ Check your system volume. If you have a custom sound file set, make sure the path is correct and the file exists.

---

## Quick Reference Card

```
FIRST TIME SETUP
────────────────
1. Edit bedtime.config.yaml     ← set your time and action
2. python setup.py              ← activates Bedtime

DAILY USE
─────────
python src/main.py status       ← check what's scheduled
python src/main.py cancel       ← skip tonight
python src/main.py edit         ← open config

CHANGE SETTINGS
───────────────
1. Edit bedtime.config.yaml
2. python setup.py              ← apply changes

REMOVE BEDTIME
──────────────
python teardown.py              ← removes everything
```

---

*Bedtime v1.0 — github.com/lassiipk/bedtime*
