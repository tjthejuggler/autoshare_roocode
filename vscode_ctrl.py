"""VSCode window management and Roo Code interaction using xdotool and wmctrl.

Key insight: Roo Code registers VSCode commands that we can invoke through the
command palette, avoiding the need for image recognition entirely:
  - "Roo Code: New Task"       → opens sidebar + starts new task + focuses input
  - "Roo Code: Focus Input Field" → opens sidebar + focuses input

All xdotool keystrokes are sent directly to the target window ID using
--window <id>, so they go to the right VSCode window even when multiple
VSCode windows are open.
"""

import logging
import subprocess
import time

import config

logger = logging.getLogger(__name__)


def _run(cmd: list[str], check: bool = True) -> str:
    """Run a shell command and return stdout."""
    logger.debug("Running: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, check=check)
    return result.stdout.strip()


def find_vscode_window(project_name: str) -> tuple[str, str] | None:
    """Find a VSCode window whose title contains the project name (case-insensitive).

    VSCode window titles look like: "filename - project_name - Visual Studio Code"
    or just "project_name - Visual Studio Code".

    Returns (window_id_hex, window_title) or None.
    """
    output = _run(["wmctrl", "-l"])
    project_lower = project_name.lower()

    for line in output.splitlines():
        # wmctrl -l format: <hex_id> <desktop> <hostname> <title>
        parts = line.split(None, 3)
        if len(parts) < 4:
            continue
        win_id, _, _, title = parts
        if "Visual Studio Code" not in title:
            continue
        # Check if project name appears in the title (case-insensitive)
        if project_lower in title.lower():
            logger.info("Found VSCode window for '%s': %s (%s)", project_name, title, win_id)
            return (win_id, title)

    logger.warning("No VSCode window found for project '%s'", project_name)
    return None


def _win_id_decimal(win_id_hex: str) -> str:
    """Convert a hex window ID (e.g. '0x040000bc') to decimal string for xdotool."""
    return str(int(win_id_hex, 16))


def activate_window(win_id: str) -> None:
    """Bring a window to the foreground and wait for it to be active."""
    _run(["wmctrl", "-i", "-a", win_id])
    time.sleep(config.DELAY_AFTER_ACTIVATE)
    # Also use xdotool to focus it, ensuring keyboard input goes there
    _run(["xdotool", "windowfocus", "--sync", _win_id_decimal(win_id)])
    time.sleep(0.3)


def set_clipboard(text: str) -> None:
    """Copy text to the X11 clipboard using xclip."""
    subprocess.run(
        ["xclip", "-selection", "clipboard"],
        input=text, text=True, check=True,
    )


def type_key(keys: str, win_id: str) -> None:
    """Type a key combination directly to a specific window using xdotool."""
    _run(["xdotool", "key", "--window", _win_id_decimal(win_id), keys])


def type_text(text: str, win_id: str) -> None:
    """Type text directly to a specific window using xdotool."""
    _run(["xdotool", "type", "--window", _win_id_decimal(win_id), "--delay", "5", text])


def dismiss_popups(win_id: str) -> None:
    """Press Escape to close any open palette, dialog, or popup."""
    type_key("Escape", win_id)
    time.sleep(0.3)


def execute_command(command_name: str, win_id: str) -> None:
    """Execute a VSCode command by typing it in the command palette.

    command_name should be the display name, e.g. "Roo Code: New Task".
    All keystrokes are sent directly to win_id.
    """
    # Open command palette
    type_key("ctrl+shift+p", win_id)
    time.sleep(config.DELAY_COMMAND_PALETTE)

    # Type the command name - VSCode filters as we type
    type_text(command_name, win_id)
    time.sleep(config.DELAY_AFTER_TYPE)

    # Execute the selected command
    type_key("Return", win_id)


def start_new_task(win_id: str) -> None:
    """Start a new Roo Code task via command palette.

    "Roo Code: New Task" opens the sidebar if needed, starts a new task,
    and focuses the input field.
    """
    execute_command("Roo Code: New Task", win_id)
    time.sleep(config.DELAY_AFTER_NEWTASK)


def paste_and_submit(text: str, win_id: str) -> None:
    """Paste text into the currently focused input and press Enter to submit."""
    set_clipboard(text)
    type_key("ctrl+v", win_id)
    time.sleep(config.DELAY_AFTER_PASTE)
    type_key("Return", win_id)


def send_task_to_roo_code(project_name: str, task_text: str) -> bool:
    """Full workflow: find VSCode window, start new Roo Code task, paste and submit.

    All xdotool keystrokes are sent directly to the target window by ID,
    so they go to the right window regardless of which window has focus.

    Args:
        project_name: The project name to match in VSCode window titles.
        task_text: The text to paste into the Roo Code chat input.

    Returns:
        True if successful, False otherwise.
    """
    # Step 1: Find the VSCode window for this project
    result = find_vscode_window(project_name)
    if not result:
        logger.error("Cannot find VSCode window for project '%s'", project_name)
        return False
    win_id, title = result

    # Step 2: Activate the window (bring to front + focus)
    activate_window(win_id)

    # Step 3: Dismiss any open popups/palettes for clean state
    dismiss_popups(win_id)

    # Step 4: Start a new task (this opens sidebar + focuses input)
    start_new_task(win_id)

    # Step 5: Paste the task text and submit
    paste_and_submit(task_text, win_id)

    logger.info("Task sent to Roo Code in project '%s'", project_name)
    return True
