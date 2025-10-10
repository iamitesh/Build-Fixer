# Architecture Documentation

## Overview

Build-Fixer follows a modular, service-oriented architecture designed for maintainability, testability, and extensibility.

## Design Principles

1. **Separation of Concerns**: Each service handles a specific domain (S3, Bedrock, Azure DevOps)
2. **Dependency Injection**: Configuration is injected into services for flexibility
3. **Error Handling**: Comprehensive error handling at each layer
4. **Logging**: Detailed logging for debugging and monitoring
5. **Single Responsibility**: Each module has one clear purpose

## Core Components

### 1. BuildFixer (Orchestrator)
**File**: `src/buildFixer.js`

The main orchestrator that coordinates the workflow:
- Manages the lifecycle of the analysis process
- Coordinates between services
- Handles error propagation
- Validates configuration

**Responsibilities**:
- Process build failures from local files or S3
- Orchestrate the 4-step workflow
- Return structured results

**Key Methods**:
- `processBuildFailure()`: Main workflow for local logs
- `processBuildFailureFromS3()`: Workflow for S3-stored logs
- `validateConfiguration()`: Ensures required config is present

### 2. S3Service
**File**: `src/services/s3Service.js`

Manages all AWS S3 operations for log storage.

**Responsibilities**:
- Upload build logs to S3
- Download build logs from S3
- Generate appropriate S3 keys with timestamps

**Dependencies**:
- `@aws-sdk/client-s3`: AWS SDK v3 for S3 operations

**Key Methods**:
- `uploadLog(logContent, buildId)`: Upload log with auto-generated key
- `downloadLog(key)`: Download log by S3 key

### 3. BedrockService
**File**: `src/services/bedrockService.js`

Integrates with Amazon Bedrock for AI-powered log analysis.

**Responsibilities**:
- Format prompts for log analysis
- Invoke Bedrock (Claude) model
- Parse and structure AI responses

**Dependencies**:
- `@aws-sdk/client-bedrock-runtime`: AWS SDK v3 for Bedrock

**Key Methods**:
- `analyzeLog(logContent)`: Main analysis method
- `createAnalysisPrompt(logContent)`: Format prompt for AI
- `parseAnalysisResponse(responseText)`: Extract RCA and recommendations

**Prompt Engineering**:
The service uses a structured prompt that:
- Identifies the AI as a DevOps expert
- Requests specific sections (RCA and Recommendations)
- Asks for concise, actionable output
- Uses markdown formatting for parsing

### 4. AzureDevOpsService
**File**: `src/services/azureDevOpsService.js`

Manages Azure DevOps API operations for work item creation.

**Responsibilities**:
- Authenticate with Azure DevOps
- Create user story work items
- Format descriptions with HTML
- Add relevant tags and metadata

**Dependencies**:
- `azure-devops-node-api`: Official Azure DevOps Node.js SDK

**Key Methods**:
- `initialize()`: Establish API connection
- `createWorkItem(buildId, rca, recommendations, buildUrl)`: Create user story
- `formatWorkItemDescription()`: Format HTML description
- `escapeHtml()`: Prevent XSS in work items

**Work Item Structure**:
- **Type**: User Story
- **Title**: "Build Failure Analysis - Build #[ID]"
- **Description**: HTML-formatted with sections for build info, RCA, and fixes
- **Tags**: "build-failure; automated-analysis"
- **Priority**: 1 (High)

### 5. Utilities
**File**: `src/utils/helpers.js`

Provides common utility functions.

**Functions**:
- `streamToString(stream)`: Convert S3 stream to string
- `readLogFile(filePath)`: Read local log files
- `validateConfig(config, fields)`: Validate configuration
- `truncateLog(logContent, maxLines)`: Handle large logs

**Log Truncation Strategy**:
- Keeps first 200 lines (context and setup)
- Keeps last 800 lines (actual errors)
- Adds truncation notice in the middle
- Total: ~1000 lines to stay within AI token limits

## Data Flow Diagram

```
┌──────────────────┐
│  Azure Pipeline  │
│   (Build Fails)  │
└────────┬─────────┘
         │
         ▼
┌────────────────────────────────────────────────────┐
│              index.js (CLI Entry)                  │
│  • Parses command line arguments                  │
│  • Loads environment variables                    │
│  • Instantiates BuildFixer                        │
└────────┬───────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────┐
│         BuildFixer (Main Orchestrator)             │
│                                                    │
│  processBuildFailure() {                          │
│    1. Read log file                               │
│    2. Upload to S3 (optional)                     │
│    3. Analyze with Bedrock                        │
│    4. Create work item                            │
│    5. Return results                              │
│  }                                                 │
└───┬────────┬────────────┬────────────┬─────────────┘
    │        │            │            │
    │        │            │            │
    ▼        ▼            ▼            ▼
┌────────┐ ┌──────────┐ ┌───────────┐ ┌─────────────┐
│ Local  │ │    S3    │ │  Bedrock  │ │Azure DevOps │
│  File  │ │ Service  │ │  Service  │ │   Service   │
│ System │ │          │ │           │ │             │
└────────┘ └────┬─────┘ └─────┬─────┘ └──────┬──────┘
                │             │              │
                ▼             ▼              ▼
         ┌──────────┐  ┌──────────┐  ┌──────────────┐
         │  AWS S3  │  │   AWS    │  │ Azure DevOps │
         │  Bucket  │  │ Bedrock  │  │  Work Items  │
         └──────────┘  └──────────┘  └──────────────┘
```

## Multiple Architectural Approaches

### Approach 1: Synchronous Pipeline Integration (Current Implementation)

**Architecture:**
```
Pipeline Failure → Build-Fixer Task → Analysis → Work Item → Pipeline Complete
```

**Pros:**
- Simple implementation
- Immediate feedback in pipeline logs
- No additional infrastructure required
- Easy to debug and maintain

**Cons:**
- Adds time to pipeline execution (1-2 minutes)
- Pipeline blocks until analysis completes
- Single point of failure

**Best For:**
- Small to medium teams
- Simple CI/CD setups
- Quick implementation needs

### Approach 2: Asynchronous Queue-Based Processing

**Architecture:**
```
Pipeline Failure → Queue Message → Build-Fixer Worker → Analysis → Work Item
                        ↓
                Pipeline Complete
```

**Implementation:**
- Use Azure Service Bus or AWS SQS
- Build-Fixer runs as background worker
- Pipeline triggers message on failure

**Pros:**
- Doesn't block pipeline
- Scalable (multiple workers)
- Resilient (retry on failure)
- Better separation of concerns

**Cons:**
- More complex infrastructure
- Delayed feedback (async)
- Additional costs (queue service)

**Best For:**
- Large teams with many pipelines
- High-throughput environments
- Production-grade deployments

### Approach 3: Webhook/Event-Driven Architecture

**Architecture:**
```
Azure DevOps Webhook → API Gateway → Lambda/Function → Build-Fixer → Analysis → Work Item
```

**Implementation:**
- Deploy Build-Fixer as serverless function
- Configure Azure DevOps webhooks
- Trigger on build completion events

**Pros:**
- Fully decoupled from pipeline
- Serverless scalability
- Multi-pipeline support
- Cost-effective (pay per use)

**Cons:**
- Requires hosting infrastructure
- Network dependencies
- More complex deployment
- Cold start latency

**Best For:**
- Multiple projects/teams
- Cloud-native environments
- Mature DevOps practices

### Approach 4: Scheduled Batch Processing

**Architecture:**
```
Cron/Scheduled Task → Query Failed Builds → Process Each → Analysis → Work Items
```

**Implementation:**
- Periodic job (e.g., every 15 minutes)
- Queries Azure DevOps for recent failures
- Processes unanalyzed builds

**Pros:**
- Very simple
- No pipeline modifications needed
- Low overhead on pipelines
- Easy rollback

**Cons:**
- Delayed analysis (up to schedule interval)
- Less immediate value
- May miss rapid builds

**Best For:**
- Pilot programs
- Legacy pipelines
- Low-frequency builds

### Approach 5: Hybrid Real-Time + Batch

**Architecture:**
```
High Priority Builds → Synchronous Processing
Low Priority Builds → Queue → Batch Processing
```

**Implementation:**
- Critical pipelines use sync processing
- Non-critical use async/batch
- Configurable per pipeline

**Pros:**
- Best of both worlds
- Flexible prioritization
- Optimized resource usage

**Cons:**
- Most complex to implement
- Requires careful configuration
- Higher maintenance

**Best For:**
- Large enterprises
- Mixed criticality workloads
- Mature DevOps organizations

## Recommended Implementation Path

1. **Start with Approach 1** (Current): Simple, quick value
2. **Scale to Approach 2**: When processing >50 builds/day
3. **Consider Approach 3**: For multi-team/multi-project scenarios
4. **Evaluate Approach 5**: For enterprise-scale deployments

## Security Considerations

### Credential Management
- Never log credentials
- Use environment variables or secure vaults
- Rotate tokens regularly

### Data Privacy
- Build logs may contain sensitive information
- S3 buckets should have appropriate access controls
- Consider encryption at rest and in transit

### Access Control
- Azure DevOps PAT should have minimal permissions
- AWS IAM user should follow least privilege principle
- Separate credentials for different environments
