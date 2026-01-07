# 🚀 START HERE - Claude Code Session Guide

> **Quick Reference:** Everything you need to start, maintain, and close Claude Code sessions efficiently.

---

## ⚡ Quick Start (30 Seconds)

### First Time Setup
```bash
# 1. Make scripts executable
chmod +x .claude/close-session.sh
chmod +x .claude/open-session.sh

# 2. Copy template (if not already done)
# PROJECT_STATE.md should already exist

# 3. Initialize your project state
# Edit .claude/PROJECT_STATE.md with your current context
```

### Every Session Start
```bash
# 1. Run the opener (optional but helpful)
./.claude/open-session.sh

# 2. Copy the initialization prompt it shows
# OR use this minimal version:
```

**Paste into Claude Code:**
```
Session init: read .claude/PROJECT_STATE.md and continue
```

---

## 📋 Session Checklist

### ✅ Before Starting Session

- [ ] Pull latest changes: `git pull`
- [ ] Check state file: `cat .claude/PROJECT_STATE.md`
- [ ] Review last session notes (in state file)
- [ ] Run: `./.claude/open-session.sh` (optional)
- [ ] Start Claude Code with init prompt

### ✅ During Session (Every 30-45 min)

- [ ] Update state file with progress
- [ ] Document any key decisions made
- [ ] Note any blockers encountered
- [ ] Check remaining rate limit

### ✅ Before Closing Session

- [ ] Update "What Was Just Completed"
- [ ] Update "What's In Progress"
- [ ] Update "What's Next" (prioritized)
- [ ] Document any new decisions or context
- [ ] Run: `./.claude/close-session.sh`
- [ ] Follow script prompts

---

## 🎯 Session Templates

### Standard Session
```
Session init: read .claude/PROJECT_STATE.md and continue from [current task]
```

### After Long Break
```
Full context load:
1. Read .claude/PROJECT_STATE.md
2. Review last 5 commits
3. Check for uncommitted changes
4. Summarize current state and next action
```

### Quick Bug Fix
```
Quick fix session:
- Issue: [describe problem]
- Read relevant context from .claude/PROJECT_STATE.md
- Propose solution
```

### Feature Implementation
```
Feature work:
- Feature: [name]
- Context: .claude/PROJECT_STATE.md section [X]
- Next: [specific implementation step]
```

---

## 🛠️ Common Commands

### Git Operations
```bash
# Check status
git status

# Recent commits
git log -5 --oneline

# Current branch
git branch --show-current

# Uncommitted changes detail
git diff
```

### State Management
```bash
# View current state
cat .claude/PROJECT_STATE.md

# Edit state
nano .claude/PROJECT_STATE.md
# OR
code .claude/PROJECT_STATE.md

# View session history
cat .claude/session.log

# View state backups
ls -lt .claude/backups/
```

### Session Scripts
```bash
# Start session (info display)
./.claude/open-session.sh

# End session (save state)
./.claude/close-session.sh

# Make executable (if needed)
chmod +x .claude/*.sh
```

---

## 💡 Pro Tips

### Token Efficiency
1. **Always reference state file first** - Don't re-explain context
2. **Keep responses focused** - Ask Claude for brief confirmations
3. **Update state incrementally** - Don't wait for session end
4. **Document decisions immediately** - Saves tokens later

### State File Hygiene
1. **Archive old sessions** - Move to separate history file after 10 sessions
2. **Keep current info at top** - Push old context down
3. **Be specific in "What's Next"** - Vague tasks waste tokens
4. **Include code snippets** - Better than explaining code patterns

### Rate Limit Management
1. **Watch your usage** - Claude Code shows remaining calls
2. **Close at 75% usage** - Don't hit the limit
3. **Plan work in chunks** - Know what you'll accomplish per session
4. **Use state updates** - As natural breaking points

### Git Integration
1. **Commit state regularly** - After major milestones
2. **Include in PR context** - Helps reviewers understand evolution
3. **Tag important states** - For release points
4. **Branch-specific states** - For long-running features

---

## 🎓 Session Flow Example

### 1. Starting Session
```bash
$ ./.claude/open-session.sh
# Review output
# Copy the initialization prompt

# In Claude Code:
"Session init: read .claude/PROJECT_STATE.md and continue"
```

### 2. Claude's Response
```
✓ Context loaded
Current: Implementing user authentication
Last completed: Database schema, user model
In progress: JWT middleware (60% done)
Next: Finish validation, add tests

Ready to continue with middleware validation?
```

### 3. Working
```
You: "Yes, proceed with validation logic"
Claude: [implements code]

You: [every 30-45 min] "Update state file with progress"
Claude: [updates .claude/PROJECT_STATE.md]
```

### 4. Ending Session
```
You: "Session ending - final state update"
Claude: [updates state with completed work]

$ ./.claude/close-session.sh
# Follow prompts
# ✅ Safe to close
```

---

## 🚨 Troubleshooting

### "State file not found"
```bash
# Copy template
cp .claude/PROJECT_STATE.md.template .claude/PROJECT_STATE.md
# Fill in your project details
```

### "Scripts not executable"
```bash
chmod +x .claude/*.sh
```

### "Lost my place in project"
```bash
# Check last session
tail -50 .claude/PROJECT_STATE.md

# Check recent commits
git log -10 --oneline

# Check backups
cat .claude/backups/PROJECT_STATE_[latest].md
```

### "Too much state file bloat"
```bash
# Archive old sessions
mkdir .claude/archive
tail -200 .claude/PROJECT_STATE.md > .claude/PROJECT_STATE.md.tmp
mv .claude/PROJECT_STATE.md .claude/archive/PROJECT_STATE_$(date +%Y%m%d).md
mv .claude/PROJECT_STATE.md.tmp .claude/PROJECT_STATE.md
```

### "Forgot to update state before closing"
```bash
# Check last backup
ls -lt .claude/backups/
# Restore if needed
cp .claude/backups/PROJECT_STATE_[timestamp].md .claude/PROJECT_STATE.md
# Update manually
```

---

## 📚 File Reference

| File | Purpose | When to Use |
|------|---------|-------------|
| `PROJECT_STATE.md` | Master state tracker | Always - this is your source of truth |
| `SESSION_PROMPT.md` | Prompt templates | When crafting session start messages |
| `close-session.sh` | Session closer | Before every session end |
| `open-session.sh` | Session opener | At every session start (optional) |
| `session.log` | Session history | For tracking patterns/debugging |
| `backups/` | State backups | When you need to recover |

---

## 🎯 Success Metrics

You'll know this system is working when:
- ✅ Sessions start in <30 seconds
- ✅ No time wasted re-explaining context
- ✅ Claude immediately knows where you are
- ✅ You never hit rate limits unexpectedly
- ✅ Handoffs between sessions are seamless
- ✅ You spend <5% of time on context management

---

## 🔄 Maintenance Schedule

### Daily
- Update state file during sessions
- Run close-session.sh at session end

### Weekly
- Review session.log for patterns
- Archive old session history
- Clean backup directory (auto-handled)

### Monthly
- Review state file template
- Update session prompts
- Optimize for your workflow

---

## 📞 Support

### Issues?
1. Check this START_HERE.md
2. Review SESSION_PROMPT.md for examples
3. Check .claude/session.log for errors
4. Review backups in .claude/backups/

### Customization?
All files in `.claude/` are yours to customize:
- Adjust scripts for your environment
- Add project-specific sections to state template
- Create custom prompt templates
- Modify session flow to your needs

---

## 🚀 Next Steps

1. **First Session:**
   - Fill out PROJECT_STATE.md with current project context
   - Start Claude Code with init prompt
   - Verify Claude understands context

2. **End First Session:**
   - Update state with what you accomplished
   - Run close-session.sh
   - Verify backup created

3. **Second Session:**
   - Run open-session.sh
   - Use init prompt
   - Confirm seamless continuation

4. **Optimize:**
   - Adjust templates for your workflow
   - Create custom prompts
   - Build muscle memory for the flow

---

**Remember:** The goal is to spend 0% of your Claude Code time explaining context and 100% building. This system gets you there.

---

_Quick Reference Version: 1.0_  
_Last Updated: 2025-01-04_
