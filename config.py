"""Configuration for autoshare_roocode."""

# Watch sources: each entry defines a file to watch, its format, and project name.
# - "markdown" format: project name is the first word of each item in the file
# - "json" format: project name comes from the "project" field below
#
# To add a new source, copy an existing entry and change the values.
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
    {
        "path": "/home/twain/habitsdb/Tail_debug/debug_tail.json",
        "format": "json",
        "project": "tail",
    },
]

# Whether to remove items from the file after processing
REMOVE_AFTER_PROCESS = True

# Timing delays in seconds
DELAY_AFTER_ACTIVATE = 0.5       # After activating a window
DELAY_COMMAND_PALETTE = 0.5      # After opening command palette
DELAY_AFTER_TYPE = 0.3           # After typing in command palette
DELAY_AFTER_NEWTASK = 2.0        # After executing New Task command
DELAY_AFTER_PASTE = 0.5          # After pasting text
DEBOUNCE_SECONDS = 2.0           # Debounce file change events

# Logging
LOG_LEVEL = "INFO"
