# API Reference

Complete API documentation for Build-Fixer classes and methods.

## Table of Contents
- [BuildFixer](#buildfixer)
- [S3Service](#s3service)
- [BedrockService](#bedrockservice)
- [AzureDevOpsService](#azuredevopsservice)
- [Utilities](#utilities)

---

## BuildFixer

Main orchestrator class that coordinates the build failure analysis workflow.

### Constructor

```javascript
new BuildFixer(config)
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| config | Object | Yes | Configuration object |
| config.aws | Object | Yes | AWS configuration |
| config.aws.region | string | Yes | AWS region (e.g., 'us-east-1') |
| config.aws.accessKeyId | string | Yes | AWS access key ID |
| config.aws.secretAccessKey | string | Yes | AWS secret access key |
| config.aws.s3BucketName | string | Yes | S3 bucket name for logs |
| config.aws.bedrockModelId | string | No | Bedrock model ID (default: Claude 3 Sonnet) |
| config.azureDevOps | Object | Yes | Azure DevOps configuration |
| config.azureDevOps.orgUrl | string | Yes | Organization URL |
| config.azureDevOps.token | string | Yes | Personal access token |
| config.azureDevOps.project | string | Yes | Project name |

**Example:**

```javascript
const BuildFixer = require('./src/buildFixer');

const buildFixer = new BuildFixer({
  aws: {
    region: 'us-east-1',
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
    s3BucketName: 'my-build-logs',
    bedrockModelId: 'anthropic.claude-3-sonnet-20240229-v1:0'
  },
  azureDevOps: {
    orgUrl: 'https://dev.azure.com/myorg',
    token: process.env.AZURE_DEVOPS_TOKEN,
    project: 'MyProject'
  }
});
```

### Methods

#### processBuildFailure

Process a build failure from a local log file.

```javascript
async processBuildFailure(options)
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| options | Object | Yes | Processing options |
| options.logFilePath | string | Yes | Path to build log file |
| options.buildId | string | Yes | Build identifier |
| options.buildUrl | string | Yes | URL to the failed build |
| options.uploadToS3 | boolean | No | Upload to S3 (default: true) |

**Returns:** `Promise<Object>`

```javascript
{
  success: boolean,        // Always true on success
  buildId: string,         // Build ID provided
  s3Key: string | null,    // S3 key if uploaded, null otherwise
  analysis: {
    rca: string,           // Root cause analysis
    recommendations: string, // Recommended fixes
    fullAnalysis: string   // Complete AI response
  },
  workItem: {
    id: number,            // Work item ID
    url: string            // Work item URL
  }
}
```

**Example:**

```javascript
const results = await buildFixer.processBuildFailure({
  logFilePath: '/path/to/build.log',
  buildId: '12345',
  buildUrl: 'https://dev.azure.com/org/project/_build/results?buildId=12345',
  uploadToS3: true
});

console.log(`Work item created: ${results.workItem.url}`);
```

**Throws:**
- `Error` if log file cannot be read
- `Error` if S3 upload fails (when uploadToS3=true)
- `Error` if Bedrock analysis fails
- `Error` if work item creation fails

#### processBuildFailureFromS3

Process a build failure from an existing S3 log file.

```javascript
async processBuildFailureFromS3(options)
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| options | Object | Yes | Processing options |
| options.s3Key | string | Yes | S3 key of the log file |
| options.buildId | string | Yes | Build identifier |
| options.buildUrl | string | Yes | URL to the failed build |

**Returns:** `Promise<Object>` (same structure as processBuildFailure)

**Example:**

```javascript
const results = await buildFixer.processBuildFailureFromS3({
  s3Key: 'build-logs/12345-1234567890.log',
  buildId: '12345',
  buildUrl: 'https://dev.azure.com/org/project/_build/results?buildId=12345'
});
```

---

## S3Service

Manages AWS S3 operations for build log storage.

### Constructor

```javascript
new S3Service(config)
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| config | Object | Yes | S3 configuration |
| config.region | string | Yes | AWS region |
| config.accessKeyId | string | Yes | AWS access key ID |
| config.secretAccessKey | string | Yes | AWS secret access key |
| config.bucketName | string | Yes | S3 bucket name |

### Methods

#### uploadLog

Upload a build log to S3.

```javascript
async uploadLog(logContent, buildId)
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| logContent | string | Yes | Build log content |
| buildId | string | Yes | Build identifier |

**Returns:** `Promise<string>` - S3 key of uploaded file

**Example:**

```javascript
const s3Key = await s3Service.uploadLog(logContent, '12345');
// Returns: 'build-logs/12345-1634567890123.log'
```

#### downloadLog

Download a build log from S3.

```javascript
async downloadLog(key)
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| key | string | Yes | S3 key of the log file |

**Returns:** `Promise<string>` - Log file content

**Example:**

```javascript
const logContent = await s3Service.downloadLog('build-logs/12345.log');
```

---

## BedrockService

Integrates with Amazon Bedrock for AI-powered log analysis.

### Constructor

```javascript
new BedrockService(config)
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| config | Object | Yes | Bedrock configuration |
| config.region | string | Yes | AWS region |
| config.accessKeyId | string | Yes | AWS access key ID |
| config.secretAccessKey | string | Yes | AWS secret access key |
| config.modelId | string | No | Model ID (default: Claude 3 Sonnet) |

### Methods

#### analyzeLog

Analyze a build log and generate RCA and recommendations.

```javascript
async analyzeLog(logContent)
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| logContent | string | Yes | Build log content to analyze |

**Returns:** `Promise<Object>`

```javascript
{
  rca: string,              // Root cause analysis
  recommendations: string,   // Recommended fixes
  fullAnalysis: string      // Complete AI response
}
```

**Example:**

```javascript
const analysis = await bedrockService.analyzeLog(logContent);
console.log('RCA:', analysis.rca);
console.log('Fixes:', analysis.recommendations);
```

#### createAnalysisPrompt

Create a structured prompt for Bedrock analysis.

```javascript
createAnalysisPrompt(logContent)
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| logContent | string | Yes | Build log content |

**Returns:** `string` - Formatted prompt

**Example:**

```javascript
const prompt = bedrockService.createAnalysisPrompt(logContent);
// Returns formatted prompt with instructions
```

#### parseAnalysisResponse

Parse Bedrock response to extract structured data.

```javascript
parseAnalysisResponse(responseText)
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| responseText | string | Yes | Raw response from Bedrock |

**Returns:** `Object` - Structured analysis

---

## AzureDevOpsService

Manages Azure DevOps API operations for work item creation.

### Constructor

```javascript
new AzureDevOpsService(config)
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| config | Object | Yes | Azure DevOps configuration |
| config.orgUrl | string | Yes | Organization URL |
| config.token | string | Yes | Personal access token |
| config.project | string | Yes | Project name |

### Methods

#### initialize

Initialize connection to Azure DevOps.

```javascript
async initialize()
```

**Returns:** `Promise<void>`

**Example:**

```javascript
await azureDevOpsService.initialize();
```

#### createWorkItem

Create a user story work item with analysis results.

```javascript
async createWorkItem(buildId, rca, recommendations, buildUrl)
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| buildId | string | Yes | Build identifier |
| rca | string | Yes | Root cause analysis |
| recommendations | string | Yes | Recommended fixes |
| buildUrl | string | Yes | URL to failed build |

**Returns:** `Promise<Object>`

```javascript
{
  id: number,      // Work item ID
  url: string      // Work item URL
}
```

**Example:**

```javascript
const workItem = await azureDevOpsService.createWorkItem(
  '12345',
  'Root cause is...',
  'Fix by...',
  'https://dev.azure.com/...'
);
console.log(`Created work item ${workItem.id}`);
```

#### formatWorkItemDescription

Format work item description with RCA and recommendations.

```javascript
formatWorkItemDescription(rca, recommendations, buildUrl)
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| rca | string | Yes | Root cause analysis |
| recommendations | string | Yes | Recommended fixes |
| buildUrl | string | Yes | URL to failed build |

**Returns:** `string` - HTML-formatted description

---

## Utilities

Helper functions for common operations.

### streamToString

Convert a readable stream to string.

```javascript
async streamToString(stream)
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| stream | ReadableStream | Yes | Stream to convert |

**Returns:** `Promise<string>` - String content

**Example:**

```javascript
const content = await streamToString(s3Response.Body);
```

### readLogFile

Read a log file from the local filesystem.

```javascript
async readLogFile(filePath)
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| filePath | string | Yes | Path to log file |

**Returns:** `Promise<string>` - File content

**Example:**

```javascript
const logContent = await readLogFile('./build.log');
```

### validateConfig

Validate required configuration fields.

```javascript
validateConfig(config, requiredFields)
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| config | Object | Yes | Configuration object |
| requiredFields | Array<string> | Yes | Required field names |

**Throws:** `Error` if required fields are missing

**Example:**

```javascript
validateConfig(config.aws, ['region', 'accessKeyId', 'secretAccessKey']);
```

### truncateLog

Truncate large log files intelligently.

```javascript
truncateLog(logContent, maxLines = 1000)
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| logContent | string | Yes | Log content to truncate |
| maxLines | number | No | Max lines to keep (default: 1000) |

**Returns:** `string` - Truncated log content

**Strategy:**
- Keeps first 200 lines (setup context)
- Keeps last 800 lines (errors)
- Adds truncation notice

**Example:**

```javascript
const truncated = truncateLog(largeLogContent, 500);
```

---

## Error Handling

All async methods can throw errors. Always use try-catch:

```javascript
try {
  const results = await buildFixer.processBuildFailure(options);
} catch (error) {
  console.error('Failed to process build:', error.message);
}
```

Common error types:
- **Configuration errors**: Missing required config
- **AWS errors**: S3 or Bedrock API failures
- **Azure DevOps errors**: Authentication or API failures
- **File system errors**: File not found or permission issues

---

## TypeScript Support

While this is a JavaScript project, you can create TypeScript definitions:

```typescript
interface BuildFixerConfig {
  aws: {
    region: string;
    accessKeyId: string;
    secretAccessKey: string;
    s3BucketName: string;
    bedrockModelId?: string;
  };
  azureDevOps: {
    orgUrl: string;
    token: string;
    project: string;
  };
}

interface ProcessOptions {
  logFilePath: string;
  buildId: string;
  buildUrl: string;
  uploadToS3?: boolean;
}

interface ProcessResults {
  success: boolean;
  buildId: string;
  s3Key: string | null;
  analysis: {
    rca: string;
    recommendations: string;
    fullAnalysis: string;
  };
  workItem: {
    id: number;
    url: string;
  };
}

class BuildFixer {
  constructor(config: BuildFixerConfig);
  processBuildFailure(options: ProcessOptions): Promise<ProcessResults>;
  processBuildFailureFromS3(options: Omit<ProcessOptions, 'logFilePath'> & { s3Key: string }): Promise<ProcessResults>;
}
```

---

For more examples, see the [examples/](../examples/) directory.
