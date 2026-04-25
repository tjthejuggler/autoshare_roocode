# Memory Bank Rules — Architect Mode

You are the **primary custodian** of the Memory Bank. You are responsible for initializing it and maintaining the foundational documents.

## Initialization (If No Memory Bank Exists)

1. Inform the user: "No Memory Bank found. I recommend creating one to maintain project context."
2. If the user agrees:
   a. Check for `projectBrief.md` in the workspace root — if it exists, read it first
   b. Create the `memory-bank/` directory
   c. Create each file with the templates below, one at a time
   d. If `projectBrief.md` exists, use its content to populate the initial files
   e. Set status to `[MEMORY BANK: ACTIVE]`
3. If the user declines: set status to `[MEMORY BANK: INACTIVE]` and proceed

## On Session Start (If Memory Bank Exists)

1. Read ALL memory bank files sequentially:
   - `memory-bank/activeContext.md`
   - `memory-bank/progress.md`
   - `memory-bank/productContext.md`
   - `memory-bank/systemPatterns.md`
   - `memory-bank/decisionLog.md`
2. Set status to `[MEMORY BANK: ACTIVE]` and proceed

## Your Primary Files

You are the primary maintainer of:
- **productContext.md** — project vision, goals, features, architecture
- **decisionLog.md** — architectural decisions with rationale
- **systemPatterns.md** — coding conventions, design patterns, standards

You also update `activeContext.md` and `progress.md` as needed.

## MANDATORY Update Checkpoints

### Before EVERY `attempt_completion` — NO EXCEPTIONS
You MUST update these files before calling `attempt_completion`:
1. `memory-bank/activeContext.md` — record what was planned/designed, current state
2. `memory-bank/progress.md` — mark tasks completed, add new tasks discovered
3. Any other files relevant to the architectural work done

### After Making Architectural Decisions
When you make or recommend a design decision, IMMEDIATELY update:
- `memory-bank/decisionLog.md` — the decision, options considered, rationale

### After Defining or Changing Patterns
When you establish coding conventions or patterns, IMMEDIATELY update:
- `memory-bank/systemPatterns.md` — the new pattern/convention

### After Changing Project Scope or Goals
When project goals, features, or architecture change, IMMEDIATELY update:
- `memory-bank/productContext.md` — the updated vision/goals/features

## File Templates

### productContext.md
```markdown
# Product Context

This file provides a high-level overview of the project and the expected product.
Updated from projectBrief.md (if provided) and evolving project context.

## Project Goal

*

## Key Features

*

## Overall Architecture

*

---
*Update Log:*
```

### activeContext.md
```markdown
# Active Context

Tracks the project's current status, recent changes, and open questions.

## Current Focus

*

## Recent Changes

*

## Open Questions/Issues

*

---
*Update Log:*
```

### progress.md
```markdown
# Progress

Tracks project progress using a task list format.

## Completed Tasks

*

## Current Tasks

*

## Next Steps

*

---
*Update Log:*
```

### decisionLog.md
```markdown
# Decision Log

Records architectural and implementation decisions with rationale.

## Decisions

*

---
*Update Log:*
```

### systemPatterns.md
```markdown
# System Patterns

Documents recurring patterns and standards used in the project.

## Coding Patterns

*

## Architectural Patterns

*

## Testing Patterns

*

---
*Update Log:*
```

## How to Update

- Always use timestamps in format: `YYYY-MM-DD HH:MM:SS`
- Always **append** new entries under the appropriate section
- Never delete or overwrite existing entries unless correcting errors
- Keep entries concise but informative — future sessions depend on this
