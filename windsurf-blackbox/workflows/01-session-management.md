# Session Management Workflow

Comprehensive session lifecycle management with integrated ID tracking protocol for the Windsurf Black Box system.

---

## Session ID Protocol

### ID Format

```
CONV-[YYYY]-[MM]-[DD]-[NNN]-[TOPIC]

Components:
├── CONV          → Fixed prefix (conversation)
├── YYYY-MM-DD    → Date of session start
├── NNN           → Sequential number for that day (001, 002, etc.)
└── TOPIC         → Brief kebab-case descriptor (optional but recommended)

Examples:
├── CONV-2024-12-14-001-auth-setup
├── CONV-2024-12-14-002-api-debugging
├── CONV-2024-12-15-001-frontend-dashboard
└── CONV-2024-12-15-002-hotfix-login
```

### ID Generation Rules

| Rule | Description |
|------|-------------|
| **Uniqueness** | Each session gets exactly one ID, never reused |
| **Sequence** | NNN resets daily, increments per session |
| **Topic** | 2-4 words, lowercase, hyphens only |
| **Persistence** | ID stays same even if session spans multiple days |
| **Linking** | Child sessions reference parent ID |

---

## Phase 1: Session Initialization

### Pre-Session Checklist

```bash
# Before starting Windsurf
□ Check last session's continuation prompt
□ Review outstanding action items
□ Note current branch and state
□ Identify today's objectives
□ Generate new session ID
```

### Session Start Protocol

**Step 1: Generate Session ID**

```bash
# Use the automation script
./blackbox.sh start "auth-refactor"
# → Creates: CONV-2024-12-17-001-auth-refactor
```

**Step 2: Announce to Cascade**

Copy and paste this to Cascade at session start:

```
═══════════════════════════════════════════════════════════════
🎬 SESSION START
═══════════════════════════════════════════════════════════════

Session ID: CONV-[YYYY-MM-DD-NNN-TOPIC]
Project: [Project Name]
Branch: [current-branch]
Previous Session: [CONV-ID or "None"]

═══════════════════════════════════════════════════════════════
CONTEXT LOAD
═══════════════════════════════════════════════════════════════

Last session summary:
[Paste from previous continuation prompt or "New project"]

Current state:
- Build: [passing/failing/unknown]
- Tests: [X passing, Y failing]
- Blockers: [None or list]

═══════════════════════════════════════════════════════════════
TODAY'S OBJECTIVES
═══════════════════════════════════════════════════════════════

Priority 1: [Main goal]
Priority 2: [Secondary goal]
Priority 3: [If time permits]

═══════════════════════════════════════════════════════════════
KEY FILES
═══════════════════════════════════════════════════════════════

@src/[file1]
@src/[file2]
@[other relevant files]

═══════════════════════════════════════════════════════════════

Please acknowledge this session ID and track all decisions,
actions, and outcomes under it. Reference this ID in important
moments throughout our work.
```

### Cascade Acknowledgment Expected

Cascade should respond with:

```
✅ Session CONV-[ID] initialized
📋 Tracking: decisions, actions, outcomes
🎯 Objectives loaded
📁 Key files noted

Ready to continue from [previous state/fresh start].
What would you like to tackle first?
```

---

## Phase 2: Active Session Tracking

### Real-Time Logging Commands

Use these prompts during the session:

| Type | Prompt Template |
|------|-----------------|
| **Action** | `"[SESSION-ID] Log action: [description]. Files: [files]. Result: [success/fail]"` |
| **Decision** | `"[SESSION-ID] Log decision: [what]. Rationale: [why]. Rejected: [alternatives]"` |
| **Issue** | `"[SESSION-ID] Log issue: [problem]. Error: [message]. Status: [resolved/pending]"` |
| **Discussion** | `"[SESSION-ID] Log discussion: [topic]. Conclusion: [outcome]"` |
| **Checkpoint** | `"[SESSION-ID] Create checkpoint: [description]"` |

### Quick Log Formats

**Action Log**
```
[HH:MM] ACTION @CONV-ID: Implemented user authentication
├── Files: auth.ts, middleware.ts, types.ts
├── Result: ✅ Success
├── Tests: 3 new, all passing
└── Note: Used JWT with 24h expiry
```

**Decision Log**
```
[HH:MM] DECISION @CONV-ID: Use PostgreSQL over MongoDB
├── Rationale: Relational data, ACID compliance needed
├── Rejected: MongoDB (document model doesn't fit)
├── Rejected: SQLite (need concurrent connections)
└── Impact: Need to set up migrations
```

**Issue Log**
```
[HH:MM] ISSUE @CONV-ID: Build failing on CI
├── Error: `Module not found: '@/lib/utils'`
├── Cause: Path alias not configured in tsconfig
├── Fix: Added paths to tsconfig.json
└── Status: ✅ Resolved
```

**Checkpoint Log**
```
[HH:MM] CHECKPOINT @CONV-ID: Pre-refactor snapshot
├── Branch: feature/auth @ commit abc123
├── State: All tests passing, build clean
├── Purpose: Safety point before major changes
└── Restore: git checkout abc123
```

### Milestone Markers

Mark significant progress points:

```
═══════════════════════════════════════════════════════════════
🏁 MILESTONE @CONV-2024-12-17-001-auth-refactor
═══════════════════════════════════════════════════════════════

Milestone: User authentication complete
Time: 14:30

Achieved:
✅ Login/logout flow working
✅ JWT token generation
✅ Protected route middleware
✅ Session persistence

Metrics:
- Files changed: 8
- Lines added: 342
- Tests added: 12
- Coverage: 87%

Next milestone: Password reset flow
═══════════════════════════════════════════════════════════════
```

---

## Phase 3: Session Closure

### Pre-Close Checklist

```bash
□ All work committed (or stashed with note)
□ Tests passing (or failures documented)
□ No uncommitted experiments
□ Action items identified
□ Continuation prompt prepared
```

### Session End Protocol

**Step 1: Request Summary from Cascade**

```
═══════════════════════════════════════════════════════════════
🎬 SESSION END: CONV-[ID]
═══════════════════════════════════════════════════════════════

Please generate the closing documentation:

1. SESSION SUMMARY
   - What was accomplished
   - What was attempted but not completed
   - Key decisions made (with rationale)
   - Issues encountered and resolutions

2. STATE SNAPSHOT
   - Current branch and commit
   - Build/test status
   - Any temporary code or experiments

3. ACTION ITEMS
   - Must do next session
   - Should do soon
   - Nice to have

4. CONTINUATION PROMPT
   - Complete prompt I can paste to resume
   - Include all context needed

5. LEARNINGS
   - What worked well
   - What to do differently
   - Insights for future

Format for my Black Box archive.
═══════════════════════════════════════════════════════════════
```

**Step 2: Save to Black Box**

```bash
# Use automation script
./blackbox.sh end

# Or manually save to:
# .windsurf-blackbox/sessions/CONV-2024-12-17-001-auth-refactor.md
```

### Session Close Template

```markdown
# Session Record: CONV-[ID]

## Metadata
| Field | Value |
|-------|-------|
| Session ID | CONV-[YYYY-MM-DD-NNN-TOPIC] |
| Date | [YYYY-MM-DD] |
| Duration | [X hours Y minutes] |
| Project | [Project Name] |
| Branch | [branch-name] |
| Previous | [Previous CONV-ID or None] |
| Next | [To be filled] |

## Objectives vs Outcomes

| Objective | Status | Notes |
|-----------|--------|-------|
| [Priority 1] | ✅/⚠️/❌ | [Details] |
| [Priority 2] | ✅/⚠️/❌ | [Details] |
| [Priority 3] | ✅/⚠️/❌ | [Details] |

## Timeline

| Time | Type | Description |
|------|------|-------------|
| [HH:MM] | START | Session initialized |
| [HH:MM] | ACTION | [Description] |
| [HH:MM] | DECISION | [Description] |
| [HH:MM] | MILESTONE | [Description] |
| [HH:MM] | END | Session closed |

## Decisions Made

### DEC-001: [Decision Title]
- **Choice:** [What was decided]
- **Rationale:** [Why]
- **Alternatives:** [What was rejected and why]
- **Impact:** [Consequences]

## Issues & Resolutions

### ISS-001: [Issue Title]
- **Problem:** [Description]
- **Error:** `[Error message if applicable]`
- **Cause:** [Root cause]
- **Solution:** [How it was fixed]
- **Prevention:** [How to avoid in future]

## Code Changes

| File | Change Type | Description |
|------|-------------|-------------|
| [path/file] | Added/Modified/Deleted | [What changed] |

## Action Items

### Must Do (Next Session)
- [ ] [Action 1]
- [ ] [Action 2]

### Should Do (Soon)
- [ ] [Action 3]
- [ ] [Action 4]

### Nice to Have
- [ ] [Action 5]

## Continuation Prompt

```
SESSION CONTINUATION: CONV-[ID]
Project: [Name]
Branch: [branch]

LAST SESSION SUMMARY:
[2-3 sentence summary of what was accomplished]

CURRENT STATE:
- Build: [status]
- Tests: [status]
- Branch: [name] @ [commit]

IMMEDIATE CONTEXT:
[Specific details about where we stopped]

KEY DECISIONS MADE:
1. [Decision 1] - because [reason]
2. [Decision 2] - because [reason]

OUTSTANDING ISSUES:
1. [Issue if any]

TODAY'S PRIORITY:
[From action items - what to tackle first]

KEY FILES:
@[file1] @[file2]

CONTEXT THAT MIGHT BE FORGOTTEN:
[Important details that aren't obvious from code]
```

## Learnings

### What Worked Well
- [Learning 1]
- [Learning 2]

### What To Do Differently
- [Improvement 1]
- [Improvement 2]

### Insights for Future
- [Insight 1]
- [Insight 2]

---
*Recorded by Windsurf Black Box v1.0*
*Session Duration: [X:XX]*
*Generated: [Timestamp]*
```

---

## Phase 4: Session Linking

### Parent-Child Sessions

When a session spawns a sub-task:

```
CONV-2024-12-17-001-auth-refactor          ← Parent
├── CONV-2024-12-17-001a-jwt-implementation  ← Child
├── CONV-2024-12-17-001b-password-hashing    ← Child
└── CONV-2024-12-17-001c-session-storage     ← Child
```

### Continuation Chains

```
CONV-2024-12-15-003-api-design
    ↓ continues as
CONV-2024-12-17-001-api-implementation
    ↓ continues as
CONV-2024-12-18-002-api-testing
```

### Cross-Reference Format

```markdown
## Related Sessions

| Relationship | Session ID | Description |
|--------------|------------|-------------|
| Previous | CONV-2024-12-15-003 | Initial API design |
| Parent | CONV-2024-12-17-001 | Main auth refactor |
| Related | CONV-2024-12-16-002 | Database schema work |
| Next | [TBD] | Testing phase |
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│              SESSION MANAGEMENT QUICK REFERENCE             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  START SESSION                                              │
│  ─────────────                                              │
│  1. ./blackbox.sh start "topic-name"                        │
│  2. Paste START prompt to Cascade                           │
│  3. Wait for acknowledgment                                 │
│                                                             │
│  DURING SESSION                                             │
│  ──────────────                                             │
│  • Log actions:   "[ID] Log action: ..."                    │
│  • Log decisions: "[ID] Log decision: ..."                  │
│  • Log issues:    "[ID] Log issue: ..."                     │
│  • Checkpoint:    "[ID] Create checkpoint: ..."             │
│  • Milestone:     "[ID] Mark milestone: ..."                │
│                                                             │
│  END SESSION                                                │
│  ───────────                                                │
│  1. Paste END prompt to Cascade                             │
│  2. Copy generated summary                                  │
│  3. ./blackbox.sh end                                       │
│  4. Verify saved to .windsurf-blackbox/sessions/            │
│                                                             │
│  ID FORMAT                                                  │
│  ─────────                                                  │
│  CONV-YYYY-MM-DD-NNN-topic-name                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Integration with Other Workflows

This session management workflow integrates with:

| Workflow | Integration Point |
|----------|-------------------|
| **SSOT** | Session decisions update SSOT |
| **Code Review** | Reviews reference session ID |
| **Git Workflow** | Commits include session ID |
| **Incident Response** | Incidents link to sessions |
| **CI/CD** | Deployments tagged with session |

---

*Windsurf Black Box - Session Management Workflow v1.0*
