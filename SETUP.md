# Setup Guide

This guide will walk you through setting up Build-Fixer for your Azure DevOps environment.

## Prerequisites Checklist

- [ ] AWS Account with administrative access
- [ ] Azure DevOps organization and project
- [ ] Python 3.8+ installed
- [ ] Git installed

## Step 1: AWS Setup

### 1.1 Create S3 Bucket

```bash
# Using AWS CLI
aws s3 mb s3://your-build-logs-bucket --region us-east-1

# Set lifecycle policy (optional but recommended)
aws s3api put-bucket-lifecycle-configuration \
  --bucket your-build-logs-bucket \
  --lifecycle-configuration file://s3-lifecycle.json
```

Example `s3-lifecycle.json`:
```json
{
  "Rules": [
    {
      "Id": "DeleteOldLogs",
      "Status": "Enabled",
      "Prefix": "build-logs/",
      "Expiration": {
        "Days": 90
      }
    }
  ]
}
```

### 1.2 Enable Amazon Bedrock

1. Go to AWS Console → Amazon Bedrock
2. Navigate to "Model access"
3. Request access to "Anthropic Claude 3 Sonnet"
4. Wait for approval (usually instant for most regions)

### 1.3 Create IAM User

Create an IAM user with the following policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-build-logs-bucket",
        "arn:aws:s3:::your-build-logs-bucket/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
    }
  ]
}
```

Save the Access Key ID and Secret Access Key.

## Step 2: Azure DevOps Setup

### 2.1 Create Personal Access Token (PAT)

1. Go to Azure DevOps → User Settings → Personal Access Tokens
2. Click "New Token"
3. Name: "Build-Fixer"
4. Scopes: Select "Work Items" → Read & Write
5. Click "Create"
6. **Important**: Copy the token immediately (you won't see it again)

### 2.2 Verify Project Settings

1. Note your organization URL: `https://dev.azure.com/your-org`
2. Note your project name
3. Ensure you have permissions to create work items

## Step 3: Install Build-Fixer

### 3.1 Clone Repository

```bash
git clone https://github.com/iamitesh/Build-Fixer.git
cd Build-Fixer
```

### 3.2 Install Dependencies

```bash
pip install -r requirements.txt
```

Or using a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Step 4: Configure Environment Variables

### 4.1 For Local Testing

Create a `.env` file (copy from `examples/config.example`):

```bash
cp examples/config.example .env
```

Edit `.env` with your values:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
S3_BUCKET_NAME=my-build-logs-bucket
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Azure DevOps Configuration
AZURE_DEVOPS_ORG_URL=https://dev.azure.com/myorg
AZURE_DEVOPS_PAT=your_pat_token_here
AZURE_DEVOPS_PROJECT=MyProject

# Work Item Configuration
WORK_ITEM_TYPE=User Story
WORK_ITEM_TAGS=build-failure,automated
```

Load the environment variables:

```bash
# On Linux/Mac
export $(cat .env | xargs)

# Or use python-dotenv
pip install python-dotenv
```

### 4.2 For Azure Pipelines

Add the following variables as **Secret Variables** in your pipeline:

1. Go to Azure DevOps → Pipelines → Your Pipeline → Edit
2. Click "Variables"
3. Add these variables (check "Keep this value secret" for sensitive values):
   - `AWS_ACCESS_KEY_ID` (secret)
   - `AWS_SECRET_ACCESS_KEY` (secret)
   - `AZURE_DEVOPS_PAT` (secret)
   - `S3_BUCKET_NAME`
   - `BEDROCK_MODEL_ID`
   - `AZURE_DEVOPS_PROJECT`
   - `WORK_ITEM_TYPE`
   - `WORK_ITEM_TAGS`

## Step 5: Test the Setup

### 5.1 Local Test

```bash
# Test with the example log file
python -m build_fixer.main examples/sample_build_failure.log --verbose
```

Expected output:
```
2024-01-10 14:30:22 - build_fixer.config_manager - INFO - Configuration loaded
2024-01-10 14:30:22 - build_fixer.s3_manager - INFO - Uploading log to S3...
2024-01-10 14:30:23 - build_fixer.bedrock_analyzer - INFO - Analyzing with Bedrock...
2024-01-10 14:30:28 - build_fixer.azure_devops_manager - INFO - Creating work item...
============================================================
Build Failure Processing Complete!
============================================================
S3 Log Key: build-logs/123456_20240110_143022.log
Work Item ID: 12345
...
```

### 5.2 Verify Results

1. Check S3 bucket for uploaded log
2. Check Azure DevOps for created work item
3. Review the RCA and recommendations

## Step 6: Integrate with Azure Pipeline

### 6.1 Add Build-Fixer Stage

Copy the content from `azure-pipeline-example.yml` and add it to your pipeline.

### 6.2 Test the Integration

1. Trigger a build that will fail (or temporarily break something)
2. Watch the Build-Fixer stage execute
3. Check Azure DevOps for the created work item

## Troubleshooting

### Issue: "Access Denied" when uploading to S3

**Solution**: Verify IAM permissions and bucket name

```bash
# Test S3 access
aws s3 ls s3://your-build-logs-bucket
```

### Issue: "Bedrock access denied"

**Solution**: 
1. Verify model access is enabled in Bedrock console
2. Check IAM permissions
3. Verify region supports Bedrock

### Issue: "Failed to create work item"

**Solution**:
1. Verify PAT has "Work Items: Read & Write" permissions
2. Check organization URL format: `https://dev.azure.com/orgname`
3. Verify project name is correct

### Issue: "Module not found" errors

**Solution**:
```bash
pip install -r requirements.txt --upgrade
```

## Advanced Configuration

### Custom Work Item Types

To use a custom work item type:

```bash
export WORK_ITEM_TYPE="Custom Work Item Type Name"
```

### Area and Iteration Paths

```bash
export WORK_ITEM_AREA_PATH="MyProject\\DevOps\\BuildAutomation"
export WORK_ITEM_ITERATION_PATH="MyProject\\Sprint 5"
```

### Different Bedrock Models

To use a different model:

```bash
export BEDROCK_MODEL_ID=anthropic.claude-3-opus-20240229-v1:0
```

Available models:
- `anthropic.claude-3-sonnet-20240229-v1:0` (recommended, balanced)
- `anthropic.claude-3-opus-20240229-v1:0` (most powerful, slower)
- `anthropic.claude-3-haiku-20240307-v1:0` (fastest, cheaper)

## Next Steps

1. Customize work item templates
2. Set up notifications for created work items
3. Integrate with your team's workflow
4. Monitor costs in AWS Cost Explorer
5. Review and improve RCA quality based on feedback

## Support

For issues, please open a GitHub issue or contact support.
