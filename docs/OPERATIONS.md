# Operations Runbook

## Overview

This runbook provides operational procedures, troubleshooting guides, and standard operating procedures (SOPs) for Build-Fixer.

## Table of Contents

1. [Daily Operations](#daily-operations)
2. [Monitoring](#monitoring)
3. [Troubleshooting](#troubleshooting)
4. [Maintenance](#maintenance)
5. [Escalation](#escalation)
6. [Emergency Procedures](#emergency-procedures)

---

## Daily Operations

### Health Checks

#### Automated Health Checks (Every 5 minutes)
```bash
#!/bin/bash
# health-check.sh

# Check AWS Bedrock availability
aws bedrock-runtime invoke-model \
  --model-id anthropic.claude-3-sonnet-20240229-v1:0 \
  --body '{"prompt":"test","max_tokens":10}' \
  --region us-east-1 \
  response.json > /dev/null 2>&1

if [ $? -eq 0 ]; then
  echo "✅ Bedrock: Healthy"
else
  echo "❌ Bedrock: Unhealthy"
  # Alert on-call
fi

# Check S3 accessibility
aws s3 ls s3://build-fixer-logs/ > /dev/null 2>&1

if [ $? -eq 0 ]; then
  echo "✅ S3: Healthy"
else
  echo "❌ S3: Unhealthy"
fi

# Check Azure DevOps API
curl -s -u :${AZURE_DEVOPS_TOKEN} \
  "${AZURE_DEVOPS_ORG_URL}/_apis/projects" > /dev/null

if [ $? -eq 0 ]; then
  echo "✅ Azure DevOps: Healthy"
else
  echo "❌ Azure DevOps: Unhealthy"
fi
```

### Daily Tasks

**Morning Checklist** (30 minutes):
- [ ] Review overnight alerts and incidents
- [ ] Check error rate dashboard (<1% target)
- [ ] Verify queue depth (<50 items)
- [ ] Review cost anomalies (>20% increase)
- [ ] Check security alerts (GuardDuty, Security Center)

**End of Day** (15 minutes):
- [ ] Review day's metrics (analyses completed, failures)
- [ ] Update incident log if any issues occurred
- [ ] Check for pending updates (dependencies, patches)
- [ ] Verify backups completed successfully

---

## Monitoring

### Key Metrics

#### Service Level Indicators (SLIs)

```yaml
Availability:
  Metric: Successful analyses / Total analyses
  Target: >99.9%
  Measurement: CloudWatch Metric
  Alert: <99% over 5-minute window

Latency:
  Metric: Time from log upload to work item creation
  Target: P95 <15 seconds
  Measurement: CloudWatch Logs Insights
  Alert: P95 >30 seconds

Error Rate:
  Metric: Failed analyses / Total analyses
  Target: <1%
  Measurement: CloudWatch Metric
  Alert: >5% over 15-minute window

Throughput:
  Metric: Analyses completed per minute
  Target: >100/min (peak capacity)
  Measurement: CloudWatch Metric
  Alert: <20/min during business hours
```

### Dashboards

#### Operations Dashboard (CloudWatch/Grafana)
```
┌─────────────────────────────────────────────┐
│ Build-Fixer Operations Dashboard           │
├─────────────────────────────────────────────┤
│                                             │
│  Analyses (Last 24h): 1,234                │
│  Success Rate: 99.2% ✅                     │
│  Average Latency: 8.5s ✅                  │
│                                             │
│  ┌─────────────────┬──────────────────┐   │
│  │ Throughput      │ Error Rate       │   │
│  │ [Graph]         │ [Graph]          │   │
│  └─────────────────┴──────────────────┘   │
│                                             │
│  ┌─────────────────┬──────────────────┐   │
│  │ Latency (P50,   │ Queue Depth      │   │
│  │  P95, P99)      │ [Graph]          │   │
│  │ [Graph]         │                  │   │
│  └─────────────────┴──────────────────┘   │
│                                             │
│  Active Alerts: 0 ✅                       │
└─────────────────────────────────────────────┘
```

#### Cost Dashboard
```
┌─────────────────────────────────────────────┐
│ Build-Fixer Cost Dashboard                 │
├─────────────────────────────────────────────┤
│                                             │
│  Monthly Spend: $487 / $500 budget ⚠️      │
│                                             │
│  ┌─────────────────────────────────────┐  │
│  │ Cost Breakdown:                     │  │
│  │ • Bedrock: $292 (60%)               │  │
│  │ • S3: $49 (10%)                     │  │
│  │ • Compute: $97 (20%)                │  │
│  │ • Network: $29 (6%)                 │  │
│  │ • Other: $20 (4%)                   │  │
│  └─────────────────────────────────────┘  │
│                                             │
│  Cost per Analysis: $0.0039                │
│  Trend: ↗️ +5% vs last month               │
└─────────────────────────────────────────────┘
```

### Alerts

#### Critical Alerts (P0)
```yaml
ServiceDown:
  Condition: Error rate >50% for 5 minutes
  Notification: PagerDuty + SMS + Slack
  Escalation: Immediate to on-call engineer
  
DataBreach:
  Condition: GuardDuty high severity finding
  Notification: PagerDuty + SMS + Email to security team
  Escalation: Immediate to security team
  
CredentialLeak:
  Condition: Secret exposed in logs
  Notification: PagerDuty + SMS
  Escalation: Immediate to on-call + security
```

#### Warning Alerts (P1)
```yaml
HighErrorRate:
  Condition: Error rate >5% for 15 minutes
  Notification: Slack + Email
  Escalation: On-call engineer within 1 hour
  
HighLatency:
  Condition: P95 latency >30s for 10 minutes
  Notification: Slack
  Escalation: Investigate within 2 hours
  
CostAnomaly:
  Condition: Daily cost >200% of 7-day average
  Notification: Email to team lead
  Escalation: Review within 4 hours
```

---

## Troubleshooting

### Common Issues

#### Issue 1: High Error Rate

**Symptoms**:
- Error rate >5%
- CloudWatch logs show repeated failures
- Work items not being created

**Diagnosis**:
```bash
# Check recent errors
aws logs tail /aws/build-fixer/errors --follow --since 1h

# Check Bedrock status
aws bedrock list-foundation-models --region us-east-1

# Check Azure DevOps connectivity
curl -I https://dev.azure.com
```

**Resolution**:
1. Check service status pages (AWS, Azure)
2. Review error patterns in CloudWatch Logs
3. Verify credentials haven't expired
4. Check rate limits (Bedrock: 1000 requests/min)
5. Restart workers if memory leak suspected

**Prevention**:
- Implement exponential backoff
- Add circuit breakers
- Set up rate limit monitoring

#### Issue 2: Slow Performance

**Symptoms**:
- P95 latency >30s
- Queue depth increasing
- User complaints about delays

**Diagnosis**:
```bash
# Check Bedrock latency
aws cloudwatch get-metric-statistics \
  --namespace AWS/Bedrock \
  --metric-name InvokeModelLatency \
  --dimensions Name=ModelId,Value=anthropic.claude-3-sonnet-20240229-v1:0 \
  --statistics Average,Maximum \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300

# Check worker resource utilization
kubectl top pods -n build-fixer
```

**Resolution**:
1. Scale out workers (increase replicas)
2. Check for large logs (truncate more aggressively)
3. Switch to faster model (Claude Haiku for simple errors)
4. Enable caching for common error patterns
5. Check network latency (cross-region issues)

**Prevention**:
- Implement auto-scaling
- Set up performance baselines
- Use CDN for static content

#### Issue 3: Work Items Not Created

**Symptoms**:
- Analysis completes successfully
- Work items missing in Azure DevOps
- Logs show 401/403 errors

**Diagnosis**:
```bash
# Test Azure DevOps API
curl -u :${AZURE_DEVOPS_TOKEN} \
  "${AZURE_DEVOPS_ORG_URL}/${PROJECT}/_apis/wit/workitems/$\$Bug?api-version=7.1-preview.3" \
  -H "Content-Type: application/json-patch+json"

# Check token expiration
node -e "
const token = '${AZURE_DEVOPS_TOKEN}';
const decoded = Buffer.from(token, 'base64').toString('utf-8');
console.log(decoded);
"
```

**Resolution**:
1. Verify PAT token is valid and not expired
2. Check token has correct permissions (Work Items: Read & Write)
3. Verify project name is correct (case-sensitive)
4. Check Azure DevOps service status
5. Regenerate PAT token if needed

**Prevention**:
- Set up token expiration monitoring
- Use shorter expiration periods with rotation
- Implement graceful degradation (log failure, retry later)

#### Issue 4: High Costs

**Symptoms**:
- Monthly bill significantly higher than expected
- Cost alerts triggered
- Bedrock usage spike

**Diagnosis**:
```bash
# Check Bedrock invocation count
aws cloudwatch get-metric-statistics \
  --namespace AWS/Bedrock \
  --metric-name InvocationCount \
  --dimensions Name=ModelId,Value=anthropic.claude-3-sonnet-20240229-v1:0 \
  --statistics Sum \
  --start-time $(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600

# Check S3 storage size
aws s3 ls s3://build-fixer-logs/ --recursive --summarize | grep "Total Size"

# Identify expensive logs
aws s3api list-objects-v2 \
  --bucket build-fixer-logs \
  --query 'reverse(sort_by(Contents, &Size))[:10].[Key,Size]' \
  --output table
```

**Resolution**:
1. Review log truncation settings (reduce if too large)
2. Switch to cheaper model for simple failures (Haiku)
3. Implement caching for duplicate errors
4. Set up S3 lifecycle policies (move to Glacier after 90 days)
5. Review and optimize Bedrock prompts (shorter = cheaper)

**Prevention**:
- Set up cost budgets with alerts
- Implement cost attribution by team
- Regular cost optimization reviews

---

## Maintenance

### Scheduled Maintenance

#### Weekly Tasks
```bash
# Every Monday at 2 AM UTC
# Review and rotate logs
aws logs delete-log-group /aws/build-fixer/old-logs

# Check for outdated dependencies
npm outdated

# Review security vulnerabilities
npm audit

# Check S3 bucket size and costs
aws s3 ls s3://build-fixer-logs/ --recursive --summarize
```

#### Monthly Tasks
```bash
# First Sunday of each month
# Update dependencies
npm update
npm audit fix

# Review IAM policies
aws iam get-policy-version \
  --policy-arn arn:aws:iam::123456789012:policy/BuildFixerPolicy \
  --version-id v1

# Cost optimization review
# - Review Bedrock usage patterns
# - Check for unused S3 objects
# - Review compute rightsizing

# Backup configuration
aws s3 cp .env s3://build-fixer-backups/config/$(date +%Y%m%d).env
```

#### Quarterly Tasks
```bash
# Every 3 months
# Disaster recovery test
./scripts/dr-test.sh

# Security audit
./scripts/security-audit.sh

# Performance benchmark
./scripts/performance-test.sh

# Access review
# - Review user access
# - Remove inactive users
# - Audit service principal permissions
```

### Patching

```yaml
Critical Security Patch:
  Timeline: Within 24 hours
  Process:
    1. Review patch notes and changelog
    2. Test in dev environment
    3. Deploy to staging
    4. Monitor for issues (1 hour)
    5. Deploy to production
    6. Verify and monitor
    
High Priority Patch:
  Timeline: Within 7 days
  Process: Same as critical but with longer testing
  
Regular Updates:
  Timeline: Monthly maintenance window
  Process: Batch multiple updates together
```

---

## Escalation

### Escalation Matrix

| Issue Severity | L1 Response | L2 Escalation | L3 Escalation | L4 Escalation |
|---------------|-------------|---------------|---------------|---------------|
| **P0 (Critical)** | On-call engineer (immediate) | Team lead (15 min) | Director (30 min) | VP Eng (1 hour) |
| **P1 (High)** | On-call engineer (1 hour) | Team lead (4 hours) | Director (8 hours) | - |
| **P2 (Medium)** | Dev team (4 hours) | Team lead (1 day) | - | - |
| **P3 (Low)** | Dev team (1 day) | - | - | - |

### On-Call Rotation

```
Week 1: Engineer A (Primary), Engineer B (Secondary)
Week 2: Engineer B (Primary), Engineer C (Secondary)
Week 3: Engineer C (Primary), Engineer A (Secondary)
```

**On-Call Responsibilities**:
- Respond to pages within 15 minutes
- Acknowledge incidents in PagerDuty
- Triage and resolve or escalate
- Document actions in incident log
- Handoff unresolved issues to next shift

---

## Emergency Procedures

### Total Service Outage

```markdown
1. IMMEDIATE (0-5 min)
   - Acknowledge incident in PagerDuty
   - Post status update (StatusPage)
   - Notify stakeholders (Slack #incidents)

2. ASSESS (5-15 min)
   - Check AWS Service Health Dashboard
   - Check Azure Service Health
   - Review recent deployments
   - Check CloudWatch metrics

3. MITIGATE (15-60 min)
   Option A: Service Degradation
   - Disable non-critical features
   - Reduce traffic to affected components
   
   Option B: Total Failure
   - Failover to DR region
   - Use service health checks
   - Route traffic to healthy region

4. RESTORE (1-4 hours)
   - Fix root cause
   - Gradually restore service
   - Monitor for stability
   - Full functionality restored

5. COMMUNICATE
   - Update stakeholders every 30 minutes
   - Post final resolution
   - Schedule post-mortem
```

### Data Breach

```markdown
1. CONTAIN (0-30 min)
   - Identify compromised systems
   - Rotate all credentials immediately
   - Revoke leaked tokens
   - Block attacker IP addresses
   - Isolate affected systems

2. INVESTIGATE (30 min - 4 hours)
   - Review CloudTrail logs
   - Identify data accessed
   - Determine breach scope
   - Preserve evidence
   - Contact security team

3. NOTIFY (Within 72 hours for GDPR)
   - Affected users
   - Regulatory bodies (if required)
   - Law enforcement (if criminal activity)
   - Insurance company

4. REMEDIATE
   - Patch vulnerabilities
   - Update security controls
   - Conduct security review
   - Implement preventive measures

5. POST-INCIDENT
   - Forensic analysis
   - Legal review
   - Update security policies
   - Team training
```

### Cost Runaway

```markdown
1. STOP THE BLEED (0-15 min)
   - Set spending limit (AWS Budgets)
   - Scale down workers to minimum
   - Disable non-essential processing
   - Review recent changes

2. IDENTIFY SOURCE (15-60 min)
   - Check Cost Explorer
   - Identify service with spike
   - Review CloudWatch metrics
   - Check for infinite loops or bugs

3. FIX ROOT CAUSE (1-4 hours)
   - Fix bug causing high usage
   - Optimize queries/requests
   - Implement rate limiting
   - Add cost controls

4. PREVENT RECURRENCE
   - Set up stricter budgets
   - Add cost anomaly detection
   - Implement circuit breakers
   - Review architecture
```

---

## Post-Incident Review

### Template

```markdown
# Post-Incident Review: [Incident Title]

**Date**: YYYY-MM-DD
**Duration**: X hours Y minutes
**Severity**: P0/P1/P2
**Incident Commander**: [Name]

## Summary
Brief description of what happened

## Impact
- Users affected: X
- Downtime: Y hours
- Data lost: None/Some/All
- Financial impact: $Z

## Timeline
- HH:MM - Event occurred
- HH:MM - Alert triggered
- HH:MM - Engineer responded
- HH:MM - Root cause identified
- HH:MM - Fix deployed
- HH:MM - Service restored
- HH:MM - Incident closed

## Root Cause
Technical explanation of what went wrong

## Resolution
What was done to fix the issue

## Action Items
- [ ] Fix X (Owner: [Name], Due: YYYY-MM-DD)
- [ ] Improve monitoring for Y (Owner: [Name], Due: YYYY-MM-DD)
- [ ] Update runbook (Owner: [Name], Due: YYYY-MM-DD)

## Lessons Learned
### What went well
- 

### What could be improved
- 

## Follow-up
Next review: YYYY-MM-DD
```

---

## References

- [AWS Service Health Dashboard](https://status.aws.amazon.com/)
- [Azure Service Health](https://status.azure.com/)
- [PagerDuty Runbooks](https://response.pagerduty.com/)
- [Google SRE Book](https://sre.google/sre-book/table-of-contents/)

**Last Updated**: 2024-01-15  
**Next Review**: 2024-04-15  
**Owner**: Operations Team
