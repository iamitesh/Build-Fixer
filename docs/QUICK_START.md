# Quick Start Guide

Get started with Build-Fixer in 15 minutes.

## Prerequisites

- [ ] Node.js 18+ installed
- [ ] AWS Account with Bedrock access
- [ ] Azure DevOps account and project
- [ ] Basic knowledge of command line

## Step 1: Clone and Install (2 minutes)

```bash
# Clone the repository
git clone https://github.com/iamitesh/Build-Fixer.git
cd Build-Fixer

# Install dependencies
npm install
```

## Step 2: AWS Setup (5 minutes)

### 2.1 Enable Amazon Bedrock

1. Go to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock)
2. Click "Model access" in the left sidebar
3. Click "Request model access"
4. Select "Anthropic" → "Claude 3 Sonnet"
5. Click "Request model access" (usually instant approval)

### 2.2 Create S3 Bucket

```bash
# Using AWS CLI
aws s3 mb s3://my-build-logs-bucket --region us-east-1

# Or via AWS Console: S3 → Create bucket
```

### 2.3 Create IAM User

1. Go to AWS IAM Console → Users → Create user
2. User name: `build-fixer-user`
3. Create user → Security credentials → Create access key
4. Select "Application running outside AWS"
5. Save Access Key ID and Secret Access Key

### 2.4 Attach IAM Policy

Create and attach this policy to the user:

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
      "Resource": "arn:aws:s3:::my-build-logs-bucket/*"
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

## Step 3: Azure DevOps Setup (3 minutes)

### 3.1 Create Personal Access Token

1. Go to Azure DevOps
2. Click your profile picture (top right) → Personal access tokens
3. Click "+ New Token"
4. Name: `build-fixer-token`
5. Scopes:
   - ✅ Work Items: Read & Write
   - ✅ Build: Read (optional)
6. Click "Create"
7. **Copy the token immediately** (you won't see it again!)

### 3.2 Get Organization URL

Your organization URL format:
```
https://dev.azure.com/YOUR_ORGANIZATION_NAME
```

Example: `https://dev.azure.com/contoso`

## Step 4: Configuration (2 minutes)

### 4.1 Create .env file

```bash
cp .env.example .env
```

### 4.2 Edit .env with your values

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIA...your-key...
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_BUCKET_NAME=my-build-logs-bucket
AWS_BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Azure DevOps Configuration
AZURE_DEVOPS_ORG_URL=https://dev.azure.com/your-org
AZURE_DEVOPS_TOKEN=your-pat-token
AZURE_DEVOPS_PROJECT=YourProjectName
```

## Step 5: Test It! (3 minutes)

### 5.1 Test with sample log

```bash
node src/index.js \
  --log-file examples/sample-build-log.txt \
  --build-id test-001 \
  --build-url "https://dev.azure.com/yourorg/yourproject/_build/results?buildId=001" \
  --skip-s3-upload
```

Expected output:
```
============================================================
Build-Fixer: Starting build failure analysis...
Build ID: test-001
============================================================

Step 1: Reading build log file...
Log file read successfully (810 characters)

Step 2: Skipping S3 upload (uploadToS3=false)

Step 3: Analyzing build log with Amazon Bedrock...
Analysis completed successfully

Root Cause Analysis:
[AI-generated analysis]

Recommended Fixes:
[AI-generated recommendations]

Step 4: Creating work item in Azure DevOps...
Work item created: https://dev.azure.com/...

============================================================
Build-Fixer: Process completed successfully!
============================================================
```

### 5.2 Verify in Azure DevOps

1. Go to Azure DevOps → Boards → Work Items
2. Look for "Build Failure Analysis - Build #test-001"
3. Open it to see the RCA and recommendations

## Step 6: Pipeline Integration (Optional)

Add to your `azure-pipelines.yml`:

```yaml
# Add this stage to run when build fails
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

### Configure Pipeline Variables

1. Azure DevOps → Pipelines → Library → Variable groups
2. Create group: `build-fixer-config`
3. Add variables:
   - `AWS_REGION` (not secret)
   - `AWS_ACCESS_KEY_ID` (secret)
   - `AWS_SECRET_ACCESS_KEY` (secret)
   - `AWS_S3_BUCKET_NAME` (not secret)
   - `AZURE_DEVOPS_TOKEN` (secret)

## Usage Patterns

### Pattern 1: Local Development
```bash
# Analyze your local failed build
node src/index.js \
  --log-file ./build-output.log \
  --build-id local-$(date +%s) \
  --skip-s3-upload
```

### Pattern 2: CI/CD Integration
```yaml
# In your pipeline after build fails
- Run Build-Fixer
- Creates work item automatically
- Team gets notified
```

### Pattern 3: Batch Processing
```bash
# Analyze multiple logs
for log in logs/*.log; do
  node src/index.js --log-file "$log" --build-id "${log%.log}"
done
```

## Next Steps

- ✅ Read the [full README](../README.md) for detailed documentation
- ✅ Check [ARCHITECTURE.md](ARCHITECTURE.md) to understand the design
- ✅ Review [TROUBLESHOOTING.md](TROUBLESHOOTING.md) if you hit issues
- ✅ See [examples/](../examples/) for more usage patterns
- ✅ Star the repo if you find it useful! ⭐

## Common Issues

### "Cannot find module 'dotenv'"
```bash
npm install
```

### "User is not authorized to perform: bedrock:InvokeModel"
Check that:
1. Bedrock model access is enabled
2. IAM policy includes `bedrock:InvokeModel`
3. Using correct AWS region

### "The user is not authorized to access this resource" (Azure DevOps)
Check that:
1. PAT token is valid and not expired
2. Token has "Work Items: Read & Write" permissions
3. Project name in .env is correct

### Work item created but empty
Check that:
1. Build log file is not empty
2. Bedrock analysis completed successfully
3. Look at console output for errors

## Tips for Best Results

1. **Use descriptive build IDs**: `feature-auth-12345` instead of just `12345`
2. **Include build URLs**: Helps team find the failed build quickly
3. **Don't skip S3**: Helpful for historical analysis
4. **Review work items**: AI suggestions need human review
5. **Customize prompts**: Edit `bedrockService.js` for domain-specific analysis

## Cost Estimation

Typical costs per build analysis:
- **Bedrock**: $0.003 - $0.015 per request
- **S3**: $0.001 per log file
- **Azure DevOps**: Free (API included)

For 100 build failures/month: **~$1-2 total**

## Support

- 📖 [Documentation](../README.md)
- 🐛 [Report Issues](https://github.com/iamitesh/Build-Fixer/issues)
- 💬 [Discussions](https://github.com/iamitesh/Build-Fixer/discussions)
- 🤝 [Contributing](../CONTRIBUTING.md)

## Congratulations! 🎉

You're now ready to use Build-Fixer to automatically analyze build failures and create actionable work items. Happy building!
