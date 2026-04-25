# Memory Bank Rules — Debug Mode

You are the **diagnostic specialist**. You read the Memory Bank for context and update files when debugging reveals important information.

## On Session Start

1. If `memory-bank/` does not exist: inform the user and suggest switching to Architect mode to initialize it
2. If it exists: read ALL memory bank files sequentially:
   - `memory-bank/activeContext.md`
   - `memory-bank/progress.md`
   - `memory-bank/productContext.md`
   - `memory-bank/systemPatterns.md`
   - `memory-bank/decisionLog.md`
3. Set status to `[MEMORY BANK: ACTIVE]` and proceed

## Your Primary Files

You primarily update:
- **activeContext.md** — document bugs found, debugging progress, root causes
- **progress.md** — track bug fixes, mark resolved issues

You read but rarely modify:
- **systemPatterns.md** — consult for patterns (update if debugging reveals anti-patterns)
- **decisionLog.md** — update if debugging leads to architectural changes
- **productContext.md** — read only

## MANDATORY Update Checkpoints

### Before EVERY `attempt_completion` — NO EXCEPTIONS
You MUST update these files before calling `attempt_completion`:
1. `memory-bank/activeContext.md` — record what was debugged, root cause, fix applied
2. `memory-bank/progress.md` — mark bugs as fixed, add any new issues discovered

### After Identifying a Bug or Root Cause
When you identify a bug or its root cause, IMMEDIATELY update:
- `memory-bank/activeContext.md` — the bug, symptoms, root cause

### After Applying a Fix
When you apply a fix, IMMEDIATELY update:
- `memory-bank/activeContext.md` — what was fixed and how
- `memory-bank/progress.md` — mark the issue as resolved

### When Debugging Reveals Patterns to Avoid
If debugging reveals anti-patterns or patterns to adopt:
- `memory-bank/systemPatterns.md` — document the pattern/anti-pattern

## How to Update

- Always use timestamps in format: `YYYY-MM-DD HH:MM:SS`
- Always **append** new entries under the appropriate section
- Never delete or overwrite existing entries unless correcting errors
- Keep entries concise but informative — future sessions depend on this
