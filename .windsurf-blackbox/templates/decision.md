# Decision Record Template

Use this template to document significant architectural, technical, or process decisions.

---

## Decision Record: DEC-[NNN]

### Metadata

| Field | Value |
|-------|-------|
| **ID** | DEC-[NNN] |
| **Session** | CONV-[ID] |
| **Date** | [YYYY-MM-DD] |
| **Status** | 🟡 Proposed / 🟢 Accepted / 🔴 Deprecated / 🔄 Superseded |
| **Deciders** | [Who made this decision] |
| **Supersedes** | [DEC-ID if replacing another] |
| **Superseded by** | [DEC-ID if this was replaced] |

---

### Title

[One-line description of the decision]

---

### Context

**What is the background?**
[Describe the situation that led to this decision. Include relevant history, constraints, and requirements.]

**Why does this decision need to be made now?**
[What triggered this decision point? What happens if we don't decide?]

---

### Problem Statement

[Clearly articulate the specific problem or question being addressed]

---

### Decision Drivers

What factors are most important in making this decision?

- **[Driver 1]**: [Why this matters]
- **[Driver 2]**: [Why this matters]
- **[Driver 3]**: [Why this matters]

Priority order: [Driver X] > [Driver Y] > [Driver Z]

---

### Options Considered

#### Option A: [Name]

**Description:** [What this option entails]

| Pros | Cons |
|------|------|
| [Pro 1] | [Con 1] |
| [Pro 2] | [Con 2] |

**Estimated effort:** [Low/Medium/High]
**Risk level:** [Low/Medium/High]

---

#### Option B: [Name]

**Description:** [What this option entails]

| Pros | Cons |
|------|------|
| [Pro 1] | [Con 1] |
| [Pro 2] | [Con 2] |

**Estimated effort:** [Low/Medium/High]
**Risk level:** [Low/Medium/High]

---

#### Option C: [Name] (if applicable)

**Description:** [What this option entails]

| Pros | Cons |
|------|------|
| [Pro 1] | [Con 1] |
| [Pro 2] | [Con 2] |

**Estimated effort:** [Low/Medium/High]
**Risk level:** [Low/Medium/High]

---

### Decision

**Chosen option:** [Option X]

**Rationale:**
[Explain why this option was selected. Reference the decision drivers and explain how this option best satisfies them.]

---

### Consequences

#### Positive
- [Benefit 1]
- [Benefit 2]

#### Negative
- [Drawback 1]
- [Drawback 2]

#### Neutral
- [Side effect 1]
- [Side effect 2]

---

### Implementation

**Action items:**
- [ ] [Task 1]
- [ ] [Task 2]
- [ ] [Task 3]

**Timeline:** [When will this be implemented?]

**Dependencies:** [What needs to happen first?]

---

### Validation

**How will we know this was the right decision?**

| Success Metric | Target | Measurement Method |
|----------------|--------|-------------------|
| [Metric 1] | [Target] | [How to measure] |
| [Metric 2] | [Target] | [How to measure] |

**Review date:** [When to evaluate this decision]

---

### Reversibility

| Aspect | Assessment |
|--------|------------|
| **Technical reversibility** | Easy / Moderate / Difficult / Irreversible |
| **Cost to reverse** | Low / Medium / High |
| **Time to reverse** | [Estimate] |
| **Point of no return** | [When reversal becomes impractical] |

---

### Related

- **Related decisions:** [DEC-XXX, DEC-YYY]
- **Related sessions:** [CONV-XXX, CONV-YYY]
- **Related documentation:** [Links]
- **Related issues:** [Issue IDs]

---

### Notes

[Any additional context, caveats, or information for future reference]

---

### History

| Date | Change | By |
|------|--------|-----|
| [Date] | Created | [Name] |
| [Date] | [Change description] | [Name] |

---

*Windsurf Black Box - Decision Record Template v1.0*
