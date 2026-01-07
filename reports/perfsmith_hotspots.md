# PerfSmith Code Hotspot Analysis
**Generated:** 2025-12-20T15:59:07Z

## Backend Analysis
### Large Python Files
- /Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend/venv/lib/python3.11/site-packages/idna/uts46data.py (8841 lines)
- /Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend/venv_broken_20251219_042353/lib/python3.11/site-packages/idna/uts46data.py (8841 lines)
- /Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend/venv/lib/python3.11/site-packages/pip/_vendor/idna/uts46data.py (8681 lines)
- /Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend/venv_broken_20251219_042353/lib/python3.11/site-packages/pip/_vendor/idna/uts46data.py (8681 lines)
- /Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend/venv/lib/python3.11/site-packages/sqlalchemy/sql/compiler.py (7655 lines)
- /Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend/venv/lib/python3.11/site-packages/pip_api/_vendor/pyparsing.py (7107 lines)
- /Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend/venv/lib/python3.11/site-packages/sqlalchemy/sql/selectable.py (6934 lines)
- /Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend/venv/lib/python3.11/site-packages/pyparsing/core.py (6730 lines)
- /Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend/venv_broken_20251219_042353/lib/python3.11/site-packages/pyparsing/core.py (6730 lines)
- /Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend/venv/lib/python3.11/site-packages/sqlalchemy/sql/schema.py (6118 lines)

## Frontend Analysis

## Recommendations
1. Break down files >500 lines into smaller modules
2. Consider code-splitting for large React components
3. Use React.lazy() for conditional components
4. Profile runtime performance with browser DevTools
- /Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend/venv/lib/python3.11/site-packages/idna/uts46data.py (8841 lines)
- /Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend/venv_broken_20251219_042353/lib/python3.11/site-packages/idna/uts46data.py (8841 lines)
- /Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend/venv/lib/python3.11/site-packages/pip/_vendor/idna/uts46data.py (8681 lines)
- /Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend/venv_broken_20251219_042353/lib/python3.11/site-packages/pip/_vendor/idna/uts46data.py (8681 lines)
- /Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend/venv/lib/python3.11/site-packages/sqlalchemy/sql/compiler.py (7655 lines)
- /Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend/venv/lib/python3.11/site-packages/pip_api/_vendor/pyparsing.py (7107 lines)
- /Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend/venv/lib/python3.11/site-packages/sqlalchemy/sql/selectable.py (6934 lines)
- /Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend/venv/lib/python3.11/site-packages/pyparsing/core.py (6730 lines)
- /Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend/venv_broken_20251219_042353/lib/python3.11/site-packages/pyparsing/core.py (6730 lines)
- /Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend/venv/lib/python3.11/site-packages/sqlalchemy/sql/schema.py (6118 lines)

## Frontend Analysis

## Recommendations
1. Break down files >500 lines into smaller modules
2. Consider code-splitting for large React components
3. Use React.lazy() for conditional components
4. Profile runtime performance with browser DevTools

---

## Bundle Analysis
> Bundle analysis was skipped. Run with `RUN_PERF_BUILD=1` to generate bundle size report.

To enable:
```bash
RUN_PERF_BUILD=1 ./ci_workflows/agent_perfsmith.sh
```
