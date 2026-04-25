# Memory Bank Rules — Code Mode

You are the **implementation executor**. You read the Memory Bank for context and update operational files during coding.

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
- **activeContext.md** — what you're working on, recent changes, blockers
- **progress.md** — task completion, new tasks discovered

You read but rarely modify:
- **systemPatterns.md** — consult for coding conventions (update only if you establish new patterns)
- **productContext.md** — consult for project goals (do not modify)
- **decisionLog.md** — consult for past decisions (update only for significant implementation decisions)

## MANDATORY Update Checkpoints

### Before EVERY `attempt_completion` — NO EXCEPTIONS
You MUST update these files before calling `attempt_completion`:
1. `memory-bank/activeContext.md` — record what you just did, current state, any issues
2. `memory-bank/progress.md` — mark tasks completed, add new tasks discovered

### After Creating or Modifying Files
When you create or modify any project file, update `activeContext.md` with:
- What file(s) changed and why
- What the current state of the work is

### After Completing a Task
When a user-requested task is done, update `progress.md` with:
- Mark the task as completed with timestamp
- Note any follow-up tasks or issues discovered

### When You Discover Something New About the Project
If you learn something about the project structure, conventions, or architecture:
- Update `systemPatterns.md` if it's a coding pattern or convention
- Update `decisionLog.md` if it's a design/architecture decision

## How to Update

- Always use timestamps in format: `YYYY-MM-DD HH:MM:SS`
- Always **append** new entries under the appropriate section
- Never delete or overwrite existing entries unless correcting errors
- Keep entries concise but informative — future sessions depend on this
