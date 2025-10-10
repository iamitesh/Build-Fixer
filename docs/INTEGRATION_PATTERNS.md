# Integration Patterns and API Design

## Overview

This document outlines integration patterns, API design principles, and extensibility mechanisms for Build-Fixer. It serves as a guide for integrating Build-Fixer with other systems and extending its capabilities.

## Table of Contents

1. [Integration Architecture](#integration-architecture)
2. [API Design Principles](#api-design-principles)
3. [Extension Points](#extension-points)
4. [Webhook Patterns](#webhook-patterns)
5. [Event-Driven Architecture](#event-driven-architecture)
6. [Plugin System](#plugin-system)
7. [Third-Party Integrations](#third-party-integrations)

---

## Integration Architecture

### Current Integration Model

```
┌─────────────────────────────────────────────────┐
│          Azure DevOps Pipeline                   │
│  (Primary Integration Point)                     │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │   Build-Fixer CLI    │
          │   (Orchestrator)     │
          └──────────┬───────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
┌────────────┐ ┌──────────┐ ┌──────────────┐
│ AWS        │ │ AWS      │ │ Azure DevOps │
│ Bedrock    │ │ S3       │ │ Work Items   │
└────────────┘ └──────────┘ └──────────────┘
```

### Future Integration Models

#### 1. API Gateway Pattern (Recommended for Scale)

```
┌──────────────────────────────────────────┐
│      Multiple Consumers                   │
│  ┌────────┐ ┌────────┐ ┌──────────┐     │
│  │Pipeline│ │Webhook │ │  Manual  │     │
│  └────┬───┘ └────┬───┘ └────┬─────┘     │
└───────┼──────────┼──────────┼────────────┘
        │          │          │
        └──────────┴──────────┘
                   │
        ┌──────────▼──────────┐
        │   API Gateway       │
        │  - Authentication   │
        │  - Rate Limiting    │
        │  - Routing          │
        │  - Caching          │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │  Build-Fixer API    │
        │  (REST/GraphQL)     │
        └──────────┬──────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
        ▼          ▼          ▼
    [Workers] [Services] [Storage]
```

**Implementation**:
```javascript
// API Gateway (Express.js example)
const express = require('express');
const app = express();

// Middleware
app.use(express.json());
app.use(authenticate);
app.use(rateLimit({ max: 100, windowMs: 60000 }));

// Routes
app.post('/api/v1/analyze', async (req, res) => {
  const { logContent, buildId, buildUrl } = req.body;
  
  // Validate input
  if (!logContent || !buildId) {
    return res.status(400).json({ error: 'Missing required fields' });
  }
  
  // Queue for processing
  const jobId = await queueAnalysis({ logContent, buildId, buildUrl });
  
  // Return immediately with job ID
  res.status(202).json({
    jobId,
    status: 'queued',
    statusUrl: `/api/v1/status/${jobId}`
  });
});

app.get('/api/v1/status/:jobId', async (req, res) => {
  const status = await getJobStatus(req.params.jobId);
  res.json(status);
});
```

#### 2. Event Bus Pattern (For Complex Workflows)

```
┌─────────────────────────────────────────────┐
│            Event Producers                   │
│  ┌────────┐ ┌────────┐ ┌──────────┐        │
│  │Pipeline│ │Webhook │ │ Schedule │        │
│  └────┬───┘ └────┬───┘ └────┬─────┘        │
└───────┼──────────┼──────────┼───────────────┘
        │          │          │
        └──────────┴──────────┘
                   │
        ┌──────────▼──────────────┐
        │   Event Bus             │
        │  (Azure Service Bus /   │
        │   AWS EventBridge)      │
        └──────────┬──────────────┘
                   │
        ┌──────────┼──────────────┐
        │          │              │
        ▼          ▼              ▼
┌────────────┐ ┌──────────┐ ┌──────────┐
│Build-Fixer │ │Notifier  │ │Analytics │
│ Worker     │ │ Service  │ │ Service  │
└────────────┘ └──────────┘ └──────────┘
```

**Event Schema**:
```json
{
  "eventType": "build.failed",
  "version": "1.0",
  "timestamp": "2024-01-15T10:30:00Z",
  "source": "azure-devops",
  "data": {
    "buildId": "12345",
    "buildUrl": "https://dev.azure.com/...",
    "project": "MyProject",
    "repository": "my-repo",
    "branch": "main",
    "triggeredBy": "user@example.com",
    "logUrl": "https://...",
    "metadata": {
      "duration": 180,
      "stage": "test",
      "failureType": "unit-test"
    }
  }
}
```

---

## API Design Principles

### RESTful API Design

#### Resource-Based URLs
```
Good:
  POST   /api/v1/analyses
  GET    /api/v1/analyses/{id}
  GET    /api/v1/analyses?buildId=12345
  PATCH  /api/v1/analyses/{id}

Bad:
  POST   /api/v1/analyzeLog
  GET    /api/v1/getAnalysis?id=123
  POST   /api/v1/updateAnalysis
```

#### HTTP Methods
```
POST   /analyses          - Create new analysis
GET    /analyses/{id}     - Retrieve analysis
GET    /analyses          - List analyses
PATCH  /analyses/{id}     - Update analysis
DELETE /analyses/{id}     - Delete analysis (admin only)
```

#### Status Codes
```
200 OK                    - Success (GET, PATCH)
201 Created              - Resource created (POST)
202 Accepted             - Async processing started
204 No Content           - Success with no response body (DELETE)
400 Bad Request          - Invalid input
401 Unauthorized         - Authentication required
403 Forbidden            - Insufficient permissions
404 Not Found            - Resource doesn't exist
429 Too Many Requests    - Rate limit exceeded
500 Internal Server Error - Server-side error
503 Service Unavailable  - Temporary unavailable
```

### API Versioning

**URL Versioning** (Recommended):
```
/api/v1/analyses
/api/v2/analyses  # Breaking changes
```

**Header Versioning** (Alternative):
```http
GET /api/analyses
Accept: application/vnd.buildfixer.v1+json
```

### Authentication

#### API Key
```http
POST /api/v1/analyses
Authorization: Bearer sk_live_abc123xyz789
Content-Type: application/json
```

#### OAuth 2.0 (Future)
```http
POST /api/v1/analyses
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

### Request/Response Format

#### Create Analysis Request
```json
POST /api/v1/analyses
{
  "buildId": "12345",
  "buildUrl": "https://dev.azure.com/org/project/_build/results?buildId=12345",
  "logContent": "...",
  "metadata": {
    "project": "MyProject",
    "repository": "my-repo",
    "branch": "main",
    "triggeredBy": "user@example.com"
  },
  "options": {
    "uploadToS3": true,
    "createWorkItem": true,
    "aiModel": "claude-3-sonnet"
  }
}
```

#### Response
```json
{
  "id": "analysis-uuid-123",
  "status": "processing",
  "buildId": "12345",
  "createdAt": "2024-01-15T10:30:00Z",
  "estimatedCompletionTime": "2024-01-15T10:30:15Z",
  "links": {
    "self": "/api/v1/analyses/analysis-uuid-123",
    "status": "/api/v1/analyses/analysis-uuid-123/status",
    "logs": "/api/v1/analyses/analysis-uuid-123/logs"
  }
}
```

#### Get Analysis Result
```json
GET /api/v1/analyses/analysis-uuid-123
{
  "id": "analysis-uuid-123",
  "status": "completed",
  "buildId": "12345",
  "buildUrl": "https://...",
  "createdAt": "2024-01-15T10:30:00Z",
  "completedAt": "2024-01-15T10:30:12Z",
  "duration": 12.5,
  "analysis": {
    "rootCause": "Unit test failure in UserService.test.js...",
    "recommendations": [
      "Fix the null pointer exception in getUserById method",
      "Add null checks before accessing user.email",
      "Update test to handle null user case"
    ],
    "confidence": 0.92,
    "severity": "high"
  },
  "workItem": {
    "id": 98765,
    "url": "https://dev.azure.com/org/project/_workitems/edit/98765",
    "type": "User Story",
    "state": "New"
  },
  "storage": {
    "s3Key": "build-logs/12345-1705318200.log",
    "s3Url": "https://s3.amazonaws.com/build-fixer-logs/..."
  },
  "cost": {
    "bedrock": 0.0032,
    "s3": 0.0001,
    "total": 0.0033,
    "currency": "USD"
  }
}
```

---

## Extension Points

### Plugin System Architecture

```javascript
// Plugin interface
class BuildFixerPlugin {
  constructor(config) {
    this.config = config;
  }
  
  // Lifecycle hooks
  async onAnalysisStart(context) {}
  async onLogUpload(context, s3Key) {}
  async onAIAnalysis(context, analysis) {}
  async onWorkItemCreate(context, workItem) {}
  async onAnalysisComplete(context, result) {}
  async onError(context, error) {}
}

// Example: Slack Notification Plugin
class SlackNotificationPlugin extends BuildFixerPlugin {
  async onWorkItemCreate(context, workItem) {
    await this.sendSlackMessage({
      channel: this.config.channel,
      message: `🔧 Build failure analyzed: ${workItem.url}`,
      buildId: context.buildId,
      rootCause: context.analysis.rootCause
    });
  }
  
  async onError(context, error) {
    await this.sendSlackMessage({
      channel: this.config.errorChannel,
      message: `❌ Build-Fixer error: ${error.message}`,
      buildId: context.buildId
    });
  }
}

// Plugin registration
const buildFixer = new BuildFixer(config);
buildFixer.use(new SlackNotificationPlugin({ 
  channel: '#build-failures',
  errorChannel: '#build-fixer-errors'
}));
```

### Custom AI Providers

```javascript
// AI Provider Interface
class AIProvider {
  async analyzeLog(logContent) {
    throw new Error('Not implemented');
  }
}

// Custom OpenAI Provider
class OpenAIProvider extends AIProvider {
  constructor(apiKey) {
    super();
    this.client = new OpenAI({ apiKey });
  }
  
  async analyzeLog(logContent) {
    const response = await this.client.chat.completions.create({
      model: 'gpt-4',
      messages: [
        { role: 'system', content: 'You are a DevOps expert...' },
        { role: 'user', content: `Analyze this build log:\n\n${logContent}` }
      ]
    });
    
    return this.parseResponse(response.choices[0].message.content);
  }
  
  parseResponse(text) {
    // Extract RCA and recommendations
    return {
      rca: '...',
      recommendations: '...'
    };
  }
}

// Register custom provider
buildFixer.setAIProvider(new OpenAIProvider(process.env.OPENAI_API_KEY));
```

### Custom Notification Channels

```javascript
class NotificationChannel {
  async notify(event) {
    throw new Error('Not implemented');
  }
}

class TeamsNotificationChannel extends NotificationChannel {
  constructor(webhookUrl) {
    super();
    this.webhookUrl = webhookUrl;
  }
  
  async notify(event) {
    const message = {
      '@type': 'MessageCard',
      'summary': 'Build Failure Analysis',
      'sections': [{
        'activityTitle': `Build #${event.buildId} Failed`,
        'facts': [
          { 'name': 'Root Cause', 'value': event.analysis.rootCause },
          { 'name': 'Work Item', 'value': event.workItem.url }
        ]
      }]
    };
    
    await axios.post(this.webhookUrl, message);
  }
}

buildFixer.addNotificationChannel(
  new TeamsNotificationChannel(process.env.TEAMS_WEBHOOK_URL)
);
```

---

## Webhook Patterns

### Inbound Webhooks (Receive Events)

```javascript
// Webhook receiver
app.post('/webhooks/github', async (req, res) => {
  // Verify signature
  const signature = req.headers['x-hub-signature-256'];
  if (!verifyGitHubSignature(req.body, signature)) {
    return res.status(401).send('Invalid signature');
  }
  
  const event = req.headers['x-github-event'];
  
  if (event === 'workflow_run' && req.body.workflow_run.conclusion === 'failure') {
    // Queue analysis
    await queueAnalysis({
      buildId: req.body.workflow_run.id,
      buildUrl: req.body.workflow_run.html_url,
      logUrl: req.body.workflow_run.logs_url
    });
  }
  
  res.status(200).send('OK');
});
```

### Outbound Webhooks (Send Events)

```javascript
class WebhookPublisher {
  constructor(config) {
    this.subscribers = config.subscribers || [];
  }
  
  async publish(event) {
    const payload = {
      eventType: event.type,
      timestamp: new Date().toISOString(),
      data: event.data
    };
    
    const signature = this.sign(payload);
    
    const results = await Promise.allSettled(
      this.subscribers.map(subscriber =>
        axios.post(subscriber.url, payload, {
          headers: {
            'X-BuildFixer-Signature': signature,
            'X-BuildFixer-Event': event.type,
            'Content-Type': 'application/json'
          },
          timeout: 5000
        })
      )
    );
    
    return results;
  }
  
  sign(payload) {
    const hmac = crypto.createHmac('sha256', process.env.WEBHOOK_SECRET);
    hmac.update(JSON.stringify(payload));
    return hmac.digest('hex');
  }
}

// Usage
const publisher = new WebhookPublisher({
  subscribers: [
    { url: 'https://my-service.com/webhooks/build-fixer' },
    { url: 'https://analytics.example.com/events' }
  ]
});

await publisher.publish({
  type: 'analysis.completed',
  data: {
    buildId: '12345',
    analysis: { ... },
    workItem: { ... }
  }
});
```

---

## Event-Driven Architecture

### Event Types

```typescript
enum EventType {
  ANALYSIS_STARTED = 'analysis.started',
  LOG_UPLOADED = 'log.uploaded',
  AI_ANALYSIS_COMPLETED = 'ai.analysis.completed',
  WORK_ITEM_CREATED = 'workitem.created',
  ANALYSIS_COMPLETED = 'analysis.completed',
  ANALYSIS_FAILED = 'analysis.failed',
  NOTIFICATION_SENT = 'notification.sent'
}

interface Event {
  id: string;
  type: EventType;
  timestamp: string;
  source: string;
  data: Record<string, any>;
  metadata?: Record<string, any>;
}
```

### Event Publisher

```javascript
class EventPublisher {
  constructor(eventBus) {
    this.eventBus = eventBus; // AWS EventBridge, Azure Service Bus, etc.
  }
  
  async publish(event) {
    const enrichedEvent = {
      ...event,
      id: uuidv4(),
      timestamp: new Date().toISOString(),
      source: 'build-fixer',
      version: '1.0'
    };
    
    // Publish to event bus
    await this.eventBus.send(enrichedEvent);
    
    // Store in event log (for audit)
    await this.storeEvent(enrichedEvent);
    
    return enrichedEvent;
  }
}
```

### Event Subscriber

```javascript
class EventSubscriber {
  constructor(eventBus, handlers) {
    this.eventBus = eventBus;
    this.handlers = handlers;
  }
  
  async subscribe(eventTypes) {
    for (const eventType of eventTypes) {
      await this.eventBus.subscribe(eventType, async (event) => {
        const handler = this.handlers[eventType];
        if (handler) {
          await handler(event);
        }
      });
    }
  }
}

// Usage
const subscriber = new EventSubscriber(eventBus, {
  [EventType.ANALYSIS_COMPLETED]: async (event) => {
    console.log('Analysis completed:', event.data);
    await sendMetrics(event.data);
  },
  [EventType.ANALYSIS_FAILED]: async (event) => {
    console.error('Analysis failed:', event.data);
    await alertOncall(event.data);
  }
});

await subscriber.subscribe([
  EventType.ANALYSIS_COMPLETED,
  EventType.ANALYSIS_FAILED
]);
```

---

## Third-Party Integrations

### Jira Integration

```javascript
class JiraIntegration {
  constructor(config) {
    this.client = new JiraClient({
      host: config.host,
      username: config.username,
      password: config.apiToken
    });
  }
  
  async createIssue(analysis) {
    const issue = {
      fields: {
        project: { key: 'PROJ' },
        summary: `Build Failure - Build #${analysis.buildId}`,
        description: this.formatDescription(analysis),
        issuetype: { name: 'Bug' },
        priority: { name: this.mapSeverity(analysis.severity) },
        labels: ['build-failure', 'automated']
      }
    };
    
    const response = await this.client.addNewIssue(issue);
    return {
      id: response.id,
      key: response.key,
      url: `${this.config.host}/browse/${response.key}`
    };
  }
  
  formatDescription(analysis) {
    return `
h2. Build Information
* Build ID: ${analysis.buildId}
* Build URL: ${analysis.buildUrl}
* Timestamp: ${analysis.timestamp}

h2. Root Cause Analysis
${analysis.rca}

h2. Recommended Fixes
${analysis.recommendations.map((r, i) => `# ${r}`).join('\n')}

h2. Additional Information
* AI Model: ${analysis.aiModel}
* Confidence: ${analysis.confidence}
* Log Location: ${analysis.s3Key}
    `.trim();
  }
}
```

### Slack Integration

```javascript
class SlackIntegration {
  constructor(webhookUrl) {
    this.webhookUrl = webhookUrl;
  }
  
  async sendAnalysisNotification(analysis) {
    const message = {
      text: `🔧 Build #${analysis.buildId} Failure Analyzed`,
      blocks: [
        {
          type: 'header',
          text: {
            type: 'plain_text',
            text: `Build #${analysis.buildId} Failed`
          }
        },
        {
          type: 'section',
          fields: [
            {
              type: 'mrkdwn',
              text: `*Build URL:*\n<${analysis.buildUrl}|View Build>`
            },
            {
              type: 'mrkdwn',
              text: `*Work Item:*\n<${analysis.workItem.url}|View Story>`
            }
          ]
        },
        {
          type: 'section',
          text: {
            type: 'mrkdwn',
            text: `*Root Cause:*\n${analysis.rca}`
          }
        },
        {
          type: 'section',
          text: {
            type: 'mrkdwn',
            text: `*Recommendations:*\n${analysis.recommendations.map((r, i) => `${i + 1}. ${r}`).join('\n')}`
          }
        },
        {
          type: 'actions',
          elements: [
            {
              type: 'button',
              text: { type: 'plain_text', text: 'View Work Item' },
              url: analysis.workItem.url,
              style: 'primary'
            },
            {
              type: 'button',
              text: { type: 'plain_text', text: 'View Build Log' },
              url: analysis.buildUrl
            }
          ]
        }
      ]
    };
    
    await axios.post(this.webhookUrl, message);
  }
}
```

### PagerDuty Integration

```javascript
class PagerDutyIntegration {
  constructor(apiKey, serviceKey) {
    this.client = new PagerDuty({ apiKey });
    this.serviceKey = serviceKey;
  }
  
  async createIncident(analysis) {
    // Only create incident for critical failures
    if (analysis.severity !== 'critical') {
      return null;
    }
    
    const incident = {
      incident: {
        type: 'incident',
        title: `Critical Build Failure - Build #${analysis.buildId}`,
        service: {
          id: this.serviceKey,
          type: 'service_reference'
        },
        urgency: 'high',
        body: {
          type: 'incident_body',
          details: `
Build ID: ${analysis.buildId}
Root Cause: ${analysis.rca}
Work Item: ${analysis.workItem.url}
          `.trim()
        }
      }
    };
    
    const response = await this.client.post('/incidents', incident);
    return response.data.incident;
  }
}
```

---

## GraphQL API (Future)

### Schema Definition

```graphql
type Query {
  analysis(id: ID!): Analysis
  analyses(
    buildId: String
    status: AnalysisStatus
    limit: Int = 10
    offset: Int = 0
  ): [Analysis!]!
  
  buildFailures(
    startDate: DateTime!
    endDate: DateTime!
    project: String
  ): [BuildFailure!]!
}

type Mutation {
  createAnalysis(input: CreateAnalysisInput!): AnalysisResult!
  retryAnalysis(id: ID!): AnalysisResult!
  updateWorkItem(id: ID!, input: UpdateWorkItemInput!): WorkItem!
}

type Subscription {
  analysisUpdated(buildId: String!): AnalysisUpdate!
}

type Analysis {
  id: ID!
  buildId: String!
  buildUrl: String!
  status: AnalysisStatus!
  createdAt: DateTime!
  completedAt: DateTime
  analysis: AnalysisResult
  workItem: WorkItem
  cost: Cost
}

enum AnalysisStatus {
  QUEUED
  PROCESSING
  COMPLETED
  FAILED
}

type AnalysisResult {
  rootCause: String!
  recommendations: [String!]!
  confidence: Float!
  severity: Severity!
}

enum Severity {
  LOW
  MEDIUM
  HIGH
  CRITICAL
}
```

### Resolver Implementation

```javascript
const resolvers = {
  Query: {
    analysis: async (_, { id }) => {
      return await db.getAnalysis(id);
    },
    
    analyses: async (_, { buildId, status, limit, offset }) => {
      return await db.getAnalyses({ buildId, status, limit, offset });
    }
  },
  
  Mutation: {
    createAnalysis: async (_, { input }) => {
      const analysis = await buildFixer.processBuildFailure(input);
      return analysis;
    }
  },
  
  Subscription: {
    analysisUpdated: {
      subscribe: (_, { buildId }) => {
        return pubsub.asyncIterator([`ANALYSIS_${buildId}`]);
      }
    }
  }
};
```

---

## Best Practices

### Idempotency

```javascript
// Use idempotency keys to prevent duplicate processing
app.post('/api/v1/analyses', async (req, res) => {
  const idempotencyKey = req.headers['idempotency-key'];
  
  if (idempotencyKey) {
    const existing = await db.getByIdempotencyKey(idempotencyKey);
    if (existing) {
      return res.status(200).json(existing);
    }
  }
  
  const analysis = await createAnalysis(req.body);
  
  if (idempotencyKey) {
    await db.saveIdempotencyKey(idempotencyKey, analysis);
  }
  
  res.status(201).json(analysis);
});
```

### Rate Limiting

```javascript
const rateLimit = require('express-rate-limit');

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: 'Too many requests, please try again later',
  standardHeaders: true,
  legacyHeaders: false,
});

app.use('/api/', limiter);
```

### API Documentation

Use OpenAPI/Swagger for API documentation:

```yaml
openapi: 3.0.0
info:
  title: Build-Fixer API
  version: 1.0.0
  description: Automated build failure analysis API

paths:
  /api/v1/analyses:
    post:
      summary: Create a new build failure analysis
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateAnalysisRequest'
      responses:
        '202':
          description: Analysis queued successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AnalysisResponse'
```

---

## Summary

This integration guide provides:
- ✅ Multiple integration patterns (CLI, API, Events, Webhooks)
- ✅ Extensibility through plugins and custom providers
- ✅ Third-party integrations (Slack, Jira, PagerDuty)
- ✅ Best practices for API design and security
- ✅ Future-ready architecture (GraphQL, Event-Driven)

For implementation examples, see:
- [examples/integrations/](../examples/integrations/) - Integration code samples
- [API.md](./API.md) - Detailed API reference
- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture

**Last Updated**: 2024-01-15  
**Next Review**: 2024-07-15  
**Owner**: Architecture Team
