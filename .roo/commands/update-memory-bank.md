---
description: "Synchronize the Memory Bank with all changes from the current session"
---

# Update Memory Bank (UMB)

Execute the following steps in order:

1. **Halt** any current task — do not continue coding or planning
2. Respond with `[MEMORY BANK: UPDATING]`
3. **Review** the entire chat session history from start to now
4. **Scan** all unstaged file modifications and recent diffs to understand what changed
5. **Update** each memory bank file as appropriate:
   - `memory-bank/activeContext.md` — rewrite Current Focus to reflect exact session end state, document unresolved errors, partial implementations, and immediate next steps
   - `memory-bank/progress.md` — move completed items, add newly discovered tasks or technical debt
   - `memory-bank/decisionLog.md` — log any new architectural or implementation decisions with rationale
   - `memory-bank/systemPatterns.md` — add any new utility functions, patterns, or conventions established
   - `memory-bank/productContext.md` — update only if project goals or features changed
6. **Verify** each file was actually written by reading it back
7. **Confirm** synchronization: "Memory Bank synchronized. All context preserved. Session can be safely closed."
