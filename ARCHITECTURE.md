# Build-Fixer Architecture

This document provides a detailed overview of the Build-Fixer architecture, component interactions, and design decisions.

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Azure DevOps Pipeline                           │
│  ┌──────────┐    ┌──────────┐    ┌────────────────┐               │
│  │  Build   │───>│ Test     │───>│ Build Failed   │               │
│  │  Stage   │    │ Stage    │    │ (Exit Code 1)  │               │
│  └──────────┘    └──────────┘    └────────┬───────┘               │
└─────────────────────────────────────────────┼──────────────────────┘
                                              │
                                    ┌─────────▼────────────┐
                                    │ Analyze Failure      │
                                    │ Stage (Conditional)  │
                                    └─────────┬────────────┘
                                              │
                                    ┌─────────▼────────────┐
                                    │   Build-Fixer Tool   │
                                    │  ┌─────────────────┐ │
                                    │  │ 1. Upload Log   │ │
                                    │  │ 2. AI Analysis  │ │
                                    │  │ 3. Create WI    │ │
                                    │  └─────────────────┘ │
                                    └──┬────┬────┬─────────┘
                                       │    │    │
                        ┌──────────────┘    │    └──────────────┐
                        ▼                   ▼                   ▼
              ┌─────────────────┐  ┌─────────────┐   ┌─────────────────┐
              │   Amazon S3     │  │   Bedrock   │   │  Azure DevOps   │
              │  (Log Storage)  │  │ (AI Model)  │   │ (Work Items)    │
              └─────────────────┘  └─────────────┘   └─────────────────┘
```

## Components

### 1. Config Manager (`config_manager.py`)

**Responsibility**: Centralized configuration management

**Key Features**:
- Loads configuration from environment variables
- Validates required configuration
- Provides configuration access to other components

**Design Decisions**:
- Environment variables chosen for easy CI/CD integration
- Validation separates configuration errors from runtime errors
- Extensible to support config files (JSON, YAML, INI)

**Configuration Sources** (Priority Order):
1. Environment variables (current implementation)
2. Configuration file (future enhancement)
3. Default values

### 2. S3 Manager (`s3_manager.py`)

**Responsibility**: Manage log file storage in Amazon S3

**Key Features**:
- Upload logs with timestamped keys
- Download logs when needed
- Stream log content without local file
- Automatic directory creation

**Design Decisions**:
- Uses boto3 for AWS SDK integration
- Timestamped keys prevent collisions
- Organized folder structure: `build-logs/{build_id}_{timestamp}.log`
- Graceful error handling with logging

**S3 Bucket Structure**:
```
s3://your-bucket/
└── build-logs/
    ├── 123456_20240110_143022.log
    ├── 123457_20240110_154533.log
    └── 123458_20240110_162044.log
```

### 3. Bedrock Analyzer (`bedrock_analyzer.py`)

**Responsibility**: AI-powered build failure analysis

**Key Features**:
- Invokes Amazon Bedrock (Claude 3)
- Generates structured RCA
- Provides actionable recommendations
- Handles JSON and text responses
- Fallback parsing for non-JSON responses

**Design Decisions**:
- Claude 3 Sonnet chosen for balance of speed and quality
- Log truncation to prevent token overflow (last 10K chars)
- Structured prompt engineering for consistent output
- Robust parsing with fallback mechanisms

**Prompt Engineering**:
```
Input: Raw build log
↓
Prompt: Expert DevOps engineer analyzing failure
↓
Output: JSON with 'rca' and 'recommendations'
```

**Supported Models**:
- Claude 3 Haiku (fastest, cheapest)
- Claude 3 Sonnet (balanced, default)
- Claude 3 Opus (most capable)

### 4. Azure DevOps Manager (`azure_devops_manager.py`)

**Responsibility**: Create and manage work items in Azure DevOps

**Key Features**:
- Creates User Stories or Bugs
- Rich HTML formatting for RCA and recommendations
- Supports custom fields (area path, iteration, assignment)
- Tag support for categorization

**Design Decisions**:
- Uses official Azure DevOps Python SDK
- HTML formatting for better readability
- Separate methods for User Story vs Bug
- Flexible field assignment

**Work Item Structure**:
```
Title: Build Failure: {repo} - Build #{number} ({branch})
Description: Build context and log location
├── RCA Section (red border)
├── Recommendations Section (green border)
└── Automated attribution
Tags: build-failure, automated, ...
```

### 5. Main Orchestrator (`main.py`)

**Responsibility**: Coordinate the entire workflow

**Key Features**:
- End-to-end workflow orchestration
- CLI interface
- Error handling and reporting
- Logging and monitoring

**Workflow**:
```
1. Validate Configuration
   ↓
2. Upload Log to S3
   ↓
3. Read Log Content
   ↓
4. Analyze with Bedrock
   ↓
5. Create Work Item
   ↓
6. Report Results
```

**Error Handling Strategy**:
- Each step can fail independently
- Failures are logged with context
- Partial success is reported (e.g., log uploaded but work item creation failed)

## Data Flow

### 1. Log Upload Flow

```
Local File → S3Manager.upload_log_file()
                ↓
           boto3.s3.upload_file()
                ↓
         S3 Bucket (versioned)
```

### 2. Analysis Flow

```
Log Content → BedrockAnalyzer.analyze_build_failure()
                     ↓
           _create_analysis_prompt()
                     ↓
              _invoke_bedrock()
                     ↓
         Bedrock API (Claude 3)
                     ↓
              _parse_response()
                     ↓
        {'rca': '...', 'recommendations': '...'}
```

### 3. Work Item Creation Flow

```
Analysis Results → AzureDevOpsManager.create_user_story()
                           ↓
                   _format_description()
                           ↓
                  JsonPatchOperation[]
                           ↓
              wit_client.create_work_item()
                           ↓
                   Azure DevOps API
                           ↓
                      Work Item #ID
```

## Security Considerations

### Credentials Management
- AWS credentials via environment variables or IAM roles
- Azure DevOps PAT via environment variables (marked as secret)
- Never log or expose sensitive credentials

### Least Privilege Access
- S3: Only PutObject, GetObject, ListBucket
- Bedrock: Only InvokeModel for specific model
- Azure DevOps: Only work item read/write

### Data Privacy
- Build logs may contain sensitive information
- S3 bucket should have appropriate access controls
- Consider encryption at rest and in transit

## Scalability

### Current Limitations
- Synchronous processing (one build at a time)
- No queueing mechanism
- Single-threaded execution

### Future Enhancements
- Async processing with queues (SQS, Azure Service Bus)
- Parallel analysis of multiple builds
- Caching of common error patterns
- Distributed execution

## Extensibility

### Adding New Features

#### 1. New Storage Backend
Create a new manager implementing the same interface:
```python
class AzureBlobManager:
    def upload_log_file(self, local_path, key):
        pass
    
    def download_log_file(self, key, local_path):
        pass
```

#### 2. New AI Provider
Create a new analyzer:
```python
class OpenAIAnalyzer:
    def analyze_build_failure(self, log_content):
        # Return same structure: {'rca': '...', 'recommendations': '...'}
        pass
```

#### 3. New Work Item System
Create a new work item manager:
```python
class JiraManager:
    def create_issue(self, title, description, rca, recommendations):
        pass
```

## Performance Considerations

### Bottlenecks
1. **Bedrock API call**: 5-15 seconds depending on log size
2. **S3 upload**: Depends on log size and network speed
3. **Azure DevOps API**: Usually < 1 second

### Optimization Strategies
- Log truncation to reduce Bedrock processing time
- Async uploads to S3
- Batch work item creation
- Response caching for similar errors

## Monitoring and Observability

### Logging Levels
- **INFO**: Normal operation flow
- **WARNING**: Recoverable issues
- **ERROR**: Operation failures
- **DEBUG**: Detailed diagnostic information

### Metrics to Track
- Time to analyze (Bedrock latency)
- Success rate of work item creation
- S3 upload success rate
- Cost per analysis

### Future Monitoring
- Integration with CloudWatch, Application Insights
- Custom metrics dashboard
- Alerting on failure patterns

## Cost Optimization

### Current Costs (Per Analysis)
- S3 storage: ~$0.001 per log file (< 10KB typical)
- Bedrock invocation: ~$0.01-0.05 per analysis
- Azure DevOps API: Free (within limits)
- Total: ~$0.01-0.05 per build failure

### Optimization Strategies
- Use cheaper Bedrock models (Haiku) for simple errors
- Implement caching for known error patterns
- S3 lifecycle policies to delete old logs
- Batch processing to reduce API calls

## Future Architecture Enhancements

### 1. Event-Driven Architecture
```
Azure DevOps → Webhook → Azure Function → Build-Fixer
                    ↓
             Event Grid/Service Bus
```

### 2. Microservices Architecture
```
API Gateway
    ├── Log Service (S3 Manager)
    ├── Analysis Service (Bedrock)
    └── Work Item Service (Azure DevOps)
```

### 3. Machine Learning Enhancement
- Train custom models on historical build failures
- Pattern recognition for common errors
- Predictive analysis to prevent failures

## Testing Strategy

### Unit Tests
- Test each component in isolation
- Mock external dependencies (boto3, Azure SDK)

### Integration Tests
- Test component interactions
- Use test AWS/Azure environments

### End-to-End Tests
- Full workflow testing
- Verify work item creation

## Deployment Options

### 1. Azure DevOps Pipeline (Current)
- Runs as pipeline stage
- No separate deployment needed

### 2. Azure Function (Future)
- Serverless deployment
- Triggered by webhook

### 3. Container (Future)
- Docker image
- Kubernetes deployment for scale

## Conclusion

Build-Fixer is designed with modularity, extensibility, and maintainability in mind. Each component has a single responsibility and can be enhanced or replaced independently. The architecture supports both current use cases and future enhancements.
