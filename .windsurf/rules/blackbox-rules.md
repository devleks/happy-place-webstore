# Windsurf Black Box - Cascade Rules

## Session Awareness

When working in this project, you are operating within the Windsurf Black Box documentation system. This means:

1. **Session Tracking**: Every significant development session should be tracked
2. **Decision Documentation**: All architectural and technical decisions need rationale
3. **Issue Logging**: Problems encountered should be documented with solutions
4. **Continuity Focus**: Work should be documented for future continuation

## Session Protocol

### At Session Start
When the user starts a new development session or says "start session", "begin work", or similar:

1. Check for active session: `cat .windsurf-blackbox/.temp/current-session 2>/dev/null`
2. If no active session, suggest running: `./blackbox.sh start "[topic]"`
3. Acknowledge the session ID and commit to tracking under it

### During Session
Track these automatically when they occur:

- **ACTIONS**: Any significant code changes, file operations, or commands
- **DECISIONS**: Choices between alternatives, architecture decisions, technology picks
- **ISSUES**: Bugs encountered, errors, problems and their resolutions
- **CHECKPOINTS**: Before risky operations or major changes

Format for logging:
```
[SESSION-ID] Log [TYPE]: [description]
```

### At Session End
When the user says "end session", "done for today", "wrap up", or similar:

1. Generate a session summary
2. List all decisions made with rationale
3. Document current state (branch, tests, build)
4. Create action items for next session
5. Generate continuation prompt
6. Suggest running: `./blackbox.sh end`

## Cascade Commands

Respond to these natural language commands:

| User Says | Action |
|-----------|--------|
| "start session [topic]" | Run `./blackbox.sh start "[topic]"` |
| "end session" | Generate summary, run `./blackbox.sh end` |
| "log action: [X]" | Run `./blackbox.sh action "[X]"` |
| "log decision: [X] because [Y]" | Run `./blackbox.sh decision "[X]" "[Y]"` |
| "log issue: [X]" | Run `./blackbox.sh issue "[X]"` |
| "checkpoint: [X]" | Run `./blackbox.sh checkpoint "[X]"` |
| "milestone: [X]" | Run `./blackbox.sh milestone "[X]"` |
| "show status" | Run `./blackbox.sh status` |
| "search sessions for [X]" | Run `./blackbox.sh search "[X]"` |
| "show recent sessions" | Run `./blackbox.sh list` |
| "what's the current session?" | Read `.windsurf-blackbox/.temp/current-session` |
| "continue from last session" | Load continuation prompt from last session |

## Auto-Suggestions

Cascade should proactively suggest Black Box actions when:

1. **Major decision made**: "Would you like me to log this decision?"
2. **Bug fixed**: "Should I log this issue and resolution?"
3. **Significant code complete**: "This seems like a good checkpoint. Create one?"
4. **Before risky operation**: "Consider creating a checkpoint first?"
5. **Session running long**: "Your session has been active for 2+ hours. Status check?"

## Session Summary Format

When generating session summaries, use this format:

```markdown
## Session Summary: [SESSION-ID]

### Accomplished
- [List of completed items]

### Decisions Made
| Decision | Rationale |
|----------|-----------|
| [What] | [Why] |

### Issues Resolved
| Issue | Resolution |
|-------|------------|
| [Problem] | [Solution] |

### Current State
- Branch: [branch]
- Build: [passing/failing]
- Tests: [status]
- Uncommitted: [yes/no]

### Action Items (Next Session)
1. [Priority 1]
2. [Priority 2]
3. [Priority 3]

### Continuation Prompt
[Generate full continuation prompt for next session]
```

## File Locations

Important Black Box locations:
- Scripts: `.windsurf-blackbox/scripts/blackbox.sh`
- Sessions: `.windsurf-blackbox/sessions/`
- Catalog: `.windsurf-blackbox/catalog/index.md`
- Templates: `.windsurf-blackbox/templates/`
- Current Session: `.windsurf-blackbox/.temp/current-session`
- Session Log: `.windsurf-blackbox/.temp/session-log`

## Integration with Workflows

The Black Box integrates with Tier 1 workflows. When executing these workflows, include session tracking:

- **Code Review**: Log review decisions and findings
- **Security Audit**: Log vulnerabilities and remediation
- **Incident Response**: Auto-create incident sessions
- **API Design**: Log design decisions
- **Git Operations**: Reference session in commits

## Reminders

- Reference session ID in significant git commits
- Update SSOT when major decisions are made
- Create checkpoints before refactoring
- Generate continuation prompts for complex work
- Rebuild catalog periodically: `./blackbox.sh catalog`
