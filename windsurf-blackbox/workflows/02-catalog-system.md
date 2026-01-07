# Session Catalog & Index System

Comprehensive searchable archive system for all Windsurf Black Box sessions. Creates multiple views and indexes for easy navigation and discovery.

---

## Catalog Architecture

```
.windsurf-blackbox/
├── catalog/
│   ├── index.md              ← Master index (all sessions)
│   ├── by-date/
│   │   ├── 2024-12.md        ← Monthly indexes
│   │   └── 2024-12-17.md     ← Daily indexes (optional)
│   ├── by-topic/
│   │   ├── authentication.md ← Topic clusters
│   │   ├── api-design.md
│   │   └── debugging.md
│   ├── by-status/
│   │   ├── active.md         ← Currently active
│   │   ├── complete.md       ← Finished sessions
│   │   └── archived.md       ← Old/archived
│   ├── decisions.md          ← All decisions across sessions
│   ├── issues.md             ← All issues across sessions
│   ├── timeline.md           ← Chronological narrative
│   └── search-tags.md        ← Tag-based index
└── sessions/
    └── CONV-*.md             ← Individual session files
```

---

## Master Index Template

```markdown
# 📚 Windsurf Black Box - Session Catalog

> Auto-generated catalog of all development sessions

## Quick Stats

| Metric | Value |
|--------|-------|
| Total Sessions | [COUNT] |
| Active Sessions | [COUNT] |
| Complete Sessions | [COUNT] |
| Total Decisions | [COUNT] |
| Total Issues | [COUNT] |
| Date Range | [FIRST] → [LAST] |
| Last Updated | [TIMESTAMP] |

---

## 🟢 Active Session

[If active session exists, show details]

**Session:** [CONV-ID]
**Started:** [TIMESTAMP]
**Topic:** [TOPIC]
**Branch:** [BRANCH]

[Link to session file]

---

## 📅 Recent Sessions

| Session ID | Date | Topic | Status | Key Outcomes |
|------------|------|-------|--------|--------------|
| [ID] | [DATE] | [TOPIC] | [STATUS] | [BRIEF] |
| ... | ... | ... | ... | ... |

---

## 🔍 Quick Navigation

### By Time Period
- [This Week](by-date/this-week.md)
- [This Month](by-date/2024-12.md)
- [All Time](timeline.md)

### By Topic
- [Authentication](by-topic/authentication.md)
- [API Design](by-topic/api-design.md)
- [Bug Fixes](by-topic/debugging.md)
- [Features](by-topic/features.md)
- [Refactoring](by-topic/refactoring.md)

### By Type
- [All Decisions](decisions.md)
- [All Issues](issues.md)
- [All Milestones](milestones.md)

### By Status
- [Active](by-status/active.md)
- [Complete](by-status/complete.md)
- [Archived](by-status/archived.md)

---

## 🏷️ Tags

[tag-cloud or list of all tags with counts]

---

## 📈 Activity Chart

```
Dec 2024
Week 1: ████████ (8 sessions)
Week 2: ████████████ (12 sessions)
Week 3: ██████ (6 sessions)
```

---

*Catalog generated: [TIMESTAMP]*
*Windsurf Black Box v1.0*
```

---

## Catalog Generation Workflow

### Phase 1: Scan Sessions

```bash
# Cascade prompt for session scanning
"Scan all files in .windsurf-blackbox/sessions/ and extract:
1. Session ID
2. Date
3. Topic (from ID or metadata)
4. Status (Active/Complete/Archived)
5. Duration
6. Key outcomes (from summary if exists)
7. Decisions made (count and list)
8. Issues encountered (count and list)
9. Tags/keywords
10. Related sessions (from links)

Output as structured data for catalog generation."
```

### Phase 2: Generate Indexes

**Master Index Generation:**
```bash
# Cascade prompt
"Using the session scan data, generate the master index.md with:
- Accurate statistics
- All sessions listed chronologically (newest first)
- Quick navigation links
- Tag cloud
- Activity visualization"
```

**Topic Index Generation:**
```bash
# Cascade prompt
"Group sessions by topic and generate topic index files:
1. Extract topic from session ID (after NNN-)
2. Cluster similar topics
3. Create by-topic/[topic].md for each cluster
4. Include all related sessions
5. Summarize key learnings per topic"
```

**Date Index Generation:**
```bash
# Cascade prompt
"Generate date-based indexes:
1. by-date/YYYY-MM.md for each month
2. Include daily breakdown
3. Show session density
4. Link to individual sessions"
```

### Phase 3: Cross-Reference

**Decision Registry:**
```markdown
# Decision Registry

All architectural and technical decisions across sessions.

## Index

| ID | Session | Decision | Rationale | Date |
|----|---------|----------|-----------|------|
| DEC-001 | CONV-X | [Decision] | [Why] | [Date] |

## By Category

### Architecture
- [DEC-001](sessions/CONV-X.md#dec-001): [Decision]

### Technology Choices
- [DEC-005](sessions/CONV-Y.md#dec-005): [Decision]

### Process
- [DEC-010](sessions/CONV-Z.md#dec-010): [Decision]
```

**Issue Tracker:**
```markdown
# Issue Tracker

All issues encountered and their resolutions.

## Statistics

| Status | Count |
|--------|-------|
| Resolved | [N] |
| Pending | [N] |
| Workaround | [N] |

## All Issues

| ID | Session | Issue | Status | Resolution |
|----|---------|-------|--------|------------|
| ISS-001 | CONV-X | [Problem] | ✅ | [How fixed] |

## By Type

### Build Issues
### Runtime Errors
### Configuration Problems
### Performance Issues
```

---

## Automation Script Enhancement

Add to `blackbox.sh`:

```bash
#───────────────────────────────────────────────────────────────────────────────
# CATALOG GENERATION
#───────────────────────────────────────────────────────────────────────────────

generate_full_catalog() {
    print_header "GENERATING FULL CATALOG"
    
    # Create catalog directories
    mkdir -p "$CATALOG_DIR/by-date"
    mkdir -p "$CATALOG_DIR/by-topic"
    mkdir -p "$CATALOG_DIR/by-status"
    
    local total=0
    local active=0
    local complete=0
    local total_decisions=0
    local total_issues=0
    local first_date=""
    local last_date=""
    
    # Temporary files for aggregation
    local temp_sessions=$(mktemp)
    local temp_decisions=$(mktemp)
    local temp_issues=$(mktemp)
    
    # Scan all sessions
    for session_file in "$SESSIONS_DIR"/CONV-*.md; do
        if [ ! -f "$session_file" ]; then
            continue
        fi
        
        total=$((total + 1))
        
        local filename=$(basename "$session_file" .md)
        local date=$(echo "$filename" | cut -d'-' -f2-4)
        local seq=$(echo "$filename" | cut -d'-' -f5)
        local topic=$(echo "$filename" | cut -d'-' -f6- | tr '-' ' ')
        
        # Track date range
        if [ -z "$first_date" ] || [[ "$date" < "$first_date" ]]; then
            first_date="$date"
        fi
        if [ -z "$last_date" ] || [[ "$date" > "$last_date" ]]; then
            last_date="$date"
        fi
        
        # Get status
        local status=$(grep "| Status |" "$session_file" | head -1 | sed 's/.*| //' | sed 's/ |.*//')
        if [[ "$status" == *"Active"* ]]; then
            active=$((active + 1))
        elif [[ "$status" == *"Complete"* ]]; then
            complete=$((complete + 1))
        fi
        
        # Count decisions and issues
        local dec_count=$(grep -c "^### DEC-" "$session_file" 2>/dev/null || echo "0")
        local iss_count=$(grep -c "^### ISS-" "$session_file" 2>/dev/null || echo "0")
        total_decisions=$((total_decisions + dec_count))
        total_issues=$((total_issues + iss_count))
        
        # Add to sessions list
        echo "$date|$filename|${topic:-N/A}|$status|$dec_count|$iss_count" >> "$temp_sessions"
        
        # Extract decisions
        grep -A3 "^### DEC-" "$session_file" 2>/dev/null | while read line; do
            echo "$filename|$line" >> "$temp_decisions"
        done
        
        # Extract issues
        grep -A3 "^### ISS-" "$session_file" 2>/dev/null | while read line; do
            echo "$filename|$line" >> "$temp_issues"
        done
    done
    
    # Generate master index
    cat > "$MASTER_INDEX" << EOF
# 📚 Windsurf Black Box - Session Catalog

> Auto-generated catalog of all development sessions

## Quick Stats

| Metric | Value |
|--------|-------|
| Total Sessions | $total |
| Active Sessions | $active |
| Complete Sessions | $complete |
| Total Decisions | $total_decisions |
| Total Issues | $total_issues |
| Date Range | $first_date → $last_date |
| Last Updated | $(get_timestamp) |

---

## 📅 All Sessions

| Session ID | Date | Topic | Status | Decisions | Issues |
|------------|------|-------|--------|-----------|--------|
EOF
    
    # Sort sessions by date (newest first) and add to index
    sort -t'|' -k1 -r "$temp_sessions" | while IFS='|' read date id topic status dec iss; do
        echo "| [$id](../sessions/$id.md) | $date | $topic | $status | $dec | $iss |" >> "$MASTER_INDEX"
    done
    
    cat >> "$MASTER_INDEX" << EOF

---

## 🔍 Quick Navigation

- [All Decisions](decisions.md)
- [All Issues](issues.md)
- [Timeline](timeline.md)

---

*Catalog generated: $(get_timestamp)*
*Windsurf Black Box v1.0*
EOF
    
    # Clean up
    rm -f "$temp_sessions" "$temp_decisions" "$temp_issues"
    
    print_success "Catalog generated: $total sessions indexed"
    echo "  Decisions: $total_decisions"
    echo "  Issues: $total_issues"
    echo "  Date range: $first_date → $last_date"
}
```

---

## Search System

### Search Prompts for Cascade

**Full-Text Search:**
```
"Search all sessions in .windsurf-blackbox/sessions/ for: [QUERY]

Return:
1. Matching session IDs
2. Relevant excerpts with context
3. Match count per session
4. Suggested related searches"
```

**Decision Search:**
```
"Find all decisions related to: [TOPIC]

Search criteria:
- Decision titles
- Rationale text
- Related context

Return chronologically with session links."
```

**Issue Search:**
```
"Find all issues related to: [ERROR/PROBLEM]

Search:
- Issue descriptions
- Error messages
- Resolutions

Group by: resolved vs pending"
```

### Search Tags System

```markdown
# Search Tags

Tags extracted from all sessions for quick filtering.

## Technology Tags
- `javascript` (15 sessions)
- `typescript` (12 sessions)
- `react` (10 sessions)
- `nodejs` (8 sessions)
- `postgresql` (5 sessions)

## Activity Tags
- `debugging` (20 sessions)
- `feature` (18 sessions)
- `refactor` (12 sessions)
- `hotfix` (5 sessions)
- `setup` (3 sessions)

## Component Tags
- `authentication` (8 sessions)
- `api` (7 sessions)
- `database` (6 sessions)
- `frontend` (15 sessions)
- `backend` (12 sessions)

## Status Tags
- `complete` (45 sessions)
- `active` (1 session)
- `blocked` (2 sessions)
```

---

## Timeline View

### Cascade Prompt for Timeline

```
"Generate a timeline narrative from all sessions in chronological order:

Format:
## [Month Year]

### [Date]
**[Session ID]** - [Topic]
[2-3 sentence summary of what happened]
Key outcomes: [bullet points]

Include:
- Major milestones
- Critical decisions
- Significant issues resolved
- Progress markers

Make it readable as a project history story."
```

### Timeline Template

```markdown
# Project Timeline

Chronological narrative of development sessions.

---

## December 2024

### Week 3 (Dec 15-21)

#### December 17, 2024

**CONV-2024-12-17-001-auth-refactor**
Completed major authentication system refactor. Migrated from session-based 
to JWT tokens for better scalability. Resolved 3 blocking issues related to 
token refresh logic.

Key outcomes:
- ✅ JWT implementation complete
- ✅ Token refresh working
- ✅ All auth tests passing
- 📋 Ready for security review

**CONV-2024-12-17-002-api-documentation**
Started API documentation sprint. Set up OpenAPI spec generation.
Documented 12 of 25 endpoints.

---

### Week 2 (Dec 8-14)

[Continue pattern...]

---

## November 2024

[Continue pattern...]
```

---

## Integration with Session Management

### Auto-Update Triggers

The catalog should update when:

1. **Session ends** → Add to catalog, update stats
2. **Decision logged** → Add to decision registry
3. **Issue logged** → Add to issue tracker
4. **Manual rebuild** → Full regeneration

### Cascade Commands for Catalog

| Command | Action |
|---------|--------|
| `"Update catalog with session [ID]"` | Incremental update |
| `"Rebuild full catalog"` | Complete regeneration |
| `"Generate timeline view"` | Create timeline.md |
| `"Search sessions for [query]"` | Full-text search |
| `"Show decision history for [topic]"` | Filtered decision view |
| `"List issues by status"` | Grouped issue view |

---

## Quick Reference

```
┌─────────────────────────────────────────────────────────────┐
│              CATALOG QUICK REFERENCE                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  REBUILD CATALOG                                            │
│  ───────────────                                            │
│  ./blackbox.sh catalog                                      │
│                                                             │
│  SEARCH SESSIONS                                            │
│  ───────────────                                            │
│  ./blackbox.sh search "query"                               │
│                                                             │
│  LIST RECENT                                                │
│  ───────────                                                │
│  ./blackbox.sh list 10                                      │
│                                                             │
│  VIEW INDEX                                                 │
│  ──────────                                                 │
│  Open: .windsurf-blackbox/catalog/index.md                  │
│                                                             │
│  FIND DECISIONS                                             │
│  ──────────────                                             │
│  grep -r "DEC-" .windsurf-blackbox/sessions/                │
│                                                             │
│  FIND ISSUES                                                │
│  ───────────                                                │
│  grep -r "ISS-" .windsurf-blackbox/sessions/                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

*Windsurf Black Box - Catalog System v1.0*
