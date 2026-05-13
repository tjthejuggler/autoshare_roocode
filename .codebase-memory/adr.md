# ADR: Serialized Task Submission Across Watch Threads

**Date:** 2026-05-13
**Status:** Accepted

## Context
When the computer starts up with multiple watch sources having pending items, each source's daemon thread calls `vscode_ctrl.send_task_to_roo_code()` simultaneously. Each call activates a different VSCode window and sends keystrokes to it. Concurrent `activate_window()` calls fight over window focus, causing keystrokes to go to the wrong window or get lost, resulting in all but one submission failing.

## Decision
Serialize all submissions through a global lock (`_submit_lock`) and enforce a minimum delay (`config.INTER_SUBMIT_DELAY`, default 60s) between consecutive submissions. The `_send_task_serialized()` wrapper in `autoshare.py` replaces direct calls to `vscode_ctrl.send_task_to_roo_code()`.

## Consequences
- Only one Roo Code task is in-flight at a time across all projects
- Startup with N pending projects takes ~N minutes instead of failing silently
- The delay is configurable in config.py
- The lock is held during the sleep, which is simple and correct since we want true serialization