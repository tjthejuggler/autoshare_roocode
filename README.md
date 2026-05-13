# Autoshare Roo Code

Watches files for tasks and automatically sends them to Roo Code in the correct VSCode window.

## How It Works

1. **Multi-Source File Watcher**: Monitors multiple files simultaneously using `inotifywait` (one thread per source)
2. **Lock Check**: Only processes when the screen is unlocked (uses `loginctl` / DBus)
3. **Format-Specific Parsing**: Supports markdown (project name from first word) and JSON (project name from config)
4. **Window Matching**: Finds the VSCode window whose title contains the project name (case-insensitive) using `wmctrl`
5. **Roo Code Automation**: Uses the VSCode command palette via `xdotool` to run "Roo Code: New Task", then pastes the task text and submits it

## No Image Recognition Needed!

The key insight is that Roo Code registers VSCode commands accessible via the command palette:
- `Roo Code: New Task` — opens the sidebar, starts a new task, and focuses the input
- `Roo Code: Focus Input Field` — opens the sidebar and focuses the input

This means we can drive everything through keyboard shortcuts (`Ctrl+Shift+P` → type command → Enter) instead of needing screenshots and image matching.

## Watch Sources

All watched files are configured in [`config.py`](config.py) via the `WATCH_SOURCES` list. Each entry specifies a file path, format, and (for JSON) the project name:

```python
WATCH_SOURCES = [
    {
        "path": "~/noteVault/RooCode_jobs.md",
        "format": "markdown",
        "project": None,  # Extracted from first word of each item
    },
    {
        "path": "/home/twain/habitsdb/Wags_debug/debug_wags.json",
        "format": "json",
        "project": "wags",
    },
    # Add more sources here by copying the pattern:
    # {
    #     "path": "/path/to/debug_otherproject.json",
    #     "format": "json",
    #     "project": "otherproject",
    # },
]
```

To add a new source, just copy an existing entry and change the values.

## File Formats

### Markdown Format

The watched markdown file uses empty lines to separate items. Each item's first word is the project name (must match a VSCode window title), and the rest is the task to send:

```
%current_roocodejobs

myproject Fix the login button styling on the homepage

other-project Refactor the database connection pool to use async

myproject Add unit tests for the payment module
```

- Lines starting with `%` or `#` are treated as comments/markers and ignored
- After processing, the item is removed from the jobs file automatically
- Completed jobs are appended to `RooCode_jobs_completed.md` with a timestamp
- Jobs that can't find a matching VSCode window are moved to `RooCode_jobs_undone.md` with a timestamp (so they don't block the queue)

### JSON Format

JSON watch files contain a `notes` array. Each note is sent as a separate Roo Code task. The project name comes from the `WATCH_SOURCES` config (not from the JSON itself). Example:

```json
{
  "notes": [
    {
      "id": "1776902305334",
      "timestamp": "2026-04-22 19:58:25",
      "screenRoute": "settings",
      "screenLabel": "Settings",
      "sourceFile": "ui/settings/SettingsScreen.kt",
      "sourceFunctions": "SettingsScreen, SettingsViewModel",
      "noteType": "BUG",
      "noteText": "The watch icon should be black and white"
    }
  ]
}
```

Each note is formatted into a task with full location info so Roo Code knows exactly where to look:

```
[BUG] The watch icon should be black and white
Location: ui/settings/SettingsScreen.kt → SettingsScreen, SettingsViewModel
Screen: Settings
```

- All notes in the array are processed (not just the first one)
- After processing, the `notes` array is cleared in the JSON file
- Completed/undone notes are saved in the **same JSON format** (with an added `_processed` timestamp), so you can copy-paste notes back into the original file to retry:
  ```json
  {
    "notes": [
      {
        "id": "1776902305334",
        "noteType": "BUG",
        "noteText": "The watch icon should be black and white",
        "sourceFile": "ui/settings/SettingsScreen.kt",
        "sourceFunctions": "SettingsScreen, SettingsViewModel",
        "_processed": "2026-04-25 09:09:02"
      }
    ]
  }
  ```

## Requirements

- **Python 3.12+**
- **inotify-tools** — `sudo apt install inotify-tools`
- **xdotool** — `sudo apt install xdotool`
- **wmctrl** — `sudo apt install wmctrl`
- **xclip** — `sudo apt install xclip`
- **VSCode** with the **Roo Code** extension installed

## Setup

```bash
# Run the watcher (watches all sources in config.py)
. venv/bin/activate && python autoshare.py

# Process all sources once and exit (no watching)
python autoshare.py --once

# Verbose mode
python autoshare.py -v
```

## Configuration

Edit [`config.py`](config.py) to adjust:
- `WATCH_SOURCES` — list of files to watch with format and project name
- `REMOVE_AFTER_PROCESS` — whether to remove items after processing (default: `True`)
- `INTER_SUBMIT_DELAY` — seconds between submissions to different projects (default: `60`). Prevents multiple projects from fighting over window focus at startup.
- Timing delays for window activation, command palette, pasting, etc.

## How It Finds the Right VSCode Window

VSCode window titles look like: `filename - project_name - Visual Studio Code`

For markdown items, the project name is the first word of the item. For JSON sources, the project name comes from the `WATCH_SOURCES` config. The script matches the project name against window titles case-insensitively. So if your item starts with `MyProject`, it will match a window titled `README.md - MyProject - Visual Studio Code`.

## Output Files

When a job is completed, it's appended to a `_completed` sibling file in the same directory:
```
[2026-04-15 16:14:25] Tail
In the settings screen we can choose a notes file...
```

When a job can't find a matching VSCode window, it's moved to an `_undone` sibling file so it doesn't block the queue:
```
[2026-04-15 16:20:00] nonexistent-project
Some task for a project that isn't open
```

## Troubleshooting

- **"No VSCode window found"**: Make sure the project name matches the folder name opened in VSCode. Check with `wmctrl -l` to see window titles. The job will be moved to the `_undone` file so it doesn't block the queue.
- **Jobs not being picked up**: Check if a `%` or `#` comment line or a bad item is at the top of the file. These are now skipped automatically. Also check that the autoshare process is running (`ps aux | grep autoshare`).
- **Command palette doesn't find the command**: Make sure the Roo Code extension is installed and enabled. Run `code --list-extensions | grep roo` to verify.
- **Screen lock detection fails**: The script tries `loginctl`, then DBus freedesktop ScreenSaver, then GNOME ScreenSaver. If none work, it assumes unlocked (won't block tasks).
- **Paste doesn't work**: The script uses `xclip` for clipboard and `xdotool` for `Ctrl+V`. Make sure both are installed.

## Architecture

```
autoshare.py        — Main entry point: multi-source file watcher, markdown/JSON parsers, lock detection, orchestration
vscode_ctrl.py      — VSCode window management and Roo Code interaction (xdotool/wmctrl)
config.py           — Configuration constants (WATCH_SOURCES list, timing, etc.)
```

## Changelog

- **2026-05-13 05:41** — Fix: serialized submissions across all watch threads. When multiple projects have pending items at startup (e.g. after reboot), they now submit one at a time with a 60-second gap between each, preventing window-focus conflicts that caused all but one to fail. Controlled by `INTER_SUBMIT_DELAY` in config.py.
- **2026-04-25 09:25** — Fix: JSON `_completed`/`_undone` files now use the same `{"notes": [...]}` format as the original JSON, so notes can be copy-pasted back to retry. Each note gets a `_processed` timestamp. Previously these were plain text, making it impossible to easily re-queue items.
- **2026-04-24 20:55** — Multi-source architecture: `WATCH_SOURCES` list in config.py replaces single `DEFAULT_WATCH_FILE`. Added JSON format support for debug note files (e.g. Wags). Each source runs in its own thread. Easy to add new sources by copying an entry in the list.
- **2026-04-15 16:37** — Fix: all xdotool keystrokes now sent directly to the target window by ID (`xdotool key --window <id>` / `xdotool type --window <id>`), so commands go to the correct VSCode window even when multiple windows are open. Also added `xdotool windowfocus --sync` after `wmctrl` activation for reliable focus.
- **2026-04-15 16:15** — Bug fix: `%` and `#` comment/marker lines are now skipped during parsing (was blocking the queue). Failed jobs (no matching VSCode window) are moved to `_undone` file instead of blocking. Completed jobs are now logged to `_completed` file with timestamps. Process all available items per file change event (not just one).
- **2026-04-15** — Initial implementation. File watcher + command palette-based Roo Code automation.
