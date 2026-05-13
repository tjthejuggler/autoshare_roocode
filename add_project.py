#!/usr/bin/env python3
"""Add a new watch source to autoshare_roocode and restart the watcher.

Usage:
    # Add a markdown source (project name extracted from first word of items)
    python add_project.py ~/noteVault/RooCode_jobs.md

    # Add a JSON source (project name required)
    python add_project.py /path/to/debug_myapp.json --project myapp

    # Explicit format
    python add_project.py ~/noteVault/jobs.md --format markdown

    # Add without restarting the watcher
    python add_project.py /path/to/debug_myapp.json --project myapp --no-restart
"""

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "config.py"
AUTOSHARE_PATH = SCRIPT_DIR / "autoshare.py"
VENV_PYTHON = SCRIPT_DIR / "venv" / "bin" / "python3"


def find_autoshare_pids() -> list[int]:
    """Find PIDs of running autoshare.py processes (excluding this script)."""
    my_pid = os.getpid()
    try:
        result = subprocess.run(
            ["pgrep", "-f", "autoshare\\.py"],
            capture_output=True, text=True,
        )
    except FileNotFoundError:
        # Fallback: use ps
        result = subprocess.run(
            ["ps", "-eo", "pid,comm,args"],
            capture_output=True, text=True,
        )
        pids = []
        for line in result.stdout.splitlines():
            if "autoshare.py" in line and "add_project" not in line:
                parts = line.strip().split(None, 1)
                if parts:
                    try:
                        pid = int(parts[0])
                        if pid != my_pid:
                            pids.append(pid)
                    except ValueError:
                        pass
        return pids

    pids = []
    for line in result.stdout.strip().splitlines():
        try:
            pid = int(line.strip())
            if pid != my_pid:
                pids.append(pid)
        except ValueError:
            continue
    return pids


def stop_autoshare() -> bool:
    """Stop running autoshare.py processes. Returns True if any were found."""
    pids = find_autoshare_pids()
    if not pids:
        print("No running autoshare.py process found.")
        return False

    for pid in pids:
        print(f"Stopping autoshare.py (PID {pid})...")
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            continue

    # Wait for processes to exit
    for _ in range(10):
        if not find_autoshare_pids():
            print("Process stopped.")
            return True
        time.sleep(0.5)

    # Force kill if still running
    for pid in find_autoshare_pids():
        try:
            os.kill(pid, signal.SIGKILL)
            print(f"Force-killed PID {pid}.")
        except ProcessLookupError:
            pass
    return True


def start_autoshare() -> None:
    """Start autoshare.py in the background."""
    python = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
    print(f"Starting autoshare.py with {python}...")
    subprocess.Popen(
        [python, str(AUTOSHARE_PATH)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    # Brief pause to let it start
    time.sleep(1.0)
    if find_autoshare_pids():
        print("autoshare.py started successfully.")
    else:
        print("WARNING: autoshare.py may not have started. Check manually.")


def add_watch_source(filepath: str, fmt: str, project: str | None) -> None:
    """Add a new entry to WATCH_SOURCES in config.py."""
    content = CONFIG_PATH.read_text()
    lines = content.split("\n")

    # Find the WATCH_SOURCES block by bracket counting
    in_watch_sources = False
    bracket_depth = 0
    insert_line = -1

    for i, line in enumerate(lines):
        if "WATCH_SOURCES" in line and "[" in line:
            in_watch_sources = True
            bracket_depth = line.count("[") - line.count("]")
            continue

        if in_watch_sources:
            bracket_depth += line.count("[") - line.count("]")
            if bracket_depth <= 0:
                insert_line = i
                break

    if insert_line == -1:
        print("ERROR: Could not find WATCH_SOURCES list in config.py", file=sys.stderr)
        sys.exit(1)

    # Build the new entry
    if fmt == "markdown":
        new_entry_lines = [
            "    {",
            f'        "path": "{filepath}",',
            '        "format": "markdown",',
            '        "project": None,  # Extracted from first word of each item',
            "    },",
        ]
    else:
        new_entry_lines = [
            "    {",
            f'        "path": "{filepath}",',
            '        "format": "json",',
            f'        "project": "{project}",',
            "    },",
        ]

    # Insert before the closing ]
    for j, entry_line in enumerate(new_entry_lines):
        lines.insert(insert_line + j, entry_line)

    CONFIG_PATH.write_text("\n".join(lines))
    label = f"format={fmt}, project={project or 'from-item'}"
    print(f"Added watch source to config.py: {filepath} ({label})")


def source_exists(filepath: str) -> bool:
    """Check if a file path is already in WATCH_SOURCES."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("config", str(CONFIG_PATH))
    if spec and spec.loader:
        cfg = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cfg)
        expanded_input = os.path.abspath(os.path.expanduser(filepath))
        for source in cfg.WATCH_SOURCES:
            expanded_existing = os.path.abspath(os.path.expanduser(source["path"]))
            if expanded_existing == expanded_input:
                return True
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Add a new watch source to autoshare_roocode and restart the watcher.",
    )
    parser.add_argument(
        "path",
        help="Path to the file to watch (e.g. ~/noteVault/RooCode_jobs.md)",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["markdown", "json"],
        default=None,
        help="File format (default: inferred from extension)",
    )
    parser.add_argument(
        "--project", "-p",
        default=None,
        help="Project name (required for JSON format, ignored for markdown)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip duplicate check (useful after manual config edits)",
    )
    parser.add_argument(
        "--no-restart",
        action="store_true",
        help="Add the source but don't restart the watcher",
    )
    args = parser.parse_args()

    # Infer format from extension if not specified
    fmt = args.format
    if fmt is None:
        if args.path.endswith(".json"):
            fmt = "json"
        elif args.path.endswith(".md"):
            fmt = "markdown"
        else:
            print(
                "ERROR: Cannot infer format from extension. "
                "Use --format markdown or --format json.",
                file=sys.stderr,
            )
            sys.exit(1)

    # Validate project name for JSON format
    if fmt == "json" and not args.project:
        print(
            "ERROR: --project is required for JSON format watch sources.",
            file=sys.stderr,
        )
        sys.exit(1)

    project = args.project if fmt == "json" else None

    # Check for duplicates
    already_exists = source_exists(args.path)
    if already_exists and not args.force:
        print(
            f"ERROR: File already watched: {args.path}\n"
            "Use --force to skip this check (e.g. after a manual config edit).",
            file=sys.stderr,
        )
        sys.exit(1)

    # Add the source to config.py (skip if already present with --force)
    if not already_exists:
        add_watch_source(args.path, fmt, project)
    else:
        print(f"Source already in config.py, skipping add (--force used).")

    # Restart the watcher
    if not args.no_restart:
        stopped = stop_autoshare()
        start_autoshare()
        if stopped:
            print("Watcher restarted with new configuration.")
        else:
            print("Watcher started (was not previously running).")
    elif already_exists:
        print("Config unchanged. Restart the watcher to apply any manual edits.")
    else:
        print("Source added. Restart the watcher manually to apply changes.")


if __name__ == "__main__":
    main()
