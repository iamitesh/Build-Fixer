# Build-Fixer

Automated build failure analyzer for Azure DevOps pipelines using AWS Bedrock AI and S3 storage.

## 🎯 Overview

Build-Fixer is an intelligent CI/CD tool that automatically analyzes failed build pipelines, generates root cause analysis (RCA) using Amazon Bedrock AI, and creates user stories in Azure DevOps with recommended fixes. It seamlessly integrates into your Azure DevOps pipeline to reduce debugging time and improve developer productivity.

## 🚀 Key Features

- **Automated Log Analysis**: Leverages Amazon Bedrock (Claude AI) to analyze build logs and identify failure root causes
- **S3 Integration**: Stores build logs in AWS S3 for centralized storage and historical analysis
- **Azure DevOps Integration**: Automatically creates user stories with RCA and recommended fixes on your DevOps board
- **Pipeline Integration**: Easy integration into Azure DevOps pipelines as a failure handler
- **Flexible Usage**: Can be used as a CLI tool, Node.js library, or pipeline task
- **Intelligent Truncation**: Handles large log files by intelligently truncating while preserving important context

## 📋 Table of Contents

- [Justification](#justification)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Azure DevOps Pipeline Integration](#azure-devops-pipeline-integration)
- [API Documentation](#api-documentation)
- [Examples](#examples)
- [Contributing](#contributing)

## 💡 Justification

### Why Build This Tool?

#### 1. **Reduced Mean Time to Resolution (MTTR)**
- Manual log analysis can take 30-60 minutes per build failure
- Build-Fixer reduces this to seconds using AI-powered analysis
- Developers can focus on fixing issues rather than debugging logs

#### 2. **Improved Developer Productivity**
- Eliminates context switching by automatically creating actionable work items
- Provides specific, actionable recommendations rather than generic error messages
- Reduces cognitive load on developers dealing with complex build failures

#### 3. **Knowledge Preservation**
- Centralizes build failure history in S3
- Creates searchable work items in Azure DevOps
- Builds organizational knowledge base of common failures and fixes

#### 4. **Cost Savings**
- Reduces developer time spent on debugging (estimated 20-30% time savings)
- Prevents repeated failures by documenting fixes
- Optimizes cloud costs by quickly identifying resource issues

#### 5. **Continuous Improvement**
- Tracks patterns in build failures over time
- Enables data-driven improvements to CI/CD processes
- Facilitates proactive prevention of common issues

### Business Impact

| Metric | Without Build-Fixer | With Build-Fixer | Improvement |
|--------|---------------------|------------------|-------------|
| Avg. Time to Identify Root Cause | 30-60 min | 1-2 min | ~95% faster |
| Developer Context Switches | High | Low | ~70% reduction |
| Documentation Quality | Inconsistent | Standardized | Consistent |
| Historical Analysis | Manual | Automated | 100% coverage |

## 🏗️ Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Azure DevOps Pipeline                        │
│                                                                   │
│  ┌──────────┐      ┌──────────┐      ┌──────────────┐          │
│  │  Build   │─────▶│  Tests   │─────▶│  Deploy      │          │
│  └──────────┘      └──────────┘      └──────────────┘          │
│       │                  │                                        │
│       └──────────────────┴─────────┐                             │
│                                    ▼                              │
│                          ┌──────────────────┐                    │
│                          │  Build Failure   │                    │
│                          │   Detection      │                    │
│                          └──────────────────┘                    │
└───────────────────────────────────┬───────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │      Build-Fixer Tool         │
                    │                               │
                    │  ┌─────────────────────────┐  │
                    │  │  1. Log Collection      │  │
                    │  └─────────────────────────┘  │
                    │             │                 │
                    │             ▼                 │
                    │  ┌─────────────────────────┐  │
                    │  │  2. S3 Upload           │◀─┼─── AWS S3
                    │  └─────────────────────────┘  │
                    │             │                 │
                    │             ▼                 │
                    │  ┌─────────────────────────┐  │
                    │  │  3. AI Analysis         │◀─┼─── Amazon Bedrock
                    │  │     (Bedrock/Claude)    │  │     (Claude AI)
                    │  └─────────────────────────┘  │
                    │             │                 │
                    │             ▼                 │
                    │  ┌─────────────────────────┐  │
                    │  │  4. Work Item Creation  │──┼───▶ Azure DevOps
                    │  │     (User Story)        │  │      Work Items
                    │  └─────────────────────────┘  │
                    └───────────────────────────────┘
```

### Component Architecture

```
build-fixer/
├── src/
│   ├── index.js                  # CLI entry point
│   ├── buildFixer.js             # Main orchestrator
│   ├── services/
│   │   ├── s3Service.js          # AWS S3 integration
│   │   ├── bedrockService.js     # Amazon Bedrock AI integration
│   │   └── azureDevOpsService.js # Azure DevOps API integration
│   └── utils/
│       └── helpers.js            # Utility functions
├── examples/
│   ├── usage-example.js          # Usage examples
│   └── azure-pipeline.yml        # Pipeline integration example
└── config/
    └── .env.example              # Configuration template
```

### Data Flow

1. **Build Failure Detection**: Azure DevOps pipeline detects a build failure
2. **Log Collection**: Build-Fixer retrieves the build log file
3. **S3 Storage**: Log is uploaded to AWS S3 for persistence and historical analysis
4. **AI Analysis**: Amazon Bedrock (Claude AI) analyzes the log to identify:
   - Root cause of the failure
   - Recommended fixes and solutions
   - Relevant error patterns
5. **Work Item Creation**: A user story is created in Azure DevOps with:
   - Build information and link
   - Detailed RCA
   - Actionable recommendations
   - Auto-tagged for tracking

### Architecture Approaches

#### Approach 1: Synchronous Pipeline Integration (Recommended)
- Build-Fixer runs as a pipeline task after build failure
- Provides immediate feedback in the pipeline logs
- Creates work item before pipeline completes
- **Pros**: Simple, immediate results, no additional infrastructure
- **Cons**: Adds time to pipeline execution

#### Approach 2: Asynchronous Queue-Based
- Build failures trigger a message to Azure Service Bus/AWS SQS
- Build-Fixer runs as a separate service processing the queue
- **Pros**: Doesn't block pipeline, scalable
- **Cons**: More complex infrastructure, delayed feedback

#### Approach 3: Webhook-Based
- Azure DevOps webhook triggers Build-Fixer API endpoint
- Build-Fixer runs as a web service (Azure Functions/AWS Lambda)
- **Pros**: Decoupled, can handle multiple pipelines
- **Cons**: Requires hosting infrastructure, network dependencies

#### Approach 4: Scheduled Batch Processing
- Periodic job scans for failed builds and processes them
- **Pros**: Simple, low overhead on pipelines
- **Cons**: Delayed analysis, less immediate value

**Current Implementation**: This tool implements **Approach 1** for simplicity and immediate value, but can be adapted for any approach.

## 📦 Installation

### Prerequisites

- Node.js 18+ and npm
- AWS Account with Bedrock access
- Azure DevOps organization and project
- AWS S3 bucket for log storage

### Install Dependencies

```bash
# Clone the repository
git clone https://github.com/iamitesh/Build-Fixer.git
cd Build-Fixer

# Install dependencies
npm install
```

## ⚙️ Configuration

### 1. AWS Setup

#### Enable Amazon Bedrock
1. Go to AWS Console → Amazon Bedrock
2. Request access to Claude models (anthropic.claude-3-sonnet)
3. Wait for approval (usually instant for existing AWS accounts)

#### Create S3 Bucket
```bash
aws s3 mb s3://your-build-logs-bucket --region us-east-1
```

#### Create IAM User with Permissions
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::your-build-logs-bucket/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "*"
    }
  ]
}
```

### 2. Azure DevOps Setup

#### Create Personal Access Token (PAT)
1. Go to Azure DevOps → User Settings → Personal Access Tokens
2. Create new token with permissions:
   - **Work Items**: Read & Write
   - **Build**: Read
3. Copy the token (you won't see it again)

### 3. Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:
```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_S3_BUCKET_NAME=your-build-logs-bucket
AWS_BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Azure DevOps Configuration
AZURE_DEVOPS_ORG_URL=https://dev.azure.com/your-organization
AZURE_DEVOPS_TOKEN=your-personal-access-token
AZURE_DEVOPS_PROJECT=your-project-name
```

## 🎮 Usage

### CLI Usage

#### Analyze a local log file
```bash
node src/index.js \
  --log-file ./build.log \
  --build-id 12345 \
  --build-url "https://dev.azure.com/org/project/_build/results?buildId=12345"
```

#### Analyze a log file already in S3
```bash
node src/index.js \
  --s3-key "build-logs/12345-1234567890.log" \
  --build-id 12345 \
  --build-url "https://dev.azure.com/org/project/_build/results?buildId=12345"
```

#### Skip S3 upload
```bash
node src/index.js \
  --log-file ./build.log \
  --build-id 12345 \
  --skip-s3-upload
```

### Programmatic Usage

```javascript
const BuildFixer = require('./src/buildFixer');

const config = {
  aws: {
    region: 'us-east-1',
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
    s3BucketName: 'my-build-logs-bucket'
  },
  azureDevOps: {
    orgUrl: 'https://dev.azure.com/my-org',
    token: process.env.AZURE_DEVOPS_TOKEN,
    project: 'MyProject'
  }
};

const buildFixer = new BuildFixer(config);

// Process build failure
const results = await buildFixer.processBuildFailure({
  logFilePath: './build.log',
  buildId: '12345',
  buildUrl: 'https://dev.azure.com/...',
  uploadToS3: true
});

console.log('Work item created:', results.workItem.url);
```

## 🔗 Azure DevOps Pipeline Integration

### Basic Integration

Add this to your `azure-pipelines.yml`:

```yaml
trigger:
  - main

pool:
  vmImage: 'ubuntu-latest'

variables:
  - group: build-fixer-config  # Variable group with credentials

stages:
  - stage: Build
    jobs:
      - job: BuildJob
        steps:
          - task: NodeTool@0
            inputs:
              versionSpec: '20.x'
          
          - script: npm install && npm run build
            displayName: 'Build'
            continueOnError: true
          
          - script: npm test
            displayName: 'Test'
            continueOnError: true

  - stage: AnalyzeFailure
    condition: failed()
    dependsOn: Build
    jobs:
      - job: RunBuildFixer
        steps:
          - checkout: self
          
          - task: NodeTool@0
            inputs:
              versionSpec: '20.x'
          
          - script: |
              git clone https://github.com/iamitesh/Build-Fixer.git
              cd Build-Fixer
              npm install
              node src/index.js \
                --log-file $(System.DefaultWorkingDirectory)/build.log \
                --build-id $(Build.BuildId) \
                --build-url $(System.CollectionUri)$(System.TeamProject)/_build/results?buildId=$(Build.BuildId)
            displayName: 'Analyze Build Failure'
            env:
              AWS_REGION: $(AWS_REGION)
              AWS_ACCESS_KEY_ID: $(AWS_ACCESS_KEY_ID)
              AWS_SECRET_ACCESS_KEY: $(AWS_SECRET_ACCESS_KEY)
              AWS_S3_BUCKET_NAME: $(AWS_S3_BUCKET_NAME)
              AZURE_DEVOPS_ORG_URL: $(System.CollectionUri)
              AZURE_DEVOPS_TOKEN: $(AZURE_DEVOPS_TOKEN)
              AZURE_DEVOPS_PROJECT: $(System.TeamProject)
```

### Advanced: Custom Pipeline Task

See `examples/azure-pipeline.yml` for a complete example with multiple build stages and conditional analysis.

## 📚 API Documentation

### BuildFixer Class

#### Constructor
```javascript
new BuildFixer(config)
```

**Parameters:**
- `config.aws.region` (string): AWS region
- `config.aws.accessKeyId` (string): AWS access key ID
- `config.aws.secretAccessKey` (string): AWS secret access key
- `config.aws.s3BucketName` (string): S3 bucket name
- `config.aws.bedrockModelId` (string, optional): Bedrock model ID
- `config.azureDevOps.orgUrl` (string): Azure DevOps organization URL
- `config.azureDevOps.token` (string): Azure DevOps PAT
- `config.azureDevOps.project` (string): Azure DevOps project name

#### Methods

##### processBuildFailure(options)
Process a build failure from a local log file.

**Parameters:**
- `options.logFilePath` (string): Path to the build log file
- `options.buildId` (string): Build ID
- `options.buildUrl` (string): URL to the failed build
- `options.uploadToS3` (boolean, default: true): Whether to upload log to S3

**Returns:** Promise\<Object\>
```javascript
{
  success: true,
  buildId: "12345",
  s3Key: "build-logs/12345-1234567890.log",
  analysis: {
    rca: "Root cause analysis...",
    recommendations: "Recommended fixes...",
    fullAnalysis: "Complete analysis..."
  },
  workItem: {
    id: 123,
    url: "https://dev.azure.com/..."
  }
}
```

##### processBuildFailureFromS3(options)
Process a build failure from an existing S3 log file.

**Parameters:**
- `options.s3Key` (string): S3 key of the log file
- `options.buildId` (string): Build ID
- `options.buildUrl` (string): URL to the failed build

**Returns:** Promise\<Object\> (same as processBuildFailure)

## 📖 Examples

See the `examples/` directory for:
- `usage-example.js`: Programmatic usage examples
- `azure-pipeline.yml`: Complete Azure DevOps pipeline integration

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- Amazon Bedrock (Claude AI) for intelligent log analysis
- Azure DevOps for excellent API support
- AWS SDK for comprehensive cloud integration

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review examples for common use cases

---

**Built with ❤️ for better CI/CD workflows**