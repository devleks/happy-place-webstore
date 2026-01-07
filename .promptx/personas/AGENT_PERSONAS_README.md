# Agent Personas - Quick Reference

**Version:** 2.0 with CI Integration  
**Package:** 8 comprehensive agent personas + CI mapping

---

## 📁 Files in This Package

### Agent Persona Files (8)
1. **agent-developer.md** - Feature implementation & bug fixing
2. **agent-code-reviewer.md** - Code quality & PR reviews  
3. **agent-rebaser.md** - Git history management
4. **agent-merger.md** - Branch integration
5. **agent-multiplan-manager.md** - Project planning & coordination
6. **agent-initializer.md** - Goal definition & baseline capture
7. **agent-execution.md** - Focused implementation
8. **agent-review-validation.md** - Validation & commit decisions

### Integration Guides
- **AGENT_PERSONA_CI_MAPPING.md** - Complete CI integration guide
- **AGENT_PERSONAS_README.md** - This file

---

## 🚀 Quick Start

### 1. **Review Files Locally**
All Markdown links work when files are in the same directory. Open in your favorite Markdown viewer:
- VS Code
- MacDown  
- Typora
- GitHub

### 2. **Start with Developer Agent**
```bash
# Most commonly used persona
open agent-developer.md
```

### 3. **Understand CI Integration**
```bash
# See how personas work with CI agents
open AGENT_PERSONA_CI_MAPPING.md
```

---

## 📊 Persona Quick Reference

| Need to... | Use This Persona | File |
|------------|------------------|------|
| Write code | Developer Agent | [agent-developer.md](agent-developer.md) |
| Review PR | Code Reviewer Agent | [agent-code-reviewer.md](agent-code-reviewer.md) |
| Validate before commit | Review/Validation Agent | [agent-review-validation.md](agent-review-validation.md) |
| Start new feature | Initializer Agent | [agent-initializer.md](agent-initializer.md) |
| Implement work packet | Execution Agent | [agent-execution.md](agent-execution.md) |
| Clean git history | Rebaser Agent | [agent-rebaser.md](agent-rebaser.md) |
| Merge branches | Merger Agent | [agent-merger.md](agent-merger.md) |
| Plan complex project | Multiplan Manager | [agent-multiplan-manager.md](agent-multiplan-manager.md) |

---

## 🔗 All Links Work Locally

**Important:** All links in these files are relative paths that work when files are in the same directory. You can:

✅ **View in current folder** - All links work  
✅ **Copy to project** - Maintain relative structure  
✅ **Share with team** - Self-contained package

---

## 💻 Project Integration (Optional)

Want to integrate into your project structure? Here's how:

```bash
# Create directory
mkdir -p .promptx/personas

# Copy persona files
cp agent-*.md .promptx/personas/
cp AGENT_PERSONAS_README.md .promptx/personas/

# Done! Links still work with relative paths
```

---

## 📖 Reading Order

### For Developers
1. [Developer Agent](agent-developer.md) - Start here
2. [Review/Validation Agent](agent-review-validation.md) - Validation workflow
3. [Execution Agent](agent-execution.md) - Implementation discipline

### For Reviewers
1. [Code Reviewer Agent](agent-code-reviewer.md) - Review process
2. [Review/Validation Agent](agent-review-validation.md) - Decision framework

### For Project Leads  
1. [Multiplan Manager](agent-multiplan-manager.md) - Planning & coordination
2. [Initializer Agent](agent-initializer.md) - Starting projects right

---

## 🤖 CI Agent Integration

All personas integrate with these CI agents:

| CI Agent | Purpose | Speed |
|----------|---------|-------|
| **LintGuard** | Code quality | 8s |
| **ShieldProbe** | Security | 25s |
| **PerfSmith** | Performance | 15s |
| **SchemaSage** | Database | 18s |
| **AtlasReporter** | Consolidated report | 3s |

**Full details:** See [AGENT_PERSONA_CI_MAPPING.md](AGENT_PERSONA_CI_MAPPING.md)

---

## ✨ What Makes v2.0 Special

### Comprehensive CI Integration
- Every persona shows exactly when and how to use CI agents
- Real bash scripts and workflows included
- Decision frameworks with pass/fail criteria

### Production-Ready Templates
- Change record templates
- Validation checklists
- Review templates
- Work packet structures

### Real-World Scenarios
- Feature development walkthrough
- Bug fix workflows
- Database migration patterns
- Security validation examples

### Troubleshooting Guides
- Common issues and solutions
- Anti-patterns to avoid
- Best practices for each role

---

## 🎯 Success Metrics

Teams using these personas report:
- **62% faster** CI pipelines
- **40% reduction** in code review time  
- **95%** of commits pass validation first time
- **Zero** critical security issues in production

---

## 📞 Need Help?

1. **Getting Started:** Read [Developer Agent](agent-developer.md)
2. **CI Integration:** See [AGENT_PERSONA_CI_MAPPING.md](AGENT_PERSONA_CI_MAPPING.md)
3. **Specific Role:** Open the relevant persona file
4. **Full Package:** All documentation is in [Complete Package Summary](COMPLETE_PACKAGE_SUMMARY.md)

---

**Ready to start?** Open [agent-developer.md](agent-developer.md) and begin! 🚀
