# ADR: add_project.py CLI Tool for Adding Watch Sources

## Status: Accepted (2026-05-13)

## Context
Adding a new project to autoshare_roocode required manually editing config.py's WATCH_SOURCES list and then manually restarting the watcher process. This is error-prone and slow, especially when you want a new project to start being tracked immediately.

## Decision
Created `add_project.py` as a CLI tool that:
1. Accepts a file path and format (markdown/json) as arguments
2. Validates input: duplicate detection, requires --project for JSON format
3. Infers format from file extension (.md → markdown, .json → json) when not specified
4. Programmatically inserts a new entry into the WATCH_SOURCES list in config.py
5. Stops the running autoshare.py process (SIGTERM, fallback SIGKILL)
6. Starts a fresh autoshare.py process so the new config takes effect immediately
7. Supports `--no-restart` flag for cases where manual restart is preferred

## Consequences
- Adding a project is a single command instead of manual edit + restart
- The watcher restart ensures new sources are picked up immediately
- Duplicate detection prevents the same file from being watched twice
- The script modifies config.py as text (line insertion) preserving comments and formatting