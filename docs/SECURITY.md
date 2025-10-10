# Security Best Practices and Guidelines

## Overview

This document outlines security best practices, threat models, and mitigation strategies for Build-Fixer. Following these guidelines ensures secure deployment and operation in enterprise environments.

## Table of Contents

1. [Threat Model](#threat-model)
2. [Security Controls](#security-controls)
3. [Authentication & Authorization](#authentication--authorization)
4. [Data Protection](#data-protection)
5. [Secret Management](#secret-management)
6. [Network Security](#network-security)
7. [Compliance](#compliance)
8. [Incident Response](#incident-response)
9. [Security Checklist](#security-checklist)

---

## Threat Model

### STRIDE Analysis

#### Spoofing Identity
**Threat**: Attacker impersonates Build-Fixer to access Azure DevOps or AWS resources
**Impact**: Unauthorized work item creation, data access
**Mitigation**:
- Use service principals with unique identities
- Implement certificate-based authentication
- Enable MFA for admin access
- Audit all authentication attempts

#### Tampering with Data
**Threat**: Attacker modifies build logs or analysis results
**Impact**: Incorrect RCA, misleading recommendations
**Mitigation**:
- Enable S3 versioning and object lock
- Use checksums for log integrity verification
- Implement audit trails for all modifications
- Sign analysis results with digital signatures

#### Repudiation
**Threat**: Actions cannot be traced back to responsible party
**Impact**: Cannot prove who performed actions
**Mitigation**:
- Enable CloudTrail (AWS) and Activity Logs (Azure)
- Implement structured logging with user context
- Retain logs for compliance period (7 years)
- Non-repudiation through digital signatures

#### Information Disclosure
**Threat**: Sensitive data leaked through logs or errors
**Impact**: Exposed credentials, source code, customer data
**Mitigation**:
- Redact sensitive patterns (API keys, passwords, emails)
- Encrypt data at rest and in transit
- Implement least privilege access
- Use private endpoints for cloud services

#### Denial of Service
**Threat**: Service overwhelmed with requests or resource exhaustion
**Impact**: Build-Fixer unavailable, pipeline failures
**Mitigation**:
- Implement rate limiting (API throttling)
- Set resource quotas (CPU, memory)
- Use auto-scaling for high load
- Implement circuit breakers for external services

#### Elevation of Privilege
**Threat**: User/service gains unauthorized permissions
**Impact**: Access to restricted resources, data exfiltration
**Mitigation**:
- Follow least privilege principle
- Regular permission audits
- Separate roles (read-only, write, admin)
- Use managed identities where possible

---

## Security Controls

### Defense in Depth Layers

```
┌─────────────────────────────────────────────────┐
│ Layer 7: Physical & Personnel Security         │
│ - Background checks, access badges             │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│ Layer 6: Perimeter Security                     │
│ - Firewalls, DDoS protection, WAF              │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│ Layer 5: Network Security                       │
│ - VPC/VNet isolation, Security Groups, NSGs    │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│ Layer 4: Host Security                          │
│ - OS hardening, Anti-malware, Patch mgmt       │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│ Layer 3: Application Security                   │
│ - Input validation, Output encoding, SAST/DAST │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│ Layer 2: Data Security                          │
│ - Encryption (rest/transit), Tokenization, DLP │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│ Layer 1: Identity & Access                      │
│ - MFA, RBAC, Least privilege, PAM              │
└─────────────────────────────────────────────────┘
```

### Critical Controls (CIS Top 20)

| Control | Implementation | Status |
|---------|---------------|--------|
| 1. Inventory of Assets | Document all cloud resources | ✅ |
| 2. Software Inventory | Track dependencies (npm audit) | ✅ |
| 3. Data Protection | Encryption, classification | ✅ |
| 4. Secure Configuration | Hardened settings, no defaults | ✅ |
| 5. Account Management | Principle of least privilege | ✅ |
| 6. Access Control | RBAC, IAM policies | ✅ |
| 7. Continuous Monitoring | CloudWatch, alerts | ⚠️ Partial |
| 8. Audit Logs | CloudTrail, Azure Logs | ✅ |
| 9. Email & Browser Protection | N/A (backend service) | N/A |
| 10. Malware Defense | Dependency scanning | ✅ |

---

## Authentication & Authorization

### Identity Management

#### AWS IAM Policy (Least Privilege)
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockInvokeModel",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": [
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-sonnet*"
      ],
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": ["us-east-1", "us-west-2"]
        }
      }
    },
    {
      "Sid": "S3LogAccess",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": [
        "arn:aws:s3:::build-fixer-logs-${AWS::AccountId}/*"
      ],
      "Condition": {
        "StringLike": {
          "s3:x-amz-server-side-encryption": "AES256"
        }
      }
    }
  ]
}
```

#### Azure DevOps PAT Scopes (Minimal)
```
Required Scopes:
✅ Work Items (Read & Write)
❌ Code (Read) - Not needed
❌ Build (Read) - Optional, for metadata
❌ Release (Read) - Not needed

Token Settings:
- Expiration: 90 days maximum
- Organization: Single organization only
- Auto-renewal: Disabled (require manual review)
```

### Service Principal Best Practices

```bash
# AWS: Use IAM roles for EC2/ECS/Lambda
{
  "AssumeRolePolicyDocument": {
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }]
  }
}

# Azure: Use Managed Identity
resource "azurerm_user_assigned_identity" "build_fixer" {
  name                = "build-fixer-identity"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
}
```

---

## Data Protection

### Data Classification

| Classification | Examples | Protection Level |
|---------------|----------|------------------|
| **Public** | Documentation, open-source code | None |
| **Internal** | Build metadata, anonymized logs | Encryption in transit |
| **Confidential** | Build logs with code snippets | Encryption at rest & transit, Access logs |
| **Restricted** | Customer PII, credentials | Not allowed, Auto-redaction |

### Encryption Standards

#### At Rest
```javascript
// S3 Server-Side Encryption
const s3Client = new S3Client({
  region: 'us-east-1'
});

await s3Client.send(new PutObjectCommand({
  Bucket: 'build-logs',
  Key: key,
  Body: logContent,
  ServerSideEncryption: 'AES256', // or 'aws:kms' for CMK
  // For compliance: use customer-managed keys
  SSEKMSKeyId: 'arn:aws:kms:us-east-1:123456789012:key/...'
}));
```

#### In Transit
```javascript
// Enforce TLS 1.2+
const https = require('https');

const agent = new https.Agent({
  minVersion: 'TLSv1.2',
  maxVersion: 'TLSv1.3',
  rejectUnauthorized: true
});

// Apply to all AWS SDK calls
AWS.config.update({
  httpOptions: {
    agent: agent
  }
});
```

### Data Sanitization

#### Sensitive Pattern Redaction
```javascript
// Implement automatic redaction
class LogSanitizer {
  static SENSITIVE_PATTERNS = [
    // API Keys
    /[a-zA-Z0-9_\-]{32,}/g,
    // AWS Access Keys
    /AKIA[0-9A-Z]{16}/g,
    // Private Keys
    /-----BEGIN (RSA |DSA )?PRIVATE KEY-----/g,
    // Email addresses (optional)
    /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g,
    // Credit cards
    /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g,
    // Social Security Numbers
    /\b\d{3}-\d{2}-\d{4}\b/g
  ];

  static sanitize(logContent) {
    let sanitized = logContent;
    
    for (const pattern of this.SENSITIVE_PATTERNS) {
      sanitized = sanitized.replace(pattern, '[REDACTED]');
    }
    
    return sanitized;
  }
}

// Usage
const sanitizedLog = LogSanitizer.sanitize(buildLog);
```

### Data Retention

```yaml
Retention Policy:
  Build Logs (S3):
    Active: 90 days (Standard storage)
    Archive: 7 years (Glacier Deep Archive)
    Deletion: Automatic after 7 years
    
  Work Items (Azure DevOps):
    Active: Indefinite (business decision)
    Backup: Weekly snapshots for 1 year
    
  Audit Logs:
    CloudTrail: 7 years (compliance requirement)
    Application Logs: 90 days (operational)
    
  Analytics Data:
    Aggregated metrics: 2 years
    Individual records: Same as source data
```

---

## Secret Management

### Development Environment

```bash
# Never commit secrets
# Use .env (gitignored)
echo ".env" >> .gitignore

# .env.example (template without secrets)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AZURE_DEVOPS_TOKEN=
```

### CI/CD Environment

#### Azure Pipelines
```yaml
# Use Variable Groups with secret variables
variables:
  - group: build-fixer-secrets

steps:
  - script: |
      node src/index.js --log-file build.log
    env:
      # Reference secrets (masked in logs)
      AWS_SECRET_ACCESS_KEY: $(AWS_SECRET_ACCESS_KEY)
      AZURE_DEVOPS_TOKEN: $(AZURE_DEVOPS_TOKEN)
    displayName: 'Run Build-Fixer'
```

### Production Environment

#### AWS Secrets Manager
```javascript
const { SecretsManagerClient, GetSecretValueCommand } = require('@aws-sdk/client-secrets-manager');

class SecretManager {
  static async getSecret(secretName) {
    const client = new SecretsManagerClient({ region: 'us-east-1' });
    
    const response = await client.send(
      new GetSecretValueCommand({ SecretId: secretName })
    );
    
    return JSON.parse(response.SecretString);
  }
}

// Usage
const config = await SecretManager.getSecret('build-fixer/prod/config');
```

#### Azure Key Vault
```javascript
const { DefaultAzureCredential } = require('@azure/identity');
const { SecretClient } = require('@azure/keyvault-secrets');

class AzureSecretManager {
  constructor(vaultUrl) {
    const credential = new DefaultAzureCredential();
    this.client = new SecretClient(vaultUrl, credential);
  }
  
  async getSecret(secretName) {
    const secret = await this.client.getSecret(secretName);
    return secret.value;
  }
}
```

### Secret Rotation

```yaml
Rotation Schedule:
  Azure DevOps PAT:
    Frequency: Every 90 days
    Process: Manual renewal, update in Key Vault
    Notification: 14 days before expiry
    
  AWS Access Keys:
    Frequency: Every 180 days (if using keys)
    Process: Create new, test, deactivate old, delete old
    Recommendation: Use IAM roles instead
    
  Encryption Keys:
    Frequency: Annually
    Process: AWS KMS automatic rotation
    Impact: Transparent to application
```

---

## Network Security

### Network Architecture

#### Option 1: Public Endpoints (Current)
```
Pipeline Agent (Public)
    │
    ├──▶ AWS Bedrock (Public API)
    ├──▶ AWS S3 (Public API)
    └──▶ Azure DevOps (Public API)

Security:
✅ TLS encryption
✅ API authentication
❌ Network-level isolation
```

#### Option 2: Private Endpoints (Recommended for Enterprise)
```
Pipeline Agent (VNet)
    │
    ├──▶ VPC Endpoint (Bedrock) ──▶ AWS Bedrock
    ├──▶ VPC Endpoint (S3) ──▶ AWS S3
    └──▶ Private Endpoint ──▶ Azure DevOps

Security:
✅ TLS encryption
✅ API authentication
✅ Network-level isolation
✅ No internet exposure
```

### Firewall Rules

#### AWS Security Group
```hcl
resource "aws_security_group" "build_fixer" {
  name        = "build-fixer-sg"
  description = "Build-Fixer security group"
  vpc_id      = aws_vpc.main.id

  # Outbound to AWS services (VPC endpoints)
  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # Restrict to VPC endpoints in production
  }

  # No inbound rules (workers initiate connections only)
}
```

#### Azure Network Security Group
```hcl
resource "azurerm_network_security_group" "build_fixer" {
  name                = "build-fixer-nsg"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  security_rule {
    name                       = "AllowHTTPSOutbound"
    priority                   = 100
    direction                  = "Outbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "*"
    destination_address_prefix = "AzureDevOps"
  }
}
```

---

## Compliance

### SOC 2 Type II

**Requirements**:
1. **Security**: Protect against unauthorized access
2. **Availability**: System available for operation and use
3. **Processing Integrity**: System processing complete, valid, accurate, timely
4. **Confidentiality**: Protect confidential information
5. **Privacy**: Collect, use, retain, disclose personal information appropriately

**Implementation Checklist**:
- [x] Encryption at rest and in transit
- [x] Access controls and authentication
- [x] Audit logging and monitoring
- [x] Incident response procedures
- [ ] Annual penetration testing
- [ ] Vendor risk assessments
- [ ] Security awareness training

### GDPR Compliance

```yaml
Data Subject Rights:
  Right to Access:
    - Provide all data we have about them
    - Export work items and logs
    
  Right to Rectification:
    - Allow correction of inaccurate data
    - Update work items
    
  Right to Erasure:
    - Delete logs from S3
    - Remove work items (if allowed by retention policy)
    
  Right to Data Portability:
    - Export in machine-readable format (JSON)
    
  Right to Object:
    - Opt-out of AI analysis
    - Manual process only

Implementation:
  Data Residency: Deploy in EU regions (eu-west-1, West Europe)
  Data Processing: Document in Data Processing Agreement (DPA)
  Consent: Obtain for AI analysis (implied in pipeline setup)
  Breach Notification: Within 72 hours
```

### HIPAA Compliance

**If handling PHI** (Protected Health Information):

```yaml
Requirements:
  Business Associate Agreement (BAA):
    - AWS Bedrock: Available (request from AWS)
    - AWS S3: Available
    - Azure DevOps: Available
    
  Technical Safeguards:
    - Encryption: AES-256 at rest, TLS 1.2+ in transit
    - Access Controls: Role-based, MFA for admin
    - Audit Logs: All access logged and retained
    - Integrity Controls: Checksums, version control
    
  Physical Safeguards:
    - AWS/Azure data centers (compliant)
    
  Administrative Safeguards:
    - Security policies and procedures
    - Workforce training
    - Incident response plan
    
  Breach Notification:
    - Notification within 60 days
    - Affected individuals and HHS
```

---

## Incident Response

### Incident Classification

| Severity | Description | Response Time | Example |
|----------|-------------|---------------|---------|
| **P0** | Service down, data breach | 15 minutes | AWS credentials leaked |
| **P1** | Major degradation, security risk | 1 hour | High error rate, unauthorized access attempt |
| **P2** | Minor issues, low security impact | 4 hours | Slow performance, deprecated API |
| **P3** | Informational | 1 business day | Feature request, documentation |

### Incident Response Playbook

#### Security Incident (Data Breach)

```markdown
1. DETECT (0-15 min)
   - Alert triggered (CloudWatch, GuardDuty)
   - On-call engineer paged
   - Incident commander assigned

2. CONTAIN (15-60 min)
   - Rotate compromised credentials immediately
   - Revoke API tokens
   - Block malicious IP addresses
   - Isolate affected systems

3. INVESTIGATE (1-4 hours)
   - Review audit logs (CloudTrail, Azure Activity Log)
   - Identify scope of breach (what data accessed?)
   - Preserve evidence (log exports, snapshots)
   - Document timeline

4. ERADICATE (4-24 hours)
   - Remove malicious access
   - Patch vulnerabilities
   - Update security rules
   - Deploy fixes

5. RECOVER (24-48 hours)
   - Restore from clean backups if needed
   - Verify system integrity
   - Monitor for re-infection
   - Gradual service restoration

6. POST-MORTEM (Within 1 week)
   - Root cause analysis
   - Lessons learned
   - Update runbooks
   - Implement preventive measures
   - Notification to affected parties (if required)
```

### Security Contacts

```yaml
Primary Contact:
  Role: Security Team
  Email: security@company.com
  Phone: +1-XXX-XXX-XXXX
  
Escalation:
  Level 1: On-call Engineer
  Level 2: Security Manager
  Level 3: CISO
  Level 4: CEO (for major breaches)
  
External:
  AWS Support: Premium support plan
  Azure Support: Professional Direct
  Law Enforcement: FBI Cyber Division (for serious crimes)
```

---

## Security Checklist

### Pre-Deployment

- [ ] All secrets stored in secret manager (no hardcoded credentials)
- [ ] IAM policies follow least privilege
- [ ] Encryption enabled for S3 buckets
- [ ] TLS 1.2+ enforced for all connections
- [ ] MFA enabled for all admin accounts
- [ ] Security group rules reviewed and minimized
- [ ] Dependency vulnerabilities scanned (`npm audit`)
- [ ] SAST scan completed (CodeQL, Snyk)
- [ ] Sensitive data redaction implemented
- [ ] Audit logging enabled (CloudTrail, Azure Logs)

### Post-Deployment

- [ ] Monitor security alerts (GuardDuty, Security Center)
- [ ] Review access logs weekly
- [ ] Rotate credentials on schedule
- [ ] Update dependencies monthly
- [ ] Penetration testing annually
- [ ] Security training for team members
- [ ] Incident response drills quarterly
- [ ] Compliance audits (SOC 2, ISO 27001)

### Ongoing

- [ ] Security patches applied within SLA
- [ ] Vulnerability scanning automated
- [ ] Access reviews quarterly
- [ ] Architecture security reviews for major changes
- [ ] Threat model updates annually
- [ ] DR testing semi-annually

---

## Security Tools

### Recommended Tools

| Purpose | Tool | Description |
|---------|------|-------------|
| **SAST** | Snyk Code, SonarQube | Static analysis of source code |
| **Dependency Scanning** | Snyk, Dependabot | Detect vulnerable dependencies |
| **Secret Scanning** | git-secrets, TruffleHog | Find accidentally committed secrets |
| **DAST** | OWASP ZAP | Dynamic application security testing |
| **Threat Detection** | AWS GuardDuty, Azure Sentinel | Anomaly detection, threat intelligence |
| **Log Analysis** | Splunk, ELK Stack | Security event correlation |
| **Vulnerability Mgmt** | Qualys, Nessus | Infrastructure vulnerability scanning |

### CI/CD Security Integration

```yaml
# azure-pipelines-security.yml
trigger:
  - main

stages:
  - stage: SecurityScans
    jobs:
      - job: DependencyCheck
        steps:
          - script: npm audit --production
            displayName: 'NPM Audit'
            
      - task: SnykSecurityScan@1
        inputs:
          serviceConnectionEndpoint: 'Snyk'
          testType: 'app'
          severityThreshold: 'high'
          
      - script: |
          git secrets --scan
        displayName: 'Scan for secrets'
        
  - stage: SAST
    jobs:
      - job: CodeQL
        steps:
          - task: CodeQL@0
            inputs:
              language: 'javascript'
```

---

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CIS Controls](https://www.cisecurity.org/controls/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [AWS Security Best Practices](https://aws.amazon.com/security/best-practices/)
- [Azure Security Baseline](https://docs.microsoft.com/en-us/security/benchmark/azure/)
- [GDPR Compliance Checklist](https://gdpr.eu/checklist/)
- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/)

---

**Last Updated**: 2024-01-15  
**Next Review**: 2024-07-15  
**Owner**: Security Team
