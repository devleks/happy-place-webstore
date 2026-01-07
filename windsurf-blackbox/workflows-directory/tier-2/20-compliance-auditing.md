# 20 - Compliance & Auditing Workflow

Comprehensive approach to maintaining regulatory compliance, implementing audit controls, and preparing for external audits across various frameworks (SOC 2, GDPR, HIPAA, PCI-DSS).

---

## Overview

This workflow establishes compliance controls, automates evidence collection, and ensures continuous audit readiness for common regulatory frameworks.

## When to Use

- Preparing for SOC 2/ISO 27001 certification
- GDPR/CCPA compliance implementation
- PCI-DSS compliance for payment processing
- HIPAA compliance for healthcare data
- Annual audit preparation
- New compliance requirement implementation

---

## Quick Start

```bash
./blackbox.sh start "compliance-[framework]-[scope]"
```

---

## Cascade Prompt

```
Execute Compliance & Auditing workflow for: [FRAMEWORK]

Framework: [SOC2/GDPR/HIPAA/PCI-DSS/ISO27001]
Scope: [full/specific-controls]
Timeline: [audit date or deadline]
Current state: [none/partial/maintaining]

Steps:
1. Identify applicable requirements
2. Gap analysis
3. Implement controls
4. Document policies
5. Collect evidence
6. Prepare for audit

Reference: workflows/tier-2/20-compliance-auditing.md
Session: [CURRENT-SESSION-ID]
```

---

## Compliance Framework Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                 COMMON COMPLIANCE FRAMEWORKS                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SOC 2                          GDPR                            │
│  ┌──────────────────┐          ┌──────────────────┐            │
│  │ Trust Services   │          │ Data Protection  │            │
│  │ • Security       │          │ • Consent        │            │
│  │ • Availability   │          │ • Data Rights    │            │
│  │ • Confidentiality│          │ • Breach Notice  │            │
│  │ • Processing     │          │ • DPO Required   │            │
│  │ • Privacy        │          │ • Cross-border   │            │
│  └──────────────────┘          └──────────────────┘            │
│                                                                 │
│  PCI-DSS                        HIPAA                          │
│  ┌──────────────────┐          ┌──────────────────┐            │
│  │ Payment Card     │          │ Healthcare Data  │            │
│  │ • Network Security│          │ • Privacy Rule   │            │
│  │ • Data Protection│          │ • Security Rule  │            │
│  │ • Access Control │          │ • Breach Rule    │            │
│  │ • Monitoring     │          │ • BAA Required   │            │
│  │ • Testing        │          │ • PHI Protection │            │
│  └──────────────────┘          └──────────────────┘            │
│                                                                 │
│  ISO 27001                      CCPA                           │
│  ┌──────────────────┐          ┌──────────────────┐            │
│  │ Info Security    │          │ California Privacy│            │
│  │ • Risk Assessment│          │ • Right to Know  │            │
│  │ • Asset Mgmt     │          │ • Right to Delete│            │
│  │ • Access Control │          │ • Opt-out Sale   │            │
│  │ • Cryptography   │          │ • Non-discrimin. │            │
│  │ • Operations     │          │ • Notice Required│            │
│  └──────────────────┘          └──────────────────┘            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Requirements Mapping

### SOC 2 Trust Services Criteria

```yaml
# soc2-requirements.yaml
trust_services:
  security:
    - id: CC1.1
      description: "Control environment demonstrates commitment to integrity"
      controls:
        - code_of_conduct
        - background_checks
        - security_training
        
    - id: CC2.1
      description: "Information and communication"
      controls:
        - security_policies
        - incident_communication
        - whistleblower_policy
        
    - id: CC3.1
      description: "Risk assessment and management"
      controls:
        - risk_register
        - risk_assessments
        - vulnerability_management
        
    - id: CC4.1
      description: "Monitoring activities"
      controls:
        - security_monitoring
        - log_review
        - metrics_dashboard
        
    - id: CC5.1
      description: "Control activities"
      controls:
        - access_controls
        - change_management
        - data_backup
        
    - id: CC6.1
      description: "Logical and physical access"
      controls:
        - authentication
        - authorization
        - physical_security
        
    - id: CC7.1
      description: "System operations"
      controls:
        - incident_response
        - business_continuity
        - vendor_management
        
    - id: CC8.1
      description: "Change management"
      controls:
        - change_control
        - testing_procedures
        - deployment_approval
        
    - id: CC9.1
      description: "Risk mitigation"
      controls:
        - insurance
        - contracts
        - contingency_plans

  availability:
    - id: A1.1
      description: "Capacity planning and performance"
      controls:
        - capacity_monitoring
        - scaling_procedures
        - sla_management

  confidentiality:
    - id: C1.1
      description: "Confidential information protection"
      controls:
        - data_classification
        - encryption
        - access_restrictions

  processing_integrity:
    - id: PI1.1
      description: "Processing accuracy and completeness"
      controls:
        - input_validation
        - processing_verification
        - output_reconciliation

  privacy:
    - id: P1.1
      description: "Privacy notice and consent"
      controls:
        - privacy_policy
        - consent_management
        - data_subject_rights
```

### GDPR Requirements Mapping

```yaml
# gdpr-requirements.yaml
articles:
  lawful_processing:
    article: 6
    requirements:
      - consent_mechanism
      - contract_necessity
      - legal_obligation
      - vital_interests
      - public_task
      - legitimate_interests
    controls:
      - consent_management_system
      - lawful_basis_documentation
      - legitimate_interest_assessment
      
  data_subject_rights:
    articles: [15, 16, 17, 18, 20, 21]
    requirements:
      - right_of_access
      - right_to_rectification
      - right_to_erasure
      - right_to_restriction
      - right_to_portability
      - right_to_object
    controls:
      - data_subject_request_process
      - automated_data_export
      - deletion_procedures
      
  security:
    article: 32
    requirements:
      - pseudonymization
      - encryption
      - confidentiality
      - integrity
      - availability
      - resilience
    controls:
      - encryption_at_rest
      - encryption_in_transit
      - access_controls
      - backup_procedures
      
  breach_notification:
    articles: [33, 34]
    requirements:
      - 72_hour_notification
      - risk_assessment
      - subject_notification
    controls:
      - incident_response_plan
      - breach_detection
      - notification_procedures
      
  data_protection_officer:
    article: 37
    requirements:
      - dpo_appointment
      - dpo_independence
      - dpo_expertise
    controls:
      - dpo_designation
      - dpo_contact_published
      
  international_transfers:
    articles: [44, 45, 46]
    requirements:
      - adequacy_decisions
      - standard_clauses
      - binding_rules
    controls:
      - transfer_impact_assessment
      - standard_contractual_clauses
      - data_localization
```

---

## Phase 2: Gap Analysis

### Gap Assessment Template

```markdown
## Compliance Gap Analysis

### Framework: [SOC 2 / GDPR / etc.]
### Assessment Date: [Date]
### Assessor: [Name]
### Session: [CONV-ID]

### Summary
| Status | Count | Percentage |
|--------|-------|------------|
| ✅ Compliant | XX | XX% |
| ⚠️ Partial | XX | XX% |
| ❌ Gap | XX | XX% |
| N/A | XX | XX% |

### Detailed Findings

#### Control: [Control ID] - [Control Name]

| Attribute | Value |
|-----------|-------|
| **Requirement** | [Description] |
| **Current State** | [What exists today] |
| **Gap** | [What's missing] |
| **Risk Level** | High / Medium / Low |
| **Remediation** | [What needs to be done] |
| **Effort** | [Estimate] |
| **Owner** | [Responsible party] |
| **Target Date** | [Deadline] |

### Priority Matrix

| Priority | Control | Gap | Effort | Target |
|----------|---------|-----|--------|--------|
| P1 | CC6.1 | No MFA | 2 weeks | Jan 15 |
| P1 | CC7.1 | No IR plan | 1 week | Jan 10 |
| P2 | CC5.1 | Manual backups | 3 weeks | Jan 30 |
| P3 | CC4.1 | Limited logging | 4 weeks | Feb 15 |
```

### Automated Gap Scanner

```python
# compliance_scanner.py
import yaml
from dataclasses import dataclass
from typing import List, Dict
from enum import Enum

class ComplianceStatus(Enum):
    COMPLIANT = "compliant"
    PARTIAL = "partial"
    GAP = "gap"
    NOT_APPLICABLE = "n/a"

@dataclass
class ControlAssessment:
    control_id: str
    description: str
    status: ComplianceStatus
    evidence: List[str]
    gaps: List[str]
    remediation: str
    priority: int

class ComplianceScanner:
    def __init__(self, framework: str):
        self.framework = framework
        self.requirements = self._load_requirements(framework)
        
    def _load_requirements(self, framework: str) -> Dict:
        with open(f"{framework}-requirements.yaml") as f:
            return yaml.safe_load(f)
    
    def assess_control(self, control_id: str) -> ControlAssessment:
        """Assess a single control against current implementation."""
        control = self._get_control(control_id)
        
        # Check for evidence
        evidence = self._collect_evidence(control)
        
        # Identify gaps
        gaps = self._identify_gaps(control, evidence)
        
        # Determine status
        if not gaps:
            status = ComplianceStatus.COMPLIANT
        elif len(gaps) < len(control['controls']) / 2:
            status = ComplianceStatus.PARTIAL
        else:
            status = ComplianceStatus.GAP
            
        return ControlAssessment(
            control_id=control_id,
            description=control['description'],
            status=status,
            evidence=evidence,
            gaps=gaps,
            remediation=self._suggest_remediation(gaps),
            priority=self._calculate_priority(gaps)
        )
    
    def _collect_evidence(self, control: Dict) -> List[str]:
        """Collect evidence for control implementation."""
        evidence = []
        
        # Check for policies
        if self._policy_exists(control):
            evidence.append("Policy documented")
            
        # Check for technical controls
        if self._technical_control_exists(control):
            evidence.append("Technical control implemented")
            
        # Check for monitoring
        if self._monitoring_exists(control):
            evidence.append("Monitoring in place")
            
        return evidence
    
    def full_assessment(self) -> Dict:
        """Run full compliance assessment."""
        results = {
            'framework': self.framework,
            'date': datetime.now().isoformat(),
            'summary': {'compliant': 0, 'partial': 0, 'gap': 0},
            'controls': []
        }
        
        for control_id in self._get_all_control_ids():
            assessment = self.assess_control(control_id)
            results['controls'].append(assessment)
            results['summary'][assessment.status.value] += 1
            
        return results

# Usage
scanner = ComplianceScanner('soc2')
report = scanner.full_assessment()
print(f"Compliance Score: {report['summary']['compliant']} / {len(report['controls'])}")
```

---

## Phase 3: Control Implementation

### Access Control Implementation

```typescript
// access-control.ts
import { Role, Permission, User } from './types';

// Role-Based Access Control (RBAC)
const roles: Record<string, Permission[]> = {
  admin: ['read', 'write', 'delete', 'admin'],
  developer: ['read', 'write'],
  viewer: ['read'],
  auditor: ['read', 'audit_log'],
};

// Attribute-Based Access Control (ABAC)
interface AccessPolicy {
  resource: string;
  action: string;
  conditions: {
    attribute: string;
    operator: 'equals' | 'contains' | 'in';
    value: unknown;
  }[];
}

const policies: AccessPolicy[] = [
  {
    resource: 'customer_data',
    action: 'read',
    conditions: [
      { attribute: 'user.department', operator: 'equals', value: 'support' },
      { attribute: 'resource.classification', operator: 'in', value: ['public', 'internal'] },
    ],
  },
  {
    resource: 'pii_data',
    action: 'read',
    conditions: [
      { attribute: 'user.pii_access', operator: 'equals', value: true },
      { attribute: 'request.purpose', operator: 'in', value: ['support', 'legal'] },
    ],
  },
];

// Access decision logging for audit
async function checkAccess(
  user: User,
  resource: string,
  action: string,
  context: Record<string, unknown>
): Promise<{ allowed: boolean; reason: string }> {
  const decision = evaluateAccess(user, resource, action, context);
  
  // Log for audit trail
  await auditLog.write({
    timestamp: new Date().toISOString(),
    user_id: user.id,
    user_email: user.email,
    resource,
    action,
    decision: decision.allowed ? 'ALLOW' : 'DENY',
    reason: decision.reason,
    context,
    ip_address: context.ip_address,
    user_agent: context.user_agent,
  });
  
  return decision;
}
```

### Encryption Implementation

```typescript
// encryption.ts
import crypto from 'crypto';
import { KMS } from '@aws-sdk/client-kms';

const kms = new KMS({ region: process.env.AWS_REGION });

// Encryption at rest
class DataEncryption {
  private algorithm = 'aes-256-gcm';
  
  async encrypt(plaintext: string, context: Record<string, string>): Promise<{
    ciphertext: string;
    encryptedKey: string;
    iv: string;
    tag: string;
  }> {
    // Generate data encryption key from KMS
    const { Plaintext, CiphertextBlob } = await kms.generateDataKey({
      KeyId: process.env.KMS_KEY_ID,
      KeySpec: 'AES_256',
      EncryptionContext: context,
    });
    
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipheriv(this.algorithm, Plaintext!, iv);
    
    let ciphertext = cipher.update(plaintext, 'utf8', 'base64');
    ciphertext += cipher.final('base64');
    
    const tag = cipher.getAuthTag();
    
    // Clear plaintext key from memory
    Plaintext!.fill(0);
    
    return {
      ciphertext,
      encryptedKey: CiphertextBlob!.toString('base64'),
      iv: iv.toString('base64'),
      tag: tag.toString('base64'),
    };
  }
  
  async decrypt(
    ciphertext: string,
    encryptedKey: string,
    iv: string,
    tag: string,
    context: Record<string, string>
  ): Promise<string> {
    // Decrypt data key using KMS
    const { Plaintext } = await kms.decrypt({
      CiphertextBlob: Buffer.from(encryptedKey, 'base64'),
      EncryptionContext: context,
    });
    
    const decipher = crypto.createDecipheriv(
      this.algorithm,
      Plaintext!,
      Buffer.from(iv, 'base64')
    );
    decipher.setAuthTag(Buffer.from(tag, 'base64'));
    
    let plaintext = decipher.update(ciphertext, 'base64', 'utf8');
    plaintext += decipher.final('utf8');
    
    // Clear plaintext key from memory
    Plaintext!.fill(0);
    
    return plaintext;
  }
}

// Field-level encryption for PII
const piiFields = ['ssn', 'credit_card', 'date_of_birth'];

async function encryptPII(data: Record<string, unknown>): Promise<Record<string, unknown>> {
  const encryption = new DataEncryption();
  const result = { ...data };
  
  for (const field of piiFields) {
    if (result[field]) {
      result[field] = await encryption.encrypt(
        String(result[field]),
        { field, purpose: 'pii_protection' }
      );
    }
  }
  
  return result;
}
```

### Audit Logging

```typescript
// audit-log.ts
import { createHash } from 'crypto';

interface AuditEvent {
  timestamp: string;
  event_type: string;
  actor: {
    user_id: string;
    email: string;
    ip_address: string;
    user_agent: string;
  };
  action: string;
  resource: {
    type: string;
    id: string;
  };
  outcome: 'success' | 'failure';
  details: Record<string, unknown>;
  previous_state?: Record<string, unknown>;
  new_state?: Record<string, unknown>;
}

class AuditLogger {
  private async write(event: AuditEvent): Promise<void> {
    // Add integrity hash
    const eventWithHash = {
      ...event,
      integrity_hash: this.calculateHash(event),
      sequence_number: await this.getNextSequence(),
    };
    
    // Write to immutable audit log
    await this.writeToAuditStore(eventWithHash);
    
    // Send to SIEM for real-time monitoring
    await this.sendToSIEM(eventWithHash);
  }
  
  private calculateHash(event: AuditEvent): string {
    const content = JSON.stringify(event);
    return createHash('sha256').update(content).digest('hex');
  }
  
  // Pre-built audit event creators
  async logDataAccess(user: User, resource: string, action: string) {
    await this.write({
      timestamp: new Date().toISOString(),
      event_type: 'DATA_ACCESS',
      actor: {
        user_id: user.id,
        email: user.email,
        ip_address: user.ip,
        user_agent: user.userAgent,
      },
      action,
      resource: { type: 'data', id: resource },
      outcome: 'success',
      details: {},
    });
  }
  
  async logConfigChange(user: User, setting: string, oldValue: unknown, newValue: unknown) {
    await this.write({
      timestamp: new Date().toISOString(),
      event_type: 'CONFIG_CHANGE',
      actor: { user_id: user.id, email: user.email, ip_address: user.ip, user_agent: user.userAgent },
      action: 'UPDATE',
      resource: { type: 'config', id: setting },
      outcome: 'success',
      details: {},
      previous_state: { value: oldValue },
      new_state: { value: newValue },
    });
  }
  
  async logAuthEvent(user: User, eventType: string, success: boolean, details: Record<string, unknown>) {
    await this.write({
      timestamp: new Date().toISOString(),
      event_type: `AUTH_${eventType}`,
      actor: { user_id: user?.id || 'unknown', email: user?.email || 'unknown', ip_address: details.ip as string, user_agent: details.userAgent as string },
      action: eventType,
      resource: { type: 'authentication', id: user?.id || 'unknown' },
      outcome: success ? 'success' : 'failure',
      details,
    });
  }
}

export const auditLog = new AuditLogger();
```

---

## Phase 4: Evidence Collection

### Evidence Repository Structure

```
evidence/
├── policies/
│   ├── security-policy-v2.1.pdf
│   ├── acceptable-use-policy.pdf
│   ├── data-classification-policy.pdf
│   └── incident-response-policy.pdf
├── procedures/
│   ├── access-review-procedure.md
│   ├── change-management-procedure.md
│   └── backup-procedure.md
├── controls/
│   ├── CC6.1-access-control/
│   │   ├── mfa-configuration.png
│   │   ├── rbac-matrix.xlsx
│   │   └── access-review-2024-Q4.pdf
│   ├── CC7.1-incident-response/
│   │   ├── ir-plan.pdf
│   │   ├── incident-log-2024.xlsx
│   │   └── tabletop-exercise-notes.md
│   └── CC5.1-backups/
│       ├── backup-configuration.png
│       ├── restore-test-results.pdf
│       └── backup-schedule.md
├── training/
│   ├── security-awareness-completion.xlsx
│   └── training-materials/
└── vendor/
    ├── aws-soc2-report.pdf
    ├── stripe-pci-attestation.pdf
    └── vendor-risk-assessments/
```

### Automated Evidence Collection

```python
# evidence_collector.py
import boto3
from datetime import datetime, timedelta
import json

class EvidenceCollector:
    def __init__(self):
        self.s3 = boto3.client('s3')
        self.iam = boto3.client('iam')
        self.cloudtrail = boto3.client('cloudtrail')
        self.evidence_bucket = 'compliance-evidence'
        
    def collect_access_control_evidence(self) -> dict:
        """Collect evidence for access control requirements."""
        evidence = {
            'collection_date': datetime.now().isoformat(),
            'control_id': 'CC6.1',
            'items': []
        }
        
        # MFA status for all users
        users = self.iam.list_users()['Users']
        mfa_status = []
        for user in users:
            mfa_devices = self.iam.list_mfa_devices(UserName=user['UserName'])
            mfa_status.append({
                'user': user['UserName'],
                'mfa_enabled': len(mfa_devices['MFADevices']) > 0,
                'last_login': user.get('PasswordLastUsed', 'Never')
            })
        
        evidence['items'].append({
            'type': 'mfa_status',
            'data': mfa_status,
            'compliant': all(u['mfa_enabled'] for u in mfa_status)
        })
        
        # Password policy
        try:
            password_policy = self.iam.get_account_password_policy()['PasswordPolicy']
            evidence['items'].append({
                'type': 'password_policy',
                'data': password_policy,
                'compliant': (
                    password_policy.get('MinimumPasswordLength', 0) >= 12 and
                    password_policy.get('RequireUppercaseCharacters', False) and
                    password_policy.get('RequireLowercaseCharacters', False) and
                    password_policy.get('RequireNumbers', False) and
                    password_policy.get('RequireSymbols', False)
                )
            })
        except:
            evidence['items'].append({
                'type': 'password_policy',
                'data': None,
                'compliant': False,
                'note': 'No password policy configured'
            })
        
        # Save evidence
        self._save_evidence(evidence)
        return evidence
    
    def collect_logging_evidence(self) -> dict:
        """Collect evidence for logging requirements."""
        evidence = {
            'collection_date': datetime.now().isoformat(),
            'control_id': 'CC4.1',
            'items': []
        }
        
        # CloudTrail status
        trails = self.cloudtrail.describe_trails()['trailList']
        for trail in trails:
            status = self.cloudtrail.get_trail_status(Name=trail['Name'])
            evidence['items'].append({
                'type': 'cloudtrail',
                'name': trail['Name'],
                'logging': status['IsLogging'],
                'multi_region': trail.get('IsMultiRegionTrail', False),
                'log_validation': trail.get('LogFileValidationEnabled', False)
            })
        
        self._save_evidence(evidence)
        return evidence
    
    def collect_encryption_evidence(self) -> dict:
        """Collect evidence for encryption requirements."""
        evidence = {
            'collection_date': datetime.now().isoformat(),
            'control_id': 'CC6.7',
            'items': []
        }
        
        # S3 bucket encryption
        s3_buckets = self.s3.list_buckets()['Buckets']
        for bucket in s3_buckets:
            try:
                encryption = self.s3.get_bucket_encryption(Bucket=bucket['Name'])
                evidence['items'].append({
                    'type': 's3_encryption',
                    'bucket': bucket['Name'],
                    'encrypted': True,
                    'algorithm': encryption['ServerSideEncryptionConfiguration']['Rules'][0]['ApplyServerSideEncryptionByDefault']['SSEAlgorithm']
                })
            except:
                evidence['items'].append({
                    'type': 's3_encryption',
                    'bucket': bucket['Name'],
                    'encrypted': False
                })
        
        self._save_evidence(evidence)
        return evidence
    
    def _save_evidence(self, evidence: dict):
        """Save evidence to S3 with integrity protection."""
        key = f"{evidence['control_id']}/{evidence['collection_date']}.json"
        
        self.s3.put_object(
            Bucket=self.evidence_bucket,
            Key=key,
            Body=json.dumps(evidence, indent=2),
            ServerSideEncryption='aws:kms',
            Metadata={
                'collection-date': evidence['collection_date'],
                'control-id': evidence['control_id']
            }
        )
        
    def generate_compliance_report(self) -> dict:
        """Generate comprehensive compliance report."""
        report = {
            'generated': datetime.now().isoformat(),
            'framework': 'SOC2',
            'controls': {}
        }
        
        # Collect all evidence
        report['controls']['CC6.1'] = self.collect_access_control_evidence()
        report['controls']['CC4.1'] = self.collect_logging_evidence()
        report['controls']['CC6.7'] = self.collect_encryption_evidence()
        
        # Calculate compliance score
        total_items = 0
        compliant_items = 0
        for control in report['controls'].values():
            for item in control['items']:
                total_items += 1
                if item.get('compliant'):
                    compliant_items += 1
        
        report['compliance_score'] = round(compliant_items / total_items * 100, 1)
        
        return report

# Run evidence collection
collector = EvidenceCollector()
report = collector.generate_compliance_report()
print(f"Compliance Score: {report['compliance_score']}%")
```

---

## Phase 5: Audit Preparation

### Audit Readiness Checklist

```markdown
## Audit Readiness Checklist

### 4 Weeks Before
- [ ] Confirm audit scope and timeline
- [ ] Identify key personnel for interviews
- [ ] Review and update all policies
- [ ] Run evidence collection automation
- [ ] Identify and remediate gaps

### 2 Weeks Before
- [ ] Organize evidence repository
- [ ] Prepare control narratives
- [ ] Brief interview participants
- [ ] Test all technical demonstrations
- [ ] Prepare executive summary

### 1 Week Before
- [ ] Final evidence review
- [ ] Ensure all approvals documented
- [ ] Prepare war room / audit space
- [ ] Confirm auditor logistics
- [ ] Backup all evidence

### During Audit
- [ ] Daily status meetings
- [ ] Track auditor requests
- [ ] Provide evidence within 24 hours
- [ ] Document all discussions
- [ ] Escalate issues immediately

### Post-Audit
- [ ] Review draft findings
- [ ] Prepare management responses
- [ ] Create remediation plan
- [ ] Track remediation progress
- [ ] Update policies/procedures
```

### Control Narrative Template

```markdown
## Control Narrative: [Control ID]

### Control Objective
[What this control is designed to achieve]

### Control Description
[How the control operates]

### Control Owner
[Name and title]

### Control Frequency
[How often the control operates]

### Control Evidence
| Evidence Type | Location | Frequency |
|---------------|----------|-----------|
| [Type] | [Path/System] | [Frequency] |

### Control Testing
| Test | Method | Result |
|------|--------|--------|
| [Test name] | [Inquiry/Observation/Inspection] | [Pass/Fail] |

### Exceptions
| Date | Description | Resolution |
|------|-------------|------------|
| [Date] | [What happened] | [How resolved] |

### Related Controls
- [Control ID]: [Brief description]

### Last Review
Date: [Date]
Reviewer: [Name]
Result: [Effective/Needs Improvement]
```

---

## Phase 6: Continuous Compliance

### Compliance Dashboard

```markdown
## Compliance Dashboard

### Overall Status: 🟢 Compliant (94%)

### By Framework
| Framework | Score | Status | Next Audit |
|-----------|-------|--------|------------|
| SOC 2 | 96% | 🟢 | 2025-03-15 |
| GDPR | 92% | 🟢 | Continuous |
| PCI-DSS | 98% | 🟢 | 2025-06-01 |

### Control Health
| Category | Compliant | Partial | Gap |
|----------|-----------|---------|-----|
| Access Control | 12 | 1 | 0 |
| Data Protection | 8 | 2 | 0 |
| Monitoring | 6 | 1 | 1 |
| Change Mgmt | 5 | 0 | 0 |

### Recent Activity
| Date | Event | Impact |
|------|-------|--------|
| 2024-12-15 | Access review completed | CC6.1 ✅ |
| 2024-12-10 | New employee training | CC1.4 ✅ |
| 2024-12-05 | Vulnerability scan | CC7.1 ⚠️ |

### Upcoming Tasks
| Due | Task | Owner |
|-----|------|-------|
| Dec 20 | Quarterly access review | Security |
| Dec 31 | Annual policy review | Compliance |
| Jan 15 | Penetration test | Security |
```

### Automated Compliance Monitoring

```yaml
# compliance-monitoring.yaml
monitors:
  access_reviews:
    schedule: "0 9 1 */3 *"  # Quarterly
    check: |
      SELECT COUNT(*) FROM users 
      WHERE last_access_review < NOW() - INTERVAL '90 days'
    alert_if: "> 0"
    owner: security-team
    
  mfa_compliance:
    schedule: "0 8 * * *"  # Daily
    check: "aws iam list-users | check_mfa_enabled"
    alert_if: "any_disabled"
    owner: security-team
    
  encryption_status:
    schedule: "0 6 * * 1"  # Weekly
    check: "aws s3 list-buckets | check_encryption"
    alert_if: "any_unencrypted"
    owner: platform-team
    
  training_compliance:
    schedule: "0 9 1 * *"  # Monthly
    check: |
      SELECT COUNT(*) FROM employees
      WHERE security_training_date < NOW() - INTERVAL '1 year'
    alert_if: "> 0"
    owner: hr-team
    
  vendor_reviews:
    schedule: "0 9 1 * *"  # Monthly
    check: |
      SELECT * FROM vendors
      WHERE last_review < NOW() - INTERVAL '1 year'
    alert_if: "count > 0"
    owner: procurement
```

---

## Black Box Integration

```bash
# Start compliance session
./blackbox.sh start "compliance-soc2-gap-analysis"

# Log assessment
./blackbox.sh action "Completed gap analysis" "12 gaps identified"
./blackbox.sh decision "Prioritize MFA implementation" "Critical control gap"

# Log remediation
./blackbox.sh action "Implemented MFA for all users" "CC6.1 compliant"
./blackbox.sh action "Created incident response plan" "CC7.1 compliant"
./blackbox.sh milestone "All critical gaps remediated"

# Log evidence
./blackbox.sh action "Collected Q4 evidence" "45 artifacts"
./blackbox.sh checkpoint "Pre-audit evidence freeze"

# End session
./blackbox.sh end "Compliance score: 96%, ready for audit"
```

---

## Quick Reference

| Task | Action |
|------|--------|
| Run gap analysis | `python compliance_scanner.py --framework soc2` |
| Collect evidence | `python evidence_collector.py --all` |
| Generate report | `python compliance_scanner.py --report` |
| Check control status | Review compliance dashboard |
| Prepare for audit | Follow readiness checklist |

---

*Compliance & Auditing Workflow v1.0*
*Integrates with Black Box for tracking*
