# Continuation Prompt Template

Use this template to create prompts that allow seamless session continuation after any period of inactivity.

---

## Quick Continuation (5 minutes or less)

```
CONTINUING: CONV-[ID]
Last action: [what you were doing]
Next step: [immediate next action]
Key files: @[file1] @[file2]
```

---

## Standard Continuation (Hours to Days)

```
═══════════════════════════════════════════════════════════════
SESSION CONTINUATION: CONV-[ID]
═══════════════════════════════════════════════════════════════

Project: [Name]
Branch: [branch] @ [commit]

LAST SESSION SUMMARY:
[2-3 sentence summary]

CURRENT STATE:
- Build: [status]
- Tests: [status]
- Branch: [name] @ [sha]

IMMEDIATE CONTEXT:
[Where we stopped, what's in progress]

TODAY'S PRIORITY:
[Main goal from action items]

KEY FILES:
@[file1] @[file2] @[file3]

Please help me continue from where I left off.
═══════════════════════════════════════════════════════════════
```

---

## Full Continuation (Weeks to Months)

```
═══════════════════════════════════════════════════════════════
🔄 PROJECT CONTINUATION REQUEST
═══════════════════════════════════════════════════════════════

IDENTIFICATION:
- Project: [Name]
- Last Session: CONV-[ID]
- Time Since: [duration]
- Branch: [branch]

═══════════════════════════════════════════════════════════════
PROJECT CONTEXT
═══════════════════════════════════════════════════════════════

PURPOSE:
[What is this project/feature for?]

TECH STACK:
- Language: [X]
- Framework: [Y]
- Database: [Z]
- Key dependencies: [list]

ARCHITECTURE OVERVIEW:
[Brief description of system structure]

═══════════════════════════════════════════════════════════════
LAST SESSION SUMMARY
═══════════════════════════════════════════════════════════════

WHAT WAS ACCOMPLISHED:
1. [Achievement 1]
2. [Achievement 2]
3. [Achievement 3]

WHAT WAS IN PROGRESS:
[Specific work that was started but not finished]

KEY DECISIONS MADE:
1. [Decision 1] - Rationale: [why]
2. [Decision 2] - Rationale: [why]

OUTSTANDING ISSUES:
1. [Issue 1] - Status: [open/workaround]
2. [Issue 2] - Status: [open/workaround]

═══════════════════════════════════════════════════════════════
CURRENT STATE
═══════════════════════════════════════════════════════════════

REPOSITORY:
- Branch: [branch-name]
- Last commit: [sha] - "[message]"
- Uncommitted changes: [yes/no - details]

BUILD STATUS:
- Last build: [passing/failing]
- Known issues: [list]

TEST STATUS:
- Passing: [X]
- Failing: [Y]
- Skipped: [Z]

DEPENDENCIES:
- Last updated: [date]
- Known vulnerabilities: [count]

═══════════════════════════════════════════════════════════════
ACTION ITEMS (FROM LAST SESSION)
═══════════════════════════════════════════════════════════════

MUST DO:
- [ ] [Priority 1 task]
- [ ] [Priority 2 task]

SHOULD DO:
- [ ] [Task 3]
- [ ] [Task 4]

BLOCKED:
- [ ] [Task 5] - Waiting on: [what]

═══════════════════════════════════════════════════════════════
KEY FILES & LOCATIONS
═══════════════════════════════════════════════════════════════

MAIN ENTRY POINTS:
@[src/index.ts]
@[src/app.ts]

CURRENTLY ACTIVE:
@[src/features/auth/login.ts]
@[src/features/auth/middleware.ts]

CONFIG:
@[config/database.ts]
@[.env.example]

TESTS:
@[tests/auth.test.ts]

═══════════════════════════════════════════════════════════════
CONTEXT THAT MIGHT BE FORGOTTEN
═══════════════════════════════════════════════════════════════

IMPORTANT DETAILS:
- [Detail 1 that isn't obvious from code]
- [Detail 2 that future you needs to know]
- [Detail 3 about why something is done a certain way]

GOTCHAS:
- [Known issue or quirk 1]
- [Known issue or quirk 2]

RELATED RESOURCES:
- [Link to relevant doc]
- [Link to related issue/PR]

═══════════════════════════════════════════════════════════════
REQUEST
═══════════════════════════════════════════════════════════════

Please help me:
1. Understand current project state
2. Review what was accomplished
3. Continue with the highest priority action item

Start a new session: CONV-[NEW-ID]
Reference previous: CONV-[OLD-ID]

═══════════════════════════════════════════════════════════════
```

---

## New Developer Onboarding Continuation

Use when a different developer needs to continue:

```
═══════════════════════════════════════════════════════════════
👋 NEW DEVELOPER ONBOARDING
═══════════════════════════════════════════════════════════════

ABOUT ME:
- Name: [Developer name]
- Role: [Role]
- Experience with this stack: [level]
- Previous context: [none / some / reviewed docs]

PROJECT HANDOFF:
- Previous developer: [name]
- Handoff session: CONV-[ID]
- Documentation reviewed: [list]

WHAT I NEED:
1. Project overview
2. Architecture explanation
3. Current state summary
4. Priority task assignment
5. Known gotchas/issues

BLACK BOX SESSIONS TO REVIEW:
[List key sessions for context]

Please onboard me to this project.
═══════════════════════════════════════════════════════════════
```

---

## Emergency/Incident Continuation

For continuing from an incident:

```
═══════════════════════════════════════════════════════════════
🚨 INCIDENT CONTINUATION
═══════════════════════════════════════════════════════════════

INCIDENT: INC-[ID]
SESSION: CONV-[ID]
SEVERITY: [P0/P1/P2/P3]
STATUS: [active/mitigated/resolved]

TIMELINE:
[HH:MM] - Incident detected
[HH:MM] - [action taken]
[HH:MM] - Current state

CURRENT MITIGATION:
[What's in place to reduce impact]

NEEDS IMMEDIATE ATTENTION:
[What must be done next]

ROOT CAUSE STATUS:
[Identified / Investigating / Unknown]

Please help continue incident response.
═══════════════════════════════════════════════════════════════
```

---

## Tips for Effective Continuation Prompts

1. **Be specific** - Include exact file paths, commit SHAs, error messages
2. **Include rationale** - Explain WHY decisions were made, not just WHAT
3. **Note the non-obvious** - Document things that aren't clear from code
4. **Prioritize clearly** - Number action items by priority
5. **Reference sessions** - Link to related Black Box sessions
6. **Update regularly** - Refresh the prompt as work progresses

---

*Windsurf Black Box - Continuation Prompt Template v1.0*
