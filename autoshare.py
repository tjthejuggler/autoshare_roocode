#!/usr/bin/env python3
"""Autoshare Roo Code - Watch files for tasks and send them to Roo Code in VSCode.

When a watched file changes (and the screen is unlocked), this script reads
items from the file, extracts the project name, and sends the task text as a
new Roo Code task in the matching VSCode window.

Supports two file formats:
  - markdown: project name is the first word of each item
  - json: project name comes from the watch source config
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import config
import vscode_ctrl

logger = logging.getLogger("autoshare")


def is_screen_unlocked() -> bool:
    """Check if the screen is unlocked using loginctl or DBus screensaver."""
    # Method 1: loginctl session lock status
    try:
        result = subprocess.run(
            ["loginctl", "show-session", "-p", "Locked", "--value"],
            capture_output=True, text=True, timeout=5,
        )
        locked = result.stdout.strip().lower()
        if locked == "no":
            return True
        if locked == "yes":
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Method 2: DBus freedesktop ScreenSaver
    try:
        result = subprocess.run(
            [
                "dbus-send", "--print-reply", "--dest=org.freedesktop.ScreenSaver",
                "/org/freedesktop/ScreenSaver",
                "org.freedesktop.ScreenSaver.GetActive",
            ],
            capture_output=True, text=True, timeout=5,
        )
        if "boolean false" in result.stdout.lower():
            return True
        if "boolean true" in result.stdout.lower():
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Method 3: GNOME screensaver
    try:
        result = subprocess.run(
            [
                "dbus-send", "--print-reply",
                "--dest=org.gnome.ScreenSaver",
                "/org/gnome/ScreenSaver",
                "org.gnome.ScreenSaver.GetActive",
            ],
            capture_output=True, text=True, timeout=5,
        )
        if "boolean false" in result.stdout.lower():
            return True
        if "boolean true" in result.stdout.lower():
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # If we can't determine lock state, assume unlocked (don't block tasks)
    logger.warning("Cannot determine screen lock state, assuming unlocked")
    return True


# ---------------------------------------------------------------------------
# Markdown format parsing (original)
# ---------------------------------------------------------------------------

def parse_items(content: str) -> list[str]:
    """Parse markdown file content into empty-line-separated items, stripping whitespace.

    Lines starting with '%' or '#' are treated as comments/markers and removed
    from items. Items that become empty after stripping are discarded.
    """
    raw_items = content.split("\n\n")
    items = []
    for item in raw_items:
        lines = [
            line for line in item.splitlines()
            if line.strip() and not line.strip().startswith(("%", "#"))
        ]
        cleaned = "\n".join(lines).strip()
        if cleaned:
            items.append(cleaned)
    return items


def extract_task(item: str) -> tuple[str, str]:
    """Extract project name (first word) and task text (everything else) from an item.

    Returns (project_name, task_text).
    """
    words = item.split(None, 1)
    if not words:
        return ("", "")
    project_name = words[0]
    task_text = words[1] if len(words) > 1 else ""
    return project_name, task_text


# ---------------------------------------------------------------------------
# JSON format parsing
# ---------------------------------------------------------------------------

def format_json_note(note: dict) -> str:
    """Format a JSON note dict into a human-readable task description for Roo Code.

    Includes all location information so Roo Code knows exactly where to look.
    """
    note_type = note.get("noteType", "NOTE")
    note_text = note.get("noteText", "")
    source_file = note.get("sourceFile", "")
    source_functions = note.get("sourceFunctions", "")
    screen_route = note.get("screenRoute", "")
    screen_label = note.get("screenLabel", "")

    parts = [f"[{note_type}] {note_text}"]

    if source_file:
        location = f"Location: {source_file}"
        if source_functions:
            location += f" → {source_functions}"
        parts.append(location)

    if screen_label or screen_route:
        screen_info = f"Screen: {screen_label}"
        if screen_route and screen_route.lower() != screen_label.lower():
            screen_info += f" ({screen_route})"
        parts.append(screen_info)

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _sibling_filepath(filepath: str, suffix: str) -> str:
    """Get a sibling filepath with a suffix added before the extension.

    e.g. RooCode_jobs.md + _completed -> RooCode_jobs_completed.md
    """
    p = Path(filepath)
    return str(p.with_name(p.stem + suffix + p.suffix))


def append_to_file(filepath: str, text: str) -> None:
    """Append text to a file, creating it if it doesn't exist."""
    with open(filepath, "a") as f:
        f.write(text)


# ---------------------------------------------------------------------------
# Markdown file processor
# ---------------------------------------------------------------------------

def remove_first_item(filepath: str) -> None:
    """Remove the first empty-line-separated item from the file."""
    try:
        with open(filepath, "r") as f:
            content = f.read()
    except FileNotFoundError:
        return

    items = parse_items(content)
    if len(items) <= 1:
        with open(filepath, "w") as f:
            f.write("")
        return

    remaining = "\n\n".join(items[1:]) + "\n"
    with open(filepath, "w") as f:
        f.write(remaining)


def process_markdown_file(filepath: str) -> bool:
    """Read a markdown watch file, process the first item, and send it to Roo Code.

    On success: removes the item from the jobs file and appends it to the
    completed file with a timestamp.
    On failure (no matching VSCode window): removes the item from the jobs
    file and moves it to the undone file so it doesn't block the queue.

    Returns True if a task was processed (success or moved to undone),
    False if nothing to process.
    """
    try:
        with open(filepath, "r") as f:
            content = f.read()
    except FileNotFoundError:
        logger.warning("Watch file not found: %s", filepath)
        return False

    items = parse_items(content)
    if not items:
        logger.debug("No items in file")
        return False

    first_item = items[0]
    project_name, task_text = extract_task(first_item)

    if not project_name:
        logger.warning("First item has no project name: %r", first_item)
        remove_first_item(filepath)
        return True

    logger.info("Processing task for project '%s': %s", project_name, task_text[:80])

    success = vscode_ctrl.send_task_to_roo_code(project_name, task_text)

    if config.REMOVE_AFTER_PROCESS:
        remove_first_item(filepath)

    if success:
        logger.info("Task sent successfully, removed from file")
        completed_path = _sibling_filepath(filepath, "_completed")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {first_item}\n\n"
        append_to_file(completed_path, entry)
        logger.info("Appended to completed file: %s", completed_path)
    else:
        logger.warning("Task failed (no VSCode window for '%s'), moving to undone", project_name)
        undone_path = _sibling_filepath(filepath, "_undone")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {first_item}\n\n"
        append_to_file(undone_path, entry)
        logger.info("Appended to undone file: %s", undone_path)

    return True


# ---------------------------------------------------------------------------
# JSON file processor
# ---------------------------------------------------------------------------

def _append_note_to_json(filepath: str, note: dict, timestamp: str) -> None:
    """Append a note dict to a JSON file in the same {"notes": [...]} format.

    Creates the file with the standard structure if it doesn't exist.
    Adds a "_processed" timestamp to the note for traceability.
    """
    note_copy = {**note, "_processed": timestamp}

    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, ValueError):
            data = {"notes": []}
    else:
        data = {"notes": []}

    data.setdefault("notes", []).append(note_copy)

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def process_json_file(filepath: str, project_name: str) -> bool:
    """Read a JSON watch file, process all notes, and send each to Roo Code.

    Each note in the "notes" array is formatted with full location info and
    sent as a separate Roo Code task. After processing, the notes array is
    cleared in the file.

    Completed/undone notes are saved in the same JSON format so they can be
    easily copied back into the original file to retry.

    Returns True if at least one task was processed, False if nothing to process.
    """
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.warning("JSON watch file not found: %s", filepath)
        return False
    except json.JSONDecodeError as e:
        logger.warning("Invalid JSON in %s: %s", filepath, e)
        return False

    notes = data.get("notes", [])
    if not notes:
        logger.debug("No notes in JSON file: %s", filepath)
        return False

    processed_any = False
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for note in notes:
        task_text = format_json_note(note)
        note_id = note.get("id", "unknown")
        logger.info("Processing JSON note %s for project '%s': %s",
                     note_id, project_name, task_text[:80])

        success = vscode_ctrl.send_task_to_roo_code(project_name, task_text)

        if success:
            completed_path = _sibling_filepath(filepath, "_completed")
            _append_note_to_json(completed_path, note, timestamp)
            logger.info("Note %s sent successfully", note_id)
        else:
            undone_path = _sibling_filepath(filepath, "_undone")
            _append_note_to_json(undone_path, note, timestamp)
            logger.warning("Note %s failed (no VSCode window for '%s')", note_id, project_name)

        processed_any = True
        # Brief pause between items to avoid overwhelming VSCode
        time.sleep(1.0)

    # Clear the notes array in the JSON file
    if config.REMOVE_AFTER_PROCESS:
        data["notes"] = []
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")

    return processed_any


# ---------------------------------------------------------------------------
# Watch loop (shared by both formats)
# ---------------------------------------------------------------------------

def _process_source(filepath: str, fmt: str, project: str | None) -> bool:
    """Dispatch to the correct processor based on format."""
    if fmt == "json":
        return process_json_file(filepath, project)
    return process_markdown_file(filepath)


def watch_source(source: dict) -> None:
    """Watch a single source file for changes and process items when changed."""
    filepath = os.path.abspath(os.path.expanduser(source["path"]))
    fmt = source["format"]
    project = source.get("project")

    if not os.path.exists(filepath):
        logger.info("Creating watch file: %s", filepath)
        if fmt == "json":
            with open(filepath, "w") as f:
                json.dump({"notes": []}, f, indent=2)
                f.write("\n")
        else:
            Path(filepath).touch()

    logger.info("Watching %s file: %s (project: %s)", fmt, filepath, project or "from-item")

    # Process any existing items first
    _process_source(filepath, fmt, project)

    # Start inotifywait in monitor mode
    cmd = [
        "inotifywait", "-m", "-e", "modify", "-e", "create",
        "--format", "%e", filepath,
    ]

    last_process_time = 0.0

    while True:
        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            logger.info("inotifywait started for %s (pid %d)", filepath, proc.pid)

            for line in proc.stdout:
                line = line.strip()
                if not line:
                    continue

                logger.debug("File change event on %s: %s", filepath, line)

                # Debounce: don't process more than once per DEBOUNCE_SECONDS
                now = time.time()
                if now - last_process_time < config.DEBOUNCE_SECONDS:
                    logger.debug("Debouncing (last process was %.1fs ago)", now - last_process_time)
                    continue

                # Check if screen is unlocked
                if not is_screen_unlocked():
                    logger.info("Screen is locked, skipping")
                    continue

                # Small delay to let file writes complete
                time.sleep(0.5)

                # Process all available items (not just one per event)
                while True:
                    success = _process_source(filepath, fmt, project)
                    if not success:
                        break
                    last_process_time = time.time()
                    # Brief pause between items to avoid overwhelming VSCode
                    time.sleep(1.0)

            # If we get here, inotifywait exited
            proc.wait()
            if proc.returncode != 0:
                logger.error("inotifywait exited with code %d for %s: %s",
                             proc.returncode, filepath, proc.stderr.read())
            else:
                logger.info("inotifywait exited normally for %s", filepath)

        except FileNotFoundError:
            logger.error("inotifywait not found. Install with: sudo apt install inotify-tools")
            sys.exit(1)
        except KeyboardInterrupt:
            logger.info("Interrupted, shutting down")
            break
        except Exception:
            logger.exception("Unexpected error in watch loop for %s", filepath)
            time.sleep(5)  # Back off before retrying


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Watch files for tasks and send them to Roo Code in VSCode",
    )
    parser.add_argument(
        "--once", action="store_true",
        help="Process all sources once and exit (don't watch)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else getattr(logging, config.LOG_LEVEL),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    sources = config.WATCH_SOURCES

    if args.once:
        any_success = False
        for source in sources:
            filepath = os.path.abspath(os.path.expanduser(source["path"]))
            fmt = source["format"]
            project = source.get("project")
            success = _process_source(filepath, fmt, project)
            any_success = any_success or success
        sys.exit(0 if any_success else 1)

    # Start one daemon thread per watch source
    threads = []
    for source in sources:
        t = threading.Thread(
            target=watch_source,
            args=(source,),
            name=f"watch-{source.get('project', Path(source['path']).stem)}",
            daemon=True,
        )
        t.start()
        threads.append(t)
        logger.info("Started watch thread for %s", source["path"])

    # Keep main thread alive until interrupted
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Interrupted, shutting down")


if __name__ == "__main__":
    main()
