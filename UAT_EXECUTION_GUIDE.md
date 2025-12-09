# UAT Execution Guide
## Happy Place Webstore - December 8, 2025

**Purpose:** Step-by-step instructions for executing User Acceptance Testing  
**Audience:** QA Engineers, DevOps, Project Managers  
**Prerequisites:** Technical knowledge of REST APIs, bash scripting, PostgreSQL

---

## Quick Start

### For Immediate Testing (After Scripts are Implemented)

```bash
# 1. Navigate to tests directory
cd tests

# 2. Run smoke tests (5 minutes)
./uat_smoke_tests.sh

# 3. If smoke tests pass, run regression tests (20 minutes)
./uat_regression_tests.sh

# 4. If regression tests pass, run full suite (4 hours)
./uat_comprehensive_2025.sh
```

---

## Pre-Execution Checklist

### Environment Preparation

#### Step 1: Verify Backend is Running
```bash
# Check if Flask server is running
curl -s http://127.0.0.1:5001/api/pos/health

# Expected response:
# {"success": true, "service": "POS API", "status": "healthy"}

# If not running:
cd backend
source venv/bin/activate
python app.py
```

#### Step 2: Verify Database State
```bash
# Connect to PostgreSQL
psql -U postgres -d happy_place_db

# Run verification queries:
SELECT COUNT(*) FROM customers;     -- Should return > 0
SELECT COUNT(*) FROM employees;     -- Should return >= 3
SELECT COUNT(*) FROM products;      -- Should return >= 11
SELECT COUNT(*) FROM pos_shifts;    -- Table should exist
SELECT COUNT(*) FROM promotions;    -- Table should exist (Phase 11)

# Expected: All queries return results without errors
```

#### Step 3: Verify Migrations Applied
```bash
# Check if latest migrations are applied
psql -U postgres -d happy_place_db -c "
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name IN ('promotions', 'system_settings', 'refresh_tokens')
"

# Expected: All three tables exist (from migrations 007 & 008)
```

#### Step 4: Verify Test Credentials
```bash
# Test manager login
curl -X POST "http://127.0.0.1:5001/api/auth/employee/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"manager@happyplace.co.ke","password":"manager123"}'

# Expected: Returns access_token

# Test cashier login
curl -X POST "http://127.0.0.1:5001/api/auth/employee/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"cashier@happyplace.co.ke","password":"cashier123"}'

# Expected: Returns access_token
```

#### Step 5: Create Database Backup
```bash
# CRITICAL: Always backup before UAT
pg_dump -U postgres happy_place_db > backup_pre_uat_$(date +%Y%m%d).sql

# Verify backup was created
ls -lh backup_pre_uat_*.sql
```

---

## Test Execution Workflow

### Phase 1: Smoke Tests (MANDATORY - 10 minutes)

**Purpose:** Verify system is operational before investing time in full testing.

```bash
cd tests
chmod +x uat_smoke_tests.sh
./uat_smoke_tests.sh
```

**Decision Point:**
- **If ALL smoke tests pass (5/5):** ✅ Proceed to Phase 2
- **If ANY smoke test fails:** ❌ STOP - Fix issues before continuing

**Common Smoke Test Failures:**

| Failure | Likely Cause | Fix |
|---------|--------------|-----|
| API Health Check | Backend not running | Start Flask server |
| Database Connectivity | PostgreSQL down | Start PostgreSQL service |
| Customer Auth | Seed data missing | Run `python seed.py` |
| Employee Auth | Wrong credentials | Verify seed.py created employees |
| Admin Dashboard | Migration not applied | Run migration 008 |

### Phase 2: Regression Tests (CRITICAL - 20 minutes)

**Purpose:** Verify that previously failed tests (from Dec 5 UAT) are now fixed.

```bash
./uat_regression_tests.sh
```

**Key Tests:**
- **REGR-001:** POS transaction creation (previously HTTP 400)
- **REGR-002:** Shift summary retrieval (previously HTTP 404)
- **REGR-003:** Complete POS workflow

**Decision Point:**
- **If both P0 tests pass:** ✅ Critical blockers resolved, proceed
- **If either P0 test fails:** 🚨 STOP - These are production blockers

**Debugging Failed Regression Tests:**

**REGR-001 Fails (POS Transaction):**
```bash
# Check stored procedure exists
psql -U postgres -d happy_place_db -c "
    SELECT proname FROM pg_proc 
    WHERE proname = 'sp_create_pos_transaction'
"

# Check for errors in backend logs
tail -f backend/logs/app.log

# Manually test the stored procedure
psql -U postgres -d happy_place_db -c "
    SELECT sp_create_pos_transaction(
        2,  -- employee_id
        1,  -- store_location_id
        1,  -- shift_id (must have open shift)
        'cash'::VARCHAR,
        '[{\"variant_id\": 1, \"quantity\": 1}]'::jsonb,
        NULL,  -- customer_id
        10000  -- cash_tendered
    )
"
```

**REGR-002 Fails (Shift Summary):**
```bash
# Verify route is registered
python -c "
from app import create_app
app = create_app()
for rule in app.url_map.iter_rules():
    if 'shifts' in str(rule):
        print(rule)
"

# Expected to see: /api/pos/shifts/<int:shift_id>

# Check if stored procedure exists
psql -U postgres -d happy_place_db -c "
    SELECT proname FROM pg_proc 
    WHERE proname = 'sp_get_shift_summary'
"
```

### Phase 3: Full Comprehensive Testing (4 hours)

**Purpose:** Complete validation of all features including Phase 10 & 11.

```bash
# Run with verbose output
./uat_comprehensive_2025.sh | tee uat_output_$(date +%Y%m%d).log
```

**Execution Tips:**
- Run during off-peak hours
- Monitor backend logs in parallel: `tail -f backend/logs/app.log`
- Keep database query log open: `tail -f /var/log/postgresql/postgresql-14-main.log`
- Take notes of any warnings or anomalies
- Don't interrupt - let it complete fully

---

## Test Execution Best Practices

### Pre-Test Preparation

1. **Environment Isolation**
   - Use dedicated test database (not production!)
   - Use test email addresses
   - Use test phone numbers
   - Flag all test data clearly

2. **Resource Monitoring**
   ```bash
   # Monitor backend CPU/memory
   top -p $(pgrep -f "python app.py")
   
   # Monitor PostgreSQL
   pg_stat_activity
   
   # Monitor disk space
   df -h
   ```

3. **Log Aggregation**
   ```bash
   # Tail all relevant logs
   tail -f backend/logs/app.log \
           backend/logs/error.log \
           /var/log/postgresql/*.log
   ```

### During Test Execution

1. **Progress Tracking**
   - Note timestamp of each test category start
   - Flag any tests taking >30 seconds
   - Document any unexpected warnings

2. **Error Investigation**
   - If test fails, capture full request/response
   - Check backend logs immediately
   - Check database state
   - Don't skip investigating - root cause needed

3. **Performance Notes**
   - Record any slow responses (>2 seconds)
   - Note if performance degrades over time
   - Check for memory leaks

### Post-Test Activities

1. **Results Review**
   ```bash
   # Check exit code
   echo $?
   
   # Review summary
   tail -50 uat_results_*.log
   
   # Open generated report
   cat UAT_RESULTS_$(date +%Y-%m-%d).md
   ```

2. **Failure Analysis**
   - Categorize failures: P0, P1, P2, P3
   - Identify patterns (all auth fails, all admin fails, etc.)
   - Determine if environment issue vs code issue

3. **Data Cleanup** (Optional - keep for audit)
   ```bash
   # If you want to clean up test data
   psql -U postgres -d happy_place_db -c "
       DELETE FROM customers WHERE email LIKE 'uat.%@test.com';
       DELETE FROM employees WHERE email LIKE 'uat.%@test.com';
       DELETE FROM products WHERE name LIKE 'UAT Test%';
   "
   ```

---

## Troubleshooting Guide

### Common Issues and Solutions

#### Issue 1: Connection Refused
```
Error: curl: (7) Failed to connect to 127.0.0.1 port 5001
```
**Solution:**
```bash
# Start backend server
cd backend
source venv/bin/activate
python app.py
```

#### Issue 2: Database Connection Error
```
Error: psycopg2.OperationalError: could not connect to database
```
**Solution:**
```bash
# Start PostgreSQL
sudo systemctl start postgresql

# Or on macOS:
brew services start postgresql@14
```

#### Issue 3: JSON Parsing Error
```
Error: json.decoder.JSONDecodeError: Expecting value
```
**Solution:**
- Check if API is returning HTML error page instead of JSON
- Verify Content-Type header is set correctly
- Check backend logs for 500 errors

#### Issue 4: Token Expired
```
Error: {"msg": "Token has expired"}
```
**Solution:**
- Tokens expire after defined period
- Re-authenticate to get new token
- Check if refresh token logic is working

#### Issue 5: Permission Denied (HTTP 403)
```
Error: {"error": "Manager or admin access required"}
```
**Solution:**
- Verify employee role in JWT token
- Use manager or admin credentials for admin endpoints
- Check role_permissions table for correct mappings

#### Issue 6: Missing Stored Procedure
```
Error: function sp_create_pos_transaction does not exist
```
**Solution:**
```bash
# Apply missing migrations
psql -U postgres -d happy_place_db -f backend/migrations/005_pos_enhancements.sql
psql -U postgres -d happy_place_db -f backend/migrations/007_fix_stored_procedures.sql
```

---

## Test Result Interpretation

### Understanding Pass Rates

| Pass Rate | Status | Interpretation | Action |
|-----------|--------|----------------|--------|
| 100% | ✅ Excellent | Production ready | Deploy with confidence |
| 95-99% | ✅ Good | Minor issues | Review failures, fix if critical |
| 90-94% | ⚠️ Acceptable | Some concerns | Fix P0/P1 issues before deploy |
| 85-89% | ⚠️ Marginal | Significant issues | Fix issues, re-test |
| <85% | ❌ Poor | Major problems | Do not deploy, fix issues |

### Priority-Based Decision Matrix

**P0 Failures (BLOCKING):**
- **Any P0 failure:** ❌ DO NOT DEPLOY
- **Examples:** Authentication broken, POS cannot process sales, data corruption
- **Action:** Fix immediately, re-run full UAT

**P1 Failures (HIGH):**
- **1-2 P1 failures:** ⚠️ Deploy with hotfix plan
- **3+ P1 failures:** ❌ Do not deploy yet
- **Examples:** Reports not working, some admin features broken, email notifications failing
- **Action:** Fix within 24-48 hours post-deployment

**P2 Failures (MEDIUM):**
- **Acceptable:** Up to 20% P2 failure rate
- **Examples:** Missing optional features, UI polish items, nice-to-have reports
- **Action:** Add to backlog, fix in next sprint

**P3 Failures (LOW):**
- **Acceptable:** Any amount
- **Examples:** Minor UI issues, optional enhancements, future features
- **Action:** Backlog for future consideration

---

## Production Deployment Checklist

### If UAT Results Are:

#### ✅ PASS (95%+ pass rate, no P0/P1 failures)

**Pre-Deployment:**
- [ ] Create production database backup
- [ ] Review all test results with stakeholders
- [ ] Update deployment documentation
- [ ] Prepare rollback plan
- [ ] Configure monitoring alerts

**Deploy:**
- [ ] Apply all migrations to production database
- [ ] Deploy backend with zero-downtime strategy
- [ ] Deploy frontend build to CDN/server
- [ ] Verify health checks pass
- [ ] Monitor error rates for 24 hours

**Post-Deployment:**
- [ ] Run smoke tests against production
- [ ] Monitor New Relic dashboards
- [ ] Check for errors in Sentry
- [ ] Verify key transactions working

#### ⚠️ MARGINAL (85-94% pass rate, or 1-2 P1 failures)

**Actions:**
- [ ] Document all failures in detail
- [ ] Get stakeholder approval for known issues
- [ ] Prepare hotfix plan for P1 issues
- [ ] Deploy with enhanced monitoring
- [ ] Have engineers on standby

#### ❌ FAIL (<85% pass rate, or any P0 failures)

**Actions:**
- [ ] DO NOT DEPLOY to production
- [ ] Categorize all failures (P0, P1, P2, P3)
- [ ] Create fix plan with timeline
- [ ] Fix P0 issues immediately
- [ ] Re-run UAT after fixes
- [ ] Reschedule deployment

---

## Test Data Guidelines

### Test Accounts

**Customer Test Account:**
- Email: `uat.customer@test.com`
- Password: `UATTest123!`
- Purpose: Customer journey testing
- Note: Created during UAT, can be deleted after

**Employee Test Accounts:**
- Manager: `uat.manager@test.com` (role: manager)
- Cashier: `uat.cashier@test.com` (role: cashier)
- Purpose: POS and admin testing
- Note: Created during UAT for role testing

**Production Accounts (Do NOT use for UAT):**
- Real customer accounts
- Production employee accounts
- Any account with real transaction history

### Test Products

**UAT Test Product:**
- Name: "UAT Test Product"
- SKU: "UAT-001"
- Category: Any
- Price: KSh 2,999
- Stock: 100 units
- **Important:** Clearly marked as test data

### Test Orders

**Generated During UAT:**
- Order numbers will have current date
- Use test customer account
- Mark with notes: "UAT Test Order"
- **Cleanup:** Optional - keep for audit trail or delete after UAT

---

## Monitoring During UAT

### Critical Metrics to Watch

1. **Backend Performance**
   ```bash
   # Monitor response times
   tail -f uat_results_*.log | grep "ms"
   
   # Watch for slow queries
   tail -f /var/log/postgresql/postgresql-14-main.log | grep "duration"
   ```

2. **Database Health**
   ```sql
   -- Active connections
   SELECT count(*) FROM pg_stat_activity;
   
   -- Long-running queries
   SELECT pid, age(clock_timestamp(), query_start), query 
   FROM pg_stat_activity 
   WHERE state != 'idle' 
   AND query NOT ILIKE '%pg_stat_activity%';
   
   -- Lock monitoring
   SELECT * FROM pg_locks WHERE NOT granted;
   ```

3. **Memory Usage**
   ```bash
   # Backend memory
   ps aux | grep "python app.py"
   
   # PostgreSQL memory
   ps aux | grep postgres
   ```

4. **Error Logs**
   ```bash
   # Backend errors
   tail -f backend/logs/error.log
   
   # Database errors
   tail -f /var/log/postgresql/postgresql-14-main.log | grep ERROR
   ```

### Performance Thresholds

| Operation | Warning | Critical |
|-----------|---------|----------|
| API Health Check | >500ms | >2000ms |
| Product Listing | >1000ms | >3000ms |
| Order Creation | >2000ms | >5000ms |
| POS Transaction | >1000ms | >3000ms |
| Admin Reports | >3000ms | >10000ms |

---

## Interpreting Test Output

### Understanding Test Result Codes

**✓ PASS (Green)**
- Test completed successfully
- All validations passed
- Response within expected time
- No warnings or anomalies

**✗ FAIL (Red)**
- Test did not complete successfully
- HTTP error code (4xx, 5xx)
- Unexpected response format
- Validation failed
- **Action Required:** Investigate immediately

**⚠ WARN (Yellow)**
- Test passed but with concerns
- Slower than expected
- Missing optional fields
- Deprecated API usage
- **Action:** Review, may need fixing

**⏭ SKIP (Blue)**
- Test not executed
- Dependency failed
- Feature not implemented
- Environment constraint
- **Action:** Note reason, may be acceptable

### Sample Output Interpretation

```
============================================
  COMPREHENSIVE UAT TEST SUITE
============================================

[SMOKE-001] API Health Check
✓ PASS - API responding in 45ms

[SMOKE-002] Database Connectivity  
✓ PASS - Database accessible, 11 products found

[REGR-001] POS Transaction Creation
✗ FAIL - HTTP 400: shift_id is required
  Response: {"success":false,"error":"shift_id is required"}
  
  ^^ CRITICAL FAILURE - POS system cannot process sales
  
[AUTH-005] Enable Employee 2FA
⚠ WARN - QR code generated but no backup codes returned
  
  ^^ Minor issue - feature mostly works
  
[ADMIN-033] Customer Report
⏭ SKIP - Depends on failed test AUTH-001

  ^^ Acceptable if AUTH-001 is not critical
```

### Reading the Final Summary

```
==============================================
  TEST SUMMARY
==============================================
Total Tests:  127
Passed:       118 (92.9%)
Failed:       5 (3.9%)
Warned:       3 (2.4%)
Skipped:      1 (0.8%)
Duration:     3847s (64 minutes)
==============================================

CRITICAL ISSUES: 1
- REGR-001: POS Transaction Creation still failing

HIGH PRIORITY ISSUES: 2
- AUTH-010: Logout all devices not working
- ADMIN-025: Employee performance metrics 404

RECOMMENDATION: DO NOT DEPLOY
- Fix P0 issue (POS Transactions) before production
- Fix or document P1 issues
==============================================
```

---

## After UAT Completion

### Step 1: Review Results Files

```bash
# Check what was generated
ls -lt uat_results_* UAT_RESULTS_*

# Review detailed log
less uat_results_20251208_034500.log

# Review summary report
cat UAT_RESULTS_2025-12-08.md

# Review JSON results (for analysis tools)
cat uat_results_20251208_034500.json | jq .
```

### Step 2: Categorize Failures

Create a failure analysis document:

```markdown
# UAT Failure Analysis

## P0 Failures (BLOCKING)
1. REGR-001: POS Transaction Creation
   - Impact: Cannot process sales
   - Root Cause: [TBD]
   - Fix ETA: [TBD]
   - Owner: [TBD]

## P1 Failures (HIGH)
...

## P2 Failures (MEDIUM)
...
```

### Step 3: Decision Meeting

**Attendees:** Product Owner, Tech Lead, QA Lead, DevOps

**Agenda:**
1. Review pass rate and critical failures
2. Discuss each P0 and P1 failure
3. Assess risk of deployment
4. Make GO/NO-GO decision
5. If GO: Define monitoring plan
6. If NO-GO: Define fix timeline and re-test plan

### Step 4: Communication

**If Deploying:**
```
Subject: UAT Complete - Production Deployment Approved

UAT Results Summary:
- Pass Rate: 95.2% (121/127 tests)
- P0 Failures: 0
- P1 Failures: 1 (non-blocking, hotfix planned)
- Risk Assessment: LOW

Deployment scheduled for: [DATE/TIME]
Rollback plan: [LINK]
Monitoring plan: [LINK]
```

**If Not Deploying:**
```
Subject: UAT Complete - Production Deployment BLOCKED

UAT Results Summary:
- Pass Rate: 87.4% (111/127 tests)
- P0 Failures: 2 (BLOCKING)
- Critical Issues:
  1. POS transaction creation failing
  2. Admin dashboard permissions error

Required Actions:
1. Fix P0 issues (ETA: 48 hours)
2. Re-run regression tests
3. Reschedule full UAT

Next UAT Date: [DATE]
```

---

## Rollback Procedure (If Issues Found Post-Deploy)

### Immediate Rollback

```bash
# 1. Stop current backend
sudo systemctl stop happy-place-backend

# 2. Restore previous version
git checkout <previous-release-tag>
sudo systemctl start happy-place-backend

# 3. Verify health
curl http://your-domain.com/api/pos/health

# 4. Notify team
```

### Database Rollback (If Migrations Applied)

```bash
# 1. Stop backend
sudo systemctl stop happy-place-backend

# 2. Restore database from backup
psql -U postgres -d happy_place_db < backup_pre_deploy.sql

# 3. Verify data integrity
psql -U postgres -d happy_place_db -c "SELECT COUNT(*) FROM orders"

# 4. Restart backend
sudo systemctl start happy-place-backend
```

---

## UAT Metrics & KPIs

### Test Coverage Metrics

**Coverage by Feature:**
- Authentication: 12/12 endpoints (100%)
- Customer Operations: 10/12 endpoints (83%)
- POS Operations: 13/15 endpoints (87%)
- Admin Dashboard: 52/59 endpoints (88%)
- GDPR: 5/5 operations (100%)

**Coverage by Priority:**
- P0 Critical: 15/15 scenarios (100%)
- P1 High: 45/50 scenarios (90%)
- P2 Medium: 35/40 scenarios (87%)
- P3 Low: 10/15 scenarios (67%)

### Quality Metrics

**Test Reliability:**
- Test script execution success rate: >99%
- False positive rate: <1%
- False negative rate: <0.1%

**Test Efficiency:**
- Smoke tests: 5-10 minutes
- Regression tests: 15-20 minutes
- Full suite: 3-4 hours
- Average test execution: 85 seconds

---

## Continuous Improvement

### After Each UAT Run

1. **Update Test Cases**
   - Add new features discovered
   - Remove obsolete tests
   - Improve test data quality
   - Enhance validation logic

2. **Optimize Performance**
   - Identify slow tests
   - Add parallel execution where possible
   - Optimize API interactions
   - Reduce redundant validations

3. **Enhance Reporting**
   - Add more metrics
   - Better categorization
   - Clearer recommendations
   - Historical comparison

4. **Documentation**
   - Update this guide with findings
   - Document new issues discovered
   - Share lessons learned
   - Create FAQs

---

## Integration with CI/CD

### Automated UAT in Pipeline

```yaml
# .github/workflows/uat.yml (example)
name: UAT Testing

on:
  pull_request:
    branches: [main]
  workflow_dispatch:

jobs:
  smoke-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start services
        run: docker-compose up -d
      - name: Run smoke tests
        run: ./tests/uat_smoke_tests.sh
      
  regression-tests:
    needs: smoke-tests
    runs-on: ubuntu-latest
    steps:
      - name: Run regression tests
        run: ./tests/uat_regression_tests.sh
      
  full-uat:
    needs: regression-tests
    runs-on: ubuntu-latest
    if: github.event_name == 'workflow_dispatch'
    steps:
      - name: Run comprehensive UAT
        run: ./tests/uat_comprehensive_2025.sh
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: uat-results
          path: |
            uat_results_*.log
            UAT_RESULTS_*.md
```

---

## Support & Escalation

### When to Escalate

**Escalate to Tech Lead if:**
- Smoke tests fail consistently for >30 minutes
- P0 regression tests still failing after fixes
- Test suite cannot complete due to environment issues
- Unclear what is causing failures

**Escalate to Product if:**
- Test results show product requirements not met
- GDPR compliance tests failing
- Business logic errors discovered
- Need to clarify expected behavior

### Escalation Template

```
Subject: UAT Issue - [P0/P1/P2] [Component] [Brief Description]

Test ID: [ID]
Failure Type: [P0/P1/P2]
Component: [Authentication/POS/Admin/etc]

Issue Description:
[What's failing]

Impact:
[Business impact]

Request:
[What you need - guidance, fix, clarification]

Logs:
[Attach relevant log snippets]
```

---

## Appendix

### A. Test Account Credentials

**Seeded Employees:**
| Role | Email | Password | Purpose |
|------|-------|----------|---------|
| Admin | admin@happyplace.co.ke | Admin123! | Full system access |
| Manager | manager@happyplace.co.ke | manager123 | Most UAT tests |
| Cashier | cashier@happyplace.co.ke | cashier123 | POS-only tests |

**Seeded Customers:**
| Name | Email | Password | Purpose |
|------|-------|----------|---------|
| Test Customer | test@example.com | TestPass123! | Customer journey |

### B. API Endpoint Quick Reference

**Authentication:**
- Customer Login: `POST /api/auth/customer/login`
- Employee Login: `POST /api/auth/employee/login`
- Refresh Token: `POST /api/auth/refresh`

**Products:**
- List Products: `GET /api/products`
- Get Product: `GET /api/products/:slug`

**Orders:**
- Create Order: `POST /api/orders`
- List Orders: `GET /api/orders`

**POS:**
- Start Shift: `POST /api/pos/shifts/start`
- Create Transaction: `POST /api/pos/transactions`
- Close Shift: `POST /api/pos/shifts/:id/close`

**Admin:**
- Dashboard: `GET /api/admin/dashboard/metrics`
- Inventory: `GET /api/admin/inventory`
- Orders: `GET /api/admin/orders`
- Customers: `GET /api/admin/customers`

### C. Common Error Messages

| Error | Meaning | Solution |
|-------|---------|----------|
| "shift_id is required" | Missing required field | Add shift_id to request |
| "Employee access required" | Not authenticated as employee | Use employee login |
| "Manager or admin access required" | Insufficient permissions | Use manager/admin account |
| "Token has expired" | JWT expired | Re-authenticate |
| "Transaction not found" | Invalid ID | Verify transaction exists |
| "Shift not found" | Invalid shift ID | Use valid shift from start_shift |

---

## Summary

This execution guide provides comprehensive instructions for:
- ✅ Running UAT test scripts
- ✅ Interpreting results
- ✅ Troubleshooting issues
- ✅ Making deployment decisions
- ✅ Post-UAT actions

**Remember:**
- Always backup before UAT
- Start with smoke tests
- Investigate failures immediately
- Don't deploy with P0 failures
- Document everything

**For Questions:**
- Review this guide
- Check test script comments
- Review test plan document
- Escalate if stuck

---

**Document Version:** 1.0  
**Created:** December 8, 2025  
**Status:** Ready for Use  
**Next Update:** After first UAT run (incorporate lessons learned)