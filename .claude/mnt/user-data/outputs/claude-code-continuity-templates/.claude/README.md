# Claude Code Session Continuity System

> **Eliminate context loss and token waste when Claude Code sessions reset due to rate limits.**

## 🎯 The Problem This Solves

When you hit Claude Code rate limits and close a session:
- ❌ Context is completely lost
- ❌ You waste 500+ tokens re-explaining where you were
- ❌ Claude forgets decisions, rationale, and current state
- ❌ 5-10 minutes of "catching up" every session
- ❌ Risk of repeating failed approaches

## ✅ The Solution

A lightweight, git-integrated state management system that:
- ✅ Preserves full context across session boundaries
- ✅ Reduces session startup to <30 seconds
- ✅ Eliminates token waste on re-explanations
- ✅ Maintains decision history and rationale
- ✅ Works seamlessly across machines
- ✅ Integrates with your git workflow

---

## 📦 What's Included

```
.claude/
├── PROJECT_STATE.md          # Main state tracker (your source of truth)
├── SESSION_PROMPT.md         # Prompt templates for different scenarios
├── START_HERE.md             # Quick reference guide (read this first!)
├── close-session.sh          # Script to run before closing session
├── open-session.sh           # Script to run when starting session
├── gitignore-additions.txt   # What to add to your .gitignore
├── README.md                 # This file
├── session.log              # Auto-generated session history
└── backups/                 # Auto-generated state backups
    └── PROJECT_STATE_*.md
```

---

## 🚀 Quick Start (5 Minutes)

### 1. Copy to Your Project

```bash
# Copy the .claude directory to your project root
cp -r .claude /path/to/your/project/

# Navigate to your project
cd /path/to/your/project

# Make scripts executable
chmod +x .claude/*.sh
```

### 2. Configure .gitignore

```bash
# Add recommended ignores to your .gitignore
cat .claude/gitignore-additions.txt >> .gitignore
```

**Recommended for solo developers:**
```gitignore
# Keep PROJECT_STATE.md in git for cross-machine access
.claude/session.log
.claude/temp/
.claude/*.tmp
.claude/backups/*.md
```

### 3. Initialize Your State

Edit `.claude/PROJECT_STATE.md` with your current project context:
- Current objective
- What you've completed
- What's in progress
- What's next
- Any critical context

### 4. Start Your First Session

```bash
# Run the session opener
./.claude/open-session.sh

# Copy the initialization prompt it displays
# Paste into Claude Code
```

**OR use this minimal prompt:**
```
Session init: read .claude/PROJECT_STATE.md and continue
```

### 5. End Your First Session

```bash
# Update .claude/PROJECT_STATE.md with progress
# Then run:
./.claude/close-session.sh
```

**That's it!** Your next session will pick up exactly where you left off.

---

## 📖 How to Use

### Every Session Start

**Option A: Full automation (recommended)**
```bash
./.claude/open-session.sh
# Copy the prompt it shows
# Paste into Claude Code
```

**Option B: Minimal (if in a hurry)**
```
Paste into Claude Code:
"Session init: read .claude/PROJECT_STATE.md and continue"
```

### During Sessions

**Every 30-45 minutes or after major milestones:**
1. Ask Claude to update PROJECT_STATE.md with progress
2. Keep "What's Next" current
3. Document any important decisions

**Example:**
```
Update state file:
- Completed: JWT middleware implementation
- In progress: Integration tests (50%)
- Next: Finish tests, then auth route integration
```

### Every Session End

```bash
# Ensure state is current
# Run the closer
./.claude/close-session.sh

# Follow prompts to save state
```

---

## 💡 Best Practices

### Token Efficiency

**DO:**
- ✅ Start sessions with state file reference
- ✅ Keep responses focused and brief initially
- ✅ Update state incrementally during work
- ✅ Document decisions with rationale

**DON'T:**
- ❌ Re-explain project context every message
- ❌ Let Claude summarize what's in state file
- ❌ Wait until session end to update state
- ❌ Forget to run close-session.sh

### State File Quality

**The better your state file, the less time wasted on context:**

1. **Be Specific in "What's Next"**
   - ❌ Bad: "Work on authentication"
   - ✅ Good: "Implement JWT token refresh logic in auth middleware"

2. **Document Decisions**
   - Include WHY you chose an approach
   - Note what you tried that didn't work
   - This prevents Claude from suggesting failed approaches

3. **Keep Critical Context Current**
   - API endpoints that changed
   - Important constraints
   - Dependencies or blockers

4. **Archive Old Sessions**
   - After ~10 sessions, move old history to separate file
   - Keep state file focused on current work

### Git Integration

**Recommended workflow:**

```bash
# When state represents a good checkpoint:
git add .claude/PROJECT_STATE.md
git commit -m "chore: update session state [skip ci]"

# Benefits:
# - State available on all machines
# - History of project evolution
# - Easy rollback if needed
# - Share context with team
```

---

## 🎓 Example Workflows

### Standard Development Session

```bash
# 1. Start
$ ./.claude/open-session.sh

# Claude Code:
"Session init: read .claude/PROJECT_STATE.md and continue"

Claude: "✓ Loaded. Working on: User auth. Next: JWT middleware tests. Continue?"

# 2. Work
You: "Yes, implement the tests"
[... work happens ...]

# 3. Mid-session update (45 min in)
You: "Update state: completed middleware tests, starting route integration"
Claude: [updates PROJECT_STATE.md]

# 4. End session
$ ./.claude/close-session.sh
✅ State saved, safe to close
```

### Quick Bug Fix

```bash
# Claude Code:
"Quick fix session:
- Issue: Login returns 401 even with valid credentials
- Read relevant context from .claude/PROJECT_STATE.md
- Check recent auth changes"

Claude: "✓ Checked state. Recent change: JWT secret rotation.
         Issue likely: old tokens invalid. Propose: clear token cache, force re-login"
```

### After Long Break (Days/Weeks)

```bash
# Claude Code:
"Full context load:
1. Read .claude/PROJECT_STATE.md
2. Review last 10 commits
3. Check uncommitted changes
4. Summarize project status and next steps"

Claude: [comprehensive summary]
        "Project is 75% complete. Currently implementing payment integration.
         Last session: finished Stripe webhook handlers.
         Next priority: Error handling and retry logic.
         1 blocker: Awaiting API key for production Stripe account.
         Ready to continue with error handling?"
```

---

## 🛠️ Advanced Features

### Automated State Updates

Add to your commit hooks:

```bash
# .git/hooks/pre-commit
#!/bin/bash
if [ -f ".claude/PROJECT_STATE.md" ]; then
    echo "Session: Auto-updated by git commit $(date)" >> .claude/PROJECT_STATE.md
fi
```

### Session Analytics

```bash
# View session patterns
cat .claude/session.log | grep "Session opened" | wc -l
# Total sessions

# Average session length (if you log end times)
# Custom analytics based on your workflow
```

### Multi-Branch State

```bash
# Create branch-specific state
cp .claude/PROJECT_STATE.md .claude/PROJECT_STATE_feature-auth.md

# Switch between states when switching branches
# (Automate with git hooks)
```

### Team Collaboration

**Shared state file approach:**
```bash
# Everyone commits PROJECT_STATE.md
# Team sees each other's progress
# Great for pair programming or handoffs
```

**Individual state approach:**
```bash
# Add PROJECT_STATE.md to .gitignore
# Keep templates in git
# Each person maintains their own state
```

---

## 📊 Measuring Success

You'll know it's working when:

| Metric | Before | After |
|--------|--------|-------|
| Session startup time | 5-10 min | <30 sec |
| Token waste on context | 500-1000 | <50 |
| Claude understands immediately | 50% | 95%+ |
| Repeat failed approaches | Common | Rare |
| Session continuity | Broken | Seamless |

---

## 🔧 Customization

### Adapt to Your Stack

**Python/Django project:**
```bash
# Add to PROJECT_STATE.md → Quick Reference
python manage.py runserver
python manage.py test
python manage.py makemigrations
```

**Node/React project:**
```bash
npm run dev
npm test
npm run build
```

**Your specific tools:**
- Add deployment commands
- Add testing commands
- Add debugging commands

### Adapt Prompts

Edit `SESSION_PROMPT.md` to match your communication style:
- More/less verbose
- Specific terminology
- Your preferred workflow

### Adapt Scripts

Scripts are plain bash - customize as needed:
- Different backup retention
- Custom git commit messages
- Integration with other tools
- Project-specific checks

---

## 🚨 Troubleshooting

### "Scripts don't run"
```bash
chmod +x .claude/*.sh
```

### "State file not found"
```bash
# Ensure you're in project root
pwd

# Check file exists
ls -la .claude/PROJECT_STATE.md
```

### "Claude doesn't remember context"
**Checklist:**
- ✓ Did you update state file before closing?
- ✓ Did you use init prompt when starting?
- ✓ Is state file detailed enough?
- ✓ Did you commit state if working across machines?

### "Too many backups"
```bash
# Auto-cleaned by close-session.sh (keeps last 10)
# Manual clean:
cd .claude/backups
ls -t | tail -n +11 | xargs rm -f
```

### "State file too large"
```bash
# Archive old sessions
mkdir .claude/archive
# Move old content to archive
# Keep only recent sessions in main state file
```

---

## 📚 File Reference

### Core Files (Edit These)

**PROJECT_STATE.md** - Your source of truth
- Update regularly during sessions
- Keep current work at top
- Archive old sessions periodically

**SESSION_PROMPT.md** - Prompt templates
- Reference for different scenarios
- Customize for your workflow
- Copy-paste ready prompts

### Reference Files (Read Only)

**START_HERE.md** - Quick reference
- Read this for daily usage
- Checklists and commands
- Troubleshooting guide

**README.md** - This file
- Complete documentation
- Setup instructions
- Best practices

### Scripts (Run These)

**open-session.sh** - Session starter
- Shows current project state
- Displays git status
- Provides init prompt

**close-session.sh** - Session closer  
- Updates state with timestamp
- Creates backup
- Commits state (optional)

### Auto-Generated (Don't Edit)

**session.log** - Session history
- Automatic timestamps
- Session open/close events
- Good for analytics

**backups/** - State backups
- Auto-created on close
- Last 10 kept automatically
- For recovery if needed

---

## 🎯 Pro Tips

1. **Update state during work, not just at end**
   - Makes close-session.sh faster
   - Prevents forgetting important context

2. **Be specific in "What's Next"**
   - Vague: "Work on API"
   - Specific: "Add pagination to /api/users endpoint"

3. **Document decision rationale**
   - Saves huge tokens later
   - Prevents repeating failed approaches

4. **Use state file as project documentation**
   - It naturally becomes a project journal
   - Great for reviews and handoffs

5. **Commit state at milestones**
   - Makes it available everywhere
   - Creates natural checkpoints

6. **Watch your rate limit usage**
   - Close session at 75% usage
   - Don't wait until you hit limit

---

## 🔄 Version History

**v1.0 (2025-01-04)**
- Initial release
- Core state management
- Session scripts
- Documentation templates

---

## 📞 Support & Feedback

This is a template system - customize it for your needs!

**Issues or improvements?**
- Modify scripts for your environment
- Adjust templates for your workflow
- Share improvements with team

**Success stories?**
- Document what works well
- Create custom templates
- Build on this foundation

---

## 🚀 Next Steps

1. **Complete setup** (5 min)
   - Copy to project
   - Configure .gitignore
   - Make scripts executable

2. **Initialize state** (5 min)
   - Fill out PROJECT_STATE.md
   - Document current context
   - Set current objective

3. **First session** (test it)
   - Run open-session.sh
   - Start Claude Code with prompt
   - Verify Claude has context

4. **First closure** (verify)
   - Update state with progress
   - Run close-session.sh
   - Check backup created

5. **Second session** (confirm success)
   - Run open-session.sh
   - Use init prompt
   - Verify seamless continuation

6. **Optimize** (ongoing)
   - Adjust for your workflow
   - Customize templates
   - Build muscle memory

---

**The goal: Spend 0% of Claude Code time on context management, 100% on building.**

This system gets you there. Happy coding! 🚀
