# Data Governance and Retention Policy

## Overview

This document defines data governance policies, retention schedules, and compliance requirements for Build-Fixer. It ensures responsible data management aligned with legal, regulatory, and business requirements.

## Table of Contents

1. [Data Classification](#data-classification)
2. [Data Lifecycle](#data-lifecycle)
3. [Retention Policies](#retention-policies)
4. [Data Privacy](#data-privacy)
5. [Access Controls](#access-controls)
6. [Audit and Compliance](#audit-and-compliance)
7. [Data Quality](#data-quality)

---

## Data Classification

### Classification Levels

| Level | Description | Examples | Handling Requirements |
|-------|-------------|----------|----------------------|
| **Public** | Information intended for public disclosure | Documentation, open-source code, public APIs | No restrictions |
| **Internal** | Information for internal use only | Build metadata, aggregated metrics, system logs | Access control, encryption in transit |
| **Confidential** | Sensitive business information | Build logs with code, error messages, configuration | Encryption at rest & transit, access logging, DLP |
| **Restricted** | Highly sensitive regulated data | Customer PII, credentials, payment data, PHI | Strongest encryption, strict access control, audit trail |

### Data Inventory

#### Build Logs
- **Classification**: Confidential
- **Location**: AWS S3, Azure Blob Storage
- **Contains**: Source code snippets, environment variables, error traces
- **Sensitivity**: HIGH - May contain secrets or proprietary code
- **Retention**: 90 days active, 7 years archived

#### Analysis Results
- **Classification**: Internal
- **Location**: Azure DevOps Work Items, Database
- **Contains**: RCA, recommendations, metadata
- **Sensitivity**: MEDIUM - Business insights
- **Retention**: Indefinite (business value)

#### Audit Logs
- **Classification**: Internal
- **Location**: AWS CloudTrail, Azure Activity Log
- **Contains**: API calls, user actions, system events
- **Sensitivity**: MEDIUM - Compliance requirement
- **Retention**: 7 years (regulatory compliance)

#### User Data
- **Classification**: Restricted (if contains PII)
- **Location**: Azure DevOps, Database
- **Contains**: Email, name, team affiliation
- **Sensitivity**: HIGH - GDPR/CCPA applies
- **Retention**: Active employment + 90 days

#### Cost Data
- **Classification**: Confidential
- **Location**: Database, Cost management tools
- **Contains**: AWS/Azure billing, per-team allocation
- **Sensitivity**: MEDIUM - Financial information
- **Retention**: 7 years (tax/audit requirements)

---

## Data Lifecycle

### Lifecycle Stages

```
┌─────────────────────────────────────────────────────┐
│                 Data Lifecycle                       │
└─────────────────────────────────────────────────────┘

1. COLLECTION
   ├─ Build logs retrieved from pipeline
   ├─ Metadata extracted
   ├─ Sensitive data redacted
   └─ Validation and quality checks

2. PROCESSING
   ├─ Upload to S3 (encrypted)
   ├─ AI analysis (Bedrock)
   ├─ Result generation
   └─ Work item creation

3. STORAGE
   ├─ S3 Standard (0-30 days)
   ├─ S3 Infrequent Access (30-90 days)
   ├─ S3 Glacier (90 days - 1 year)
   └─ S3 Glacier Deep Archive (1-7 years)

4. ACCESS
   ├─ Search and retrieval
   ├─ Analytics and reporting
   ├─ Audit and compliance
   └─ Legal discovery

5. ARCHIVAL
   ├─ Compliance-driven retention
   ├─ Compressed storage
   ├─ Indexed for retrieval
   └─ Documented chain of custody

6. DELETION
   ├─ End of retention period
   ├─ User right to erasure (GDPR)
   ├─ Secure deletion (overwrite)
   └─ Deletion certificate generated
```

### State Transitions

```javascript
const dataLifecycle = {
  'ACTIVE': {
    duration: 90 * 24 * 60 * 60 * 1000, // 90 days
    storage: 'S3_STANDARD',
    encryption: 'AES-256',
    indexing: true,
    nextState: 'ARCHIVED'
  },
  
  'ARCHIVED': {
    duration: 7 * 365 * 24 * 60 * 60 * 1000, // 7 years
    storage: 'S3_GLACIER_DEEP_ARCHIVE',
    encryption: 'AES-256',
    indexing: true,
    nextState: 'ELIGIBLE_FOR_DELETION'
  },
  
  'ELIGIBLE_FOR_DELETION': {
    duration: 30 * 24 * 60 * 60 * 1000, // 30 day grace period
    storage: 'S3_GLACIER_DEEP_ARCHIVE',
    encryption: 'AES-256',
    indexing: true,
    nextState: 'DELETED'
  },
  
  'DELETED': {
    duration: null,
    storage: null,
    encryption: null,
    indexing: false,
    nextState: null
  }
};
```

---

## Retention Policies

### Legal and Regulatory Requirements

| Requirement | Retention Period | Data Types | Jurisdictions |
|------------|------------------|------------|---------------|
| **SOX (Sarbanes-Oxley)** | 7 years | Audit logs, financial data | USA |
| **GDPR** | Minimal, with consent | Personal data | EU/EEA |
| **HIPAA** | 6 years | PHI, audit logs | USA |
| **CCPA** | Until deletion request | Personal data | California |
| **Tax Records** | 7 years | Cost data, invoices | Most countries |
| **Employment Records** | 7 years post-termination | User data | Various |

### Build-Fixer Specific Policies

#### Build Logs
```yaml
Policy: BL-001
Description: Build log retention and archival

Stages:
  - Active (S3 Standard):
      Duration: 90 days
      Reason: Frequent access for recent failures
      Cost: $0.023/GB/month
      
  - Archive (S3 Glacier):
      Duration: 1 year
      Reason: Occasional reference, trend analysis
      Cost: $0.004/GB/month
      
  - Deep Archive (S3 Glacier Deep Archive):
      Duration: 6 years (total 7 years)
      Reason: Compliance (SOX, audit requirements)
      Cost: $0.00099/GB/month
      
  - Deletion:
      Trigger: After 7 years or on user request
      Method: Secure deletion with certificate
      Exceptions: Active litigation or regulatory hold

Implementation:
  s3_lifecycle_policy:
    - id: transition-to-glacier
      status: Enabled
      transition:
        days: 90
        storage_class: GLACIER
        
    - id: transition-to-deep-archive
      status: Enabled
      transition:
        days: 365
        storage_class: DEEP_ARCHIVE
        
    - id: expire-old-logs
      status: Enabled
      expiration:
        days: 2555  # 7 years
```

#### Work Items (Azure DevOps)
```yaml
Policy: WI-001
Description: Work item retention

Retention: Indefinite
Reason: Business value, historical reference
Exceptions:
  - User requests deletion (GDPR Right to Erasure)
  - Project sunset (delete after 1 year inactive)
  
Backup:
  Frequency: Weekly
  Retention: 1 year
  Location: Azure Blob Storage (Geo-redundant)
  
Export:
  Format: JSON
  Frequency: Monthly
  Location: S3 (encrypted)
```

#### Audit Logs
```yaml
Policy: AL-001
Description: Audit log retention

Primary Storage:
  Duration: 90 days
  Location: CloudWatch Logs
  Access: Real-time query
  
Archive:
  Duration: 7 years
  Location: S3 Glacier Deep Archive
  Access: Retrieval within 12 hours
  Reason: Compliance (SOC 2, HIPAA)
  
Immutability:
  S3 Object Lock: Enabled (Compliance mode)
  Retention: 7 years
  Prevents: Deletion or modification
```

#### Analytics Data
```yaml
Policy: AD-001
Description: Aggregated analytics and metrics

Granular Data (Individual analyses):
  Duration: 2 years
  Storage: Database (encrypted)
  
Aggregated Metrics (hourly/daily/monthly):
  Duration: 5 years
  Storage: Time-series database
  
Summary Reports:
  Duration: Indefinite
  Storage: Document storage
  
Deletion:
  Trigger: End of retention + 30 day grace period
  Method: Soft delete → Hard delete
```

---

## Data Privacy

### GDPR Compliance

#### Data Subject Rights Implementation

##### 1. Right to Access (Art. 15)
```javascript
async function handleDataAccessRequest(userId) {
  // Compile all data for the user
  const userData = {
    profile: await db.getUserProfile(userId),
    analyses: await db.getUserAnalyses(userId),
    workItems: await azureDevOps.getUserWorkItems(userId),
    auditLogs: await cloudTrail.getUserActions(userId),
    exportedAt: new Date().toISOString()
  };
  
  // Export in machine-readable format (JSON)
  const exportFile = await generateExport(userData);
  
  // Provide secure download link (expires in 7 days)
  return {
    downloadUrl: await s3.getSignedUrl(exportFile, { expiresIn: 7 * 24 * 60 * 60 }),
    expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString()
  };
}
```

##### 2. Right to Rectification (Art. 16)
```javascript
async function handleRectificationRequest(userId, corrections) {
  // Validate corrections
  const validated = validateCorrections(corrections);
  
  // Apply corrections
  await db.updateUserProfile(userId, validated);
  
  // Audit trail
  await auditLog.record({
    action: 'DATA_RECTIFICATION',
    userId,
    changes: corrections,
    requestedBy: userId,
    timestamp: new Date().toISOString()
  });
  
  return { success: true, updated: validated };
}
```

##### 3. Right to Erasure (Art. 17)
```javascript
async function handleErasureRequest(userId) {
  // Cannot delete if under legal hold
  if (await isUnderLegalHold(userId)) {
    throw new Error('Cannot delete: legal hold active');
  }
  
  // Pseudonymize instead of delete (for audit integrity)
  await db.pseudonymizeUser(userId);
  
  // Delete personal data
  await Promise.all([
    db.deleteUserProfile(userId),
    azureDevOps.anonymizeWorkItems(userId),
    s3.deleteLogs({ userId }),
  ]);
  
  // Keep audit trail (anonymized)
  await auditLog.record({
    action: 'DATA_ERASURE',
    userId: 'DELETED_USER_' + crypto.randomUUID(),
    timestamp: new Date().toISOString(),
    reason: 'GDPR Right to Erasure'
  });
  
  return { success: true, deletedAt: new Date().toISOString() };
}
```

##### 4. Right to Data Portability (Art. 20)
```javascript
async function handlePortabilityRequest(userId) {
  const data = await compileUserData(userId);
  
  // Export in standard format (JSON)
  const portableData = {
    version: '1.0',
    user: {
      id: userId,
      profile: data.profile
    },
    analyses: data.analyses,
    exportDate: new Date().toISOString(),
    format: 'application/json'
  };
  
  return portableData;
}
```

##### 5. Right to Object (Art. 21)
```javascript
async function handleObjectionRequest(userId, processingType) {
  if (processingType === 'AI_ANALYSIS') {
    // Opt-out of AI analysis
    await db.updateUserPreferences(userId, { 
      aiAnalysis: false 
    });
    
    // Future analyses will skip AI processing
    return { 
      success: true, 
      message: 'Opted out of AI analysis. Future builds will use manual process only.' 
    };
  }
}
```

### Data Minimization

```javascript
class DataMinimization {
  // Collect only necessary data
  static sanitizeBuildLog(log) {
    // Remove unnecessary data
    let sanitized = log;
    
    // Remove sensitive patterns
    const patterns = {
      apiKeys: /[a-zA-Z0-9_\-]{32,}/g,
      awsKeys: /AKIA[0-9A-Z]{16}/g,
      emails: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g,
      ipAddresses: /\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/g,
      creditCards: /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g
    };
    
    for (const [type, pattern] of Object.entries(patterns)) {
      sanitized = sanitized.replace(pattern, `[REDACTED_${type.toUpperCase()}]`);
    }
    
    return sanitized;
  }
  
  // Pseudonymization for analytics
  static pseudonymize(data) {
    return {
      ...data,
      userId: crypto.createHash('sha256').update(data.userId).digest('hex'),
      email: null,
      name: null,
      // Keep non-identifying data for analytics
      timestamp: data.timestamp,
      buildId: data.buildId,
      errorType: data.errorType
    };
  }
}
```

### Consent Management

```yaml
Consent Types:
  Essential:
    - Purpose: Core functionality (analyze build failures)
    - Legal Basis: Legitimate interest
    - User Control: Cannot opt-out (required for service)
    
  Analytics:
    - Purpose: Improve service quality
    - Legal Basis: Consent
    - User Control: Can opt-out
    - Default: Opt-in
    
  AI Analysis:
    - Purpose: Automated root cause analysis
    - Legal Basis: Consent
    - User Control: Can opt-out (manual process fallback)
    - Default: Opt-in
    
  Notifications:
    - Purpose: Alerts and updates
    - Legal Basis: Consent
    - User Control: Can opt-out per channel
    - Default: Opt-in

Consent Record:
  user_id: UUID
  timestamp: ISO8601
  consents:
    analytics: true
    ai_analysis: true
    email_notifications: false
    slack_notifications: true
  ip_address: (hashed)
  user_agent: (hashed)
  version: 1.0
```

---

## Access Controls

### Role-Based Access Control (RBAC)

```yaml
Roles:
  admin:
    description: Full system access
    permissions:
      - analyses:*
      - data:*
      - config:*
      - users:*
    assignment: IT Administrators, Security Team
    
  developer:
    description: Create and view analyses
    permissions:
      - analyses:create
      - analyses:read
      - analyses:list
    assignment: Development team members
    
  viewer:
    description: Read-only access
    permissions:
      - analyses:read
      - analyses:list
    assignment: Managers, stakeholders
    
  data_officer:
    description: Data governance and compliance
    permissions:
      - data:export
      - data:delete
      - audit:read
    assignment: Legal, Compliance team
    
  auditor:
    description: Audit log access only
    permissions:
      - audit:read
      - audit:export
    assignment: Internal audit team
```

### Attribute-Based Access Control (ABAC)

```javascript
class AccessControl {
  async authorize(user, resource, action) {
    // User attributes
    const userAttrs = {
      role: user.role,
      department: user.department,
      clearanceLevel: user.clearanceLevel
    };
    
    // Resource attributes
    const resourceAttrs = {
      classification: resource.classification,
      owner: resource.owner,
      project: resource.project
    };
    
    // Environment attributes
    const envAttrs = {
      time: new Date(),
      ipAddress: user.ipAddress,
      mfaVerified: user.mfaVerified
    };
    
    // Policy evaluation
    return await this.evaluatePolicy(userAttrs, resourceAttrs, envAttrs, action);
  }
  
  async evaluatePolicy(user, resource, env, action) {
    // Example policy rules
    const rules = [
      {
        // Admins can do anything
        condition: user.role === 'admin',
        effect: 'allow'
      },
      {
        // Users can access their own team's resources
        condition: user.department === resource.project && action === 'read',
        effect: 'allow'
      },
      {
        // Confidential data requires MFA
        condition: resource.classification === 'confidential' && !env.mfaVerified,
        effect: 'deny'
      },
      {
        // No access outside business hours for non-admins
        condition: !this.isBusinessHours(env.time) && user.role !== 'admin',
        effect: 'deny'
      }
    ];
    
    for (const rule of rules) {
      if (rule.condition) {
        return rule.effect === 'allow';
      }
    }
    
    // Default deny
    return false;
  }
}
```

---

## Audit and Compliance

### Audit Trail Requirements

```javascript
const auditEventSchema = {
  id: 'UUID',
  timestamp: 'ISO8601',
  eventType: 'ENUM',
  actor: {
    userId: 'string',
    role: 'string',
    ipAddress: 'string (hashed)',
    userAgent: 'string (hashed)'
  },
  resource: {
    type: 'string',
    id: 'string',
    classification: 'ENUM'
  },
  action: 'string',
  result: 'success | failure',
  details: {
    // Action-specific details
  },
  metadata: {
    sessionId: 'string',
    requestId: 'string',
    apiVersion: 'string'
  }
};

// Example audit event
const auditEvent = {
  id: 'ae-12345678',
  timestamp: '2024-01-15T10:30:00Z',
  eventType: 'DATA_ACCESS',
  actor: {
    userId: 'user-123',
    role: 'developer',
    ipAddress: 'hash-of-ip',
    userAgent: 'hash-of-ua'
  },
  resource: {
    type: 'BUILD_LOG',
    id: 'log-98765',
    classification: 'CONFIDENTIAL'
  },
  action: 'READ',
  result: 'success',
  details: {
    buildId: '12345',
    project: 'MyProject',
    accessMethod: 'API'
  },
  metadata: {
    sessionId: 'sess-xyz',
    requestId: 'req-abc',
    apiVersion: 'v1'
  }
};
```

### Compliance Reporting

```javascript
class ComplianceReporter {
  async generateSOC2Report(startDate, endDate) {
    return {
      reportType: 'SOC 2 Type II',
      period: { start: startDate, end: endDate },
      controls: {
        CC6_1_AccessControls: await this.validateAccessControls(),
        CC6_2_LogicalAccess: await this.validateLogicalAccess(),
        CC6_3_NetworkSecurity: await this.validateNetworkSecurity(),
        CC7_2_Monitoring: await this.validateMonitoring(),
        CC8_1_ChangeManagement: await this.validateChangeManagement()
      },
      incidents: await this.getSecurityIncidents(startDate, endDate),
      exceptions: await this.getControlExceptions(startDate, endDate)
    };
  }
  
  async generateGDPRReport() {
    return {
      dataProcessingActivities: await this.getProcessingActivities(),
      dataSubjectRequests: await this.getDataSubjectRequests(),
      dataBreaches: await this.getDataBreaches(),
      dataRetention: await this.getRetentionCompliance(),
      thirdPartyProcessors: await this.getSubProcessors(),
      dpia: await this.getDataProtectionImpactAssessments()
    };
  }
}
```

---

## Data Quality

### Quality Dimensions

| Dimension | Definition | Measurement | Target |
|-----------|-----------|-------------|--------|
| **Accuracy** | Data correctly represents reality | % of correct analyses | >90% |
| **Completeness** | All required data present | % of complete records | >95% |
| **Consistency** | Data consistent across systems | % of matching records | >99% |
| **Timeliness** | Data available when needed | Time to availability | <5 min |
| **Validity** | Data conforms to schema | % of valid records | 100% |
| **Uniqueness** | No duplicate records | % of unique records | 100% |

### Data Quality Framework

```javascript
class DataQualityChecker {
  async validateBuildLog(log) {
    const issues = [];
    
    // Completeness
    if (!log.buildId || !log.timestamp || !log.content) {
      issues.push({ type: 'COMPLETENESS', field: 'required fields missing' });
    }
    
    // Validity
    if (log.content.length < 10) {
      issues.push({ type: 'VALIDITY', field: 'content too short' });
    }
    
    // Consistency
    if (log.buildId && !await this.buildExists(log.buildId)) {
      issues.push({ type: 'CONSISTENCY', field: 'buildId not found' });
    }
    
    // Accuracy (sampling)
    if (Math.random() < 0.01) { // 1% sample
      const verified = await this.verifyWithSource(log);
      if (!verified) {
        issues.push({ type: 'ACCURACY', field: 'content mismatch' });
      }
    }
    
    return {
      valid: issues.length === 0,
      issues,
      score: this.calculateQualityScore(issues)
    };
  }
  
  calculateQualityScore(issues) {
    const weights = {
      'COMPLETENESS': 0.3,
      'VALIDITY': 0.3,
      'CONSISTENCY': 0.2,
      'ACCURACY': 0.2
    };
    
    let score = 100;
    for (const issue of issues) {
      score -= (weights[issue.type] || 0.1) * 100;
    }
    
    return Math.max(0, score);
  }
}
```

---

## Summary

This data governance framework ensures:
- ✅ **Compliance**: GDPR, HIPAA, SOC 2, SOX
- ✅ **Security**: Classification, encryption, access control
- ✅ **Privacy**: Data minimization, pseudonymization, consent
- ✅ **Quality**: Validation, monitoring, reporting
- ✅ **Lifecycle**: Collection to deletion with audit trail

For related documentation, see:
- [SECURITY.md](./SECURITY.md) - Security controls
- [OPERATIONS.md](./OPERATIONS.md) - Operational procedures
- [ENTERPRISE_ARCHITECTURE.md](./ENTERPRISE_ARCHITECTURE.md) - Architecture patterns

**Last Updated**: 2024-01-15  
**Next Review**: 2024-04-15 (Quarterly)  
**Owner**: Data Governance Committee
