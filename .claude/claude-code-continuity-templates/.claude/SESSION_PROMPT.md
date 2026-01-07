# Claude Code Session Prompt

> **Purpose:** This file contains the standard prompt to use when starting each Claude Code session for maximum context efficiency and minimal token waste.

---

## 🚀 Quick Start Prompt (Recommended)

**Copy-paste this to start your session:**

```
Session initialization:
1. Read .claude/PROJECT_STATE.md
2. Review git status and recent commits
3. Confirm understanding of current objective and next steps

Keep response brief - just verify context loaded and propose next action.
```

---

## 📋 Detailed Start Prompt (For Complex Projects)

**Use when returning after long breaks or major changes:**

```
New session - context loading:

1. Read .claude/PROJECT_STATE.md completely
2. Check git status: current branch, uncommitted changes
3. Review last 5 commits: git log -5 --oneline
4. Identify any blockers or issues from state file
5. Verify understanding of:
   - Current objective
   - Work completed
   - Work in progress
   - Prioritized next steps

After loading context, provide:
- One-sentence summary of where we are
- Confirmation of next immediate action
- Any questions about unclear state

Keep initial response under 150 words.
```

---

## 🎯 Focused Task Prompt (Minimal Context)

**When you know exactly what to work on:**

```
Continue: [specific task description]

Context: Read relevant sections from .claude/PROJECT_STATE.md
Next: [exact next step]

Skip summary, proceed directly.
```

---

## 🔧 Debugging/Investigation Prompt

**When something isn't working:**

```
Debug session:
1. Read .claude/PROJECT_STATE.md - check "Known Issues"
2. Current problem: [describe issue]
3. What we tried: [from state file or your knowledge]
4. Git status and recent changes

Propose diagnostic steps.
```

---

## 📊 Status Check Prompt

**Quick status without taking action:**

```
Status check only:
1. Read .claude/PROJECT_STATE.md
2. Summarize current state in 3 bullets
3. Confirm next priority action
4. Highlight any blockers

No code changes - just verification.
```

---

## 🔄 Mid-Session State Refresh

**Use every 45-60 minutes during long sessions:**

```
Mid-session refresh:
1. What have we completed in last hour?
2. Update .claude/PROJECT_STATE.md:
   - Move completed items to "What Was Just Completed"
   - Update "What's In Progress"
   - Reprioritize "What's Next"
3. Commit state update

Keep us on track for rate limits.
```

---

## 💡 Best Practices

### Token Efficiency
- ✅ **DO:** Reference state file instead of explaining context
- ✅ **DO:** Use bullet points for context confirmation
- ✅ **DO:** Request brief responses initially
- ❌ **DON'T:** Re-explain project in every message
- ❌ **DON'T:** Ask Claude to explain what it already knows from state

### State File Maintenance
- Update state file every major milestone
- Document decisions with rationale (saves future token waste)
- Keep "What's Next" current and prioritized
- Record blockers immediately

### Session Continuity
- Always start with state file read
- End sessions with updated state
- Git commit state changes regularly
- Keep state file under 500 lines (archive old sessions)

---

## 🎓 Example Session Flow

### Session Start
```
You: "Session init: read .claude/PROJECT_STATE.md and confirm next action"

Claude: "✓ Context loaded. Working on: JWT middleware implementation
         Last session: completed database schema, user model
         Next: finish middleware validation logic
         Continue?"

You: "Yes, proceed"
```

### Session End
```
You: "Update state file with progress, then run close-session.sh"

Claude: [updates state file]
        "✓ Updated state - completed middleware, added tests
         Next session: integrate with auth routes
         Run ./claude/close-session.sh"
```

---

## 🔑 Key Phrases That Work Well

**High Efficiency:**
- "Read state and continue"
- "Status check from state file"
- "Update state: [changes]"
- "Proceed with next priority"

**Medium Efficiency:**
- "Review state file and propose approach for [task]"
- "Check state for context on [issue]"

**Low Efficiency (Avoid):**
- "Can you remind me what we were working on?"
- "What's the status of the project?"
- "Tell me about our progress"

---

## 📝 Template Customization

Adapt these prompts to your workflow:

1. **Your project type:** Add framework-specific checks
2. **Your rate limits:** Adjust session length guidance
3. **Your preferences:** Add your communication style
4. **Your tools:** Include your specific commands

---

## 🚨 Emergency Session Recovery

**If state file is lost or corrupted:**

```
Emergency recovery:
1. Check git log for state file history
2. Review last 10 commits for context
3. List modified files: git status
4. Rebuild minimal state from commits
5. Ask me to fill gaps in context

Priority: Get us functional, refine later.
```

---

_Last Updated: 2025-01-04_  
_Version: 1.0_
