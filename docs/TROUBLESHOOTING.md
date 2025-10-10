# Troubleshooting Guide

Common issues and their solutions when using Build-Fixer.

## Table of Contents
- [Installation Issues](#installation-issues)
- [AWS Configuration Issues](#aws-configuration-issues)
- [Azure DevOps Issues](#azure-devops-issues)
- [Runtime Errors](#runtime-errors)
- [Log Analysis Issues](#log-analysis-issues)
- [Performance Issues](#performance-issues)

## Installation Issues

### npm install fails

**Problem**: Dependencies fail to install

**Solutions**:
```bash
# Clear npm cache
npm cache clean --force

# Remove node_modules and package-lock.json
rm -rf node_modules package-lock.json

# Reinstall
npm install

# If still failing, try updating npm
npm install -g npm@latest
```

### Node.js version too old

**Problem**: `node: command not found` or version incompatibility

**Solution**:
```bash
# Check Node.js version (need 18+)
node --version

# Install/update Node.js using nvm
nvm install 20
nvm use 20
```

## AWS Configuration Issues

### AWS credentials not found

**Error**: `Missing required configuration: accessKeyId, secretAccessKey`

**Solutions**:
1. Check environment variables are set:
   ```bash
   echo $AWS_ACCESS_KEY_ID
   echo $AWS_SECRET_ACCESS_KEY
   ```

2. Verify `.env` file exists and has correct values:
   ```bash
   cat .env
   ```

3. Ensure no extra spaces in `.env`:
   ```bash
   # WRONG
   AWS_ACCESS_KEY_ID = your-key
   
   # CORRECT
   AWS_ACCESS_KEY_ID=your-key
   ```

### Bedrock access denied

**Error**: `AccessDeniedException: User is not authorized to perform: bedrock:InvokeModel`

**Solutions**:
1. Verify Bedrock access is enabled in AWS Console:
   - Go to AWS Bedrock console
   - Check "Model access" in the left menu
   - Ensure Claude models are enabled

2. Check IAM permissions:
   ```json
   {
     "Effect": "Allow",
     "Action": "bedrock:InvokeModel",
     "Resource": "*"
   }
   ```

3. Verify AWS region supports Bedrock:
   - Bedrock is not available in all regions
   - Try `us-east-1` or `us-west-2`

### Bedrock model not found

**Error**: `ValidationException: The provided model identifier is invalid`

**Solution**:
```bash
# Check available models in your region
aws bedrock list-foundation-models --region us-east-1

# Use correct model ID
AWS_BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

### S3 upload fails

**Error**: `Failed to upload log to S3: Access Denied`

**Solutions**:
1. Check S3 bucket exists:
   ```bash
   aws s3 ls s3://your-bucket-name
   ```

2. Verify IAM permissions:
   ```json
   {
     "Effect": "Allow",
     "Action": ["s3:PutObject", "s3:GetObject"],
     "Resource": "arn:aws:s3:::your-bucket-name/*"
   }
   ```

3. Check bucket policy allows your IAM user

## Azure DevOps Issues

### Personal Access Token (PAT) expired

**Error**: `TF400813: The user 'X' is not authorized to access this resource`

**Solution**:
1. Generate new PAT in Azure DevOps:
   - User Settings → Personal Access Tokens
   - Create new token with Work Items: Read & Write
2. Update environment variable:
   ```bash
   AZURE_DEVOPS_TOKEN=your-new-token
   ```

### Work item creation fails

**Error**: `Failed to create work item: The field 'System.Title' cannot be empty`

**Solutions**:
1. Verify project name is correct:
   ```bash
   echo $AZURE_DEVOPS_PROJECT
   ```

2. Check organization URL format:
   ```bash
   # CORRECT
   AZURE_DEVOPS_ORG_URL=https://dev.azure.com/your-org
   
   # WRONG
   AZURE_DEVOPS_ORG_URL=https://your-org.visualstudio.com
   ```

3. Ensure PAT has correct permissions:
   - Work Items: Read & Write

### Work item type 'User Story' not found

**Error**: `VS402371: The work item type 'User Story' does not exist`

**Solution**:
Work item types vary by process template. Check your project's process:
1. Azure DevOps → Project Settings → Overview → Process
2. Common alternatives:
   - Agile/Scrum: "User Story" ✓
   - Basic: "Issue"
   - CMMI: "Requirement"

Modify `src/services/azureDevOpsService.js`:
```javascript
// Change from:
'User Story'

// To your process type:
'Issue'  // or 'Requirement'
```

## Runtime Errors

### Log file not found

**Error**: `Failed to read log file: ENOENT: no such file or directory`

**Solutions**:
1. Use absolute path:
   ```bash
   node src/index.js --log-file /full/path/to/build.log
   ```

2. Verify file exists:
   ```bash
   ls -la /path/to/build.log
   ```

### Out of memory

**Error**: `JavaScript heap out of memory`

**Solution**:
Increase Node.js memory limit:
```bash
node --max-old-space-size=4096 src/index.js --log-file build.log
```

Or truncate large log files before processing:
```bash
# Keep first and last 1000 lines
(head -n 500 build.log; echo "... [truncated] ..."; tail -n 500 build.log) > build-truncated.log
node src/index.js --log-file build-truncated.log
```

### JSON parse error

**Error**: `Unexpected token in JSON at position X`

**Solution**:
This usually indicates an AWS response issue. Enable debug logging:
```javascript
// In bedrockService.js, add:
console.log('Bedrock response:', JSON.stringify(response, null, 2));
```

## Log Analysis Issues

### Analysis is too generic

**Problem**: Bedrock returns vague recommendations

**Solutions**:
1. Ensure log contains enough context (check truncation)
2. Modify prompt in `src/services/bedrockService.js` to be more specific
3. Try a different Bedrock model:
   ```bash
   AWS_BEDROCK_MODEL_ID=anthropic.claude-3-opus-20240229-v1:0
   ```

### Analysis misses actual error

**Problem**: AI focuses on wrong part of log

**Solution**:
The truncation strategy keeps first 200 and last 800 lines. If error is in the middle:
1. Manually extract relevant section
2. Adjust truncation in `src/utils/helpers.js`:
   ```javascript
   // Modify truncateLog function
   const firstLines = lines.slice(0, 100);  // Less context
   const lastLines = lines.slice(-900);     // More errors
   ```

### Token limit exceeded

**Error**: `ValidationException: Input is too long for requested model`

**Solution**:
Reduce log size in `src/utils/helpers.js`:
```javascript
// Change from 1000 to 500 lines
function truncateLog(logContent, maxLines = 500) {
  // ...
  const firstLines = lines.slice(0, 100);
  const lastLines = lines.slice(-400);
}
```

## Performance Issues

### Processing takes too long

**Problem**: Analysis takes 5+ minutes

**Causes**:
1. Large log file (truncation helps)
2. Slow network to AWS
3. Bedrock throttling

**Solutions**:
```bash
# Skip S3 upload to save time
node src/index.js --log-file build.log --skip-s3-upload

# Use faster model (if available)
AWS_BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
```

### Pipeline timeout

**Problem**: Azure pipeline times out waiting for Build-Fixer

**Solution**:
Run Build-Fixer asynchronously in pipeline:
```yaml
- script: |
    node src/index.js ... &
  displayName: 'Analyze Build Failure (async)'
```

## Debug Mode

Enable verbose logging for troubleshooting:

```javascript
// Add to src/index.js
process.env.DEBUG = 'true';

// Add to each service
if (process.env.DEBUG) {
  console.log('Debug info:', ...);
}
```

## Getting Help

If you can't resolve the issue:

1. **Check logs**: Enable verbose logging
2. **Search issues**: Check GitHub issues for similar problems
3. **Create issue**: Include:
   - Error message
   - Environment (Node.js version, OS)
   - Configuration (sanitized, no secrets)
   - Steps to reproduce
   - Relevant logs

## Common Command Variations

### Minimal test (skip S3)
```bash
node src/index.js \
  --log-file ./examples/sample-build-log.txt \
  --build-id test-123 \
  --skip-s3-upload
```

### With debugging
```bash
DEBUG=true node src/index.js \
  --log-file build.log \
  --build-id 12345
```

### Using environment file
```bash
# Load from custom .env file
node -r dotenv/config src/index.js --log-file build.log dotenv_config_path=/path/to/.env
```

## FAQ

**Q: Can I use this without AWS?**
A: Not currently. The AI analysis requires AWS Bedrock. You could modify the code to use other AI services.

**Q: Can I use this without S3?**
A: Yes! Use `--skip-s3-upload` flag.

**Q: Does this work with GitHub Actions?**
A: Not yet, but it's on the roadmap. Currently only supports Azure DevOps.

**Q: How much does this cost?**
A: Costs depend on:
- Bedrock: ~$0.003-0.015 per request (Claude pricing)
- S3: ~$0.001 per log file
- Azure DevOps: Free (API calls included)

**Q: Can I run this locally for testing?**
A: Yes! Use the sample log file:
```bash
cp .env.example .env
# Edit .env with your credentials
node src/index.js --log-file examples/sample-build-log.txt --build-id test --skip-s3-upload
```

---

Still having issues? Open an issue on GitHub with details!
