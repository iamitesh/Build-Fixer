# Frequently Asked Questions (FAQ)

## General Questions

### Q: Why should I use Build-Fixer instead of manually analyzing build failures?

**A**: Build-Fixer provides several advantages:
- **Speed**: AI analysis takes 5-15 seconds vs. hours of manual investigation
- **Consistency**: Every failure gets the same thorough analysis
- **Documentation**: Automatic work item creation creates a searchable history
- **Cost**: AI analysis costs $0.01-0.05 vs. $100-200 in developer time
- **24/7 Availability**: Works automatically even outside business hours

### Q: How much does Build-Fixer cost to run?

**A**: Typical costs per build failure analysis:
- S3 storage: ~$0.001 (for a 10KB log file)
- Bedrock API: ~$0.01-0.05 (depends on log size and model)
- Azure DevOps API: Free (within standard limits)
- **Total: ~$0.01-0.05 per analysis**

For 100 build failures per month, expect ~$1-5 in AWS costs.

### Q: What types of build failures can Build-Fixer analyze?

**A**: Build-Fixer can analyze any type of build failure including:
- Compilation errors
- Test failures
- Dependency issues
- Configuration problems
- Infrastructure failures
- Deployment errors

The AI model (Claude 3) is trained on a wide variety of technical content and can understand most build-related issues.

### Q: Is my build log data secure?

**A**: Yes, your data is secure:
- Logs are stored in your own S3 bucket with your access controls
- Bedrock processes data in AWS's secure environment (no data retention for inference)
- Azure DevOps work items are in your organization's instance
- No data is shared with third parties
- You control all access credentials

### Q: Can I use Build-Fixer with other CI/CD platforms besides Azure DevOps?

**A**: Currently, Build-Fixer is designed for Azure DevOps pipelines. However, the architecture is extensible. You can:
- Use the analysis features with any platform (S3 + Bedrock)
- Create adapters for GitHub Actions, Jenkins, GitLab CI, etc.
- Contribute new integrations (see [CONTRIBUTING.md](CONTRIBUTING.md))

## Setup and Configuration

### Q: Do I need an AWS account?

**A**: Yes, you need:
- An AWS account with Bedrock access
- S3 bucket for log storage
- IAM credentials with appropriate permissions
- Bedrock model access (Claude 3) enabled in your region

### Q: Which AWS regions support Amazon Bedrock?

**A**: As of 2024, Bedrock is available in:
- us-east-1 (US East, N. Virginia)
- us-west-2 (US West, Oregon)
- eu-central-1 (Europe, Frankfurt)
- ap-southeast-1 (Asia Pacific, Singapore)
- ap-northeast-1 (Asia Pacific, Tokyo)

Check the [AWS documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html) for the latest list.

### Q: What permissions does the Azure DevOps PAT need?

**A**: The Personal Access Token needs:
- **Work Items**: Read & Write
- Scope: Project-level access to your target project

That's all! No other permissions are required.

### Q: Can I use IAM roles instead of access keys?

**A**: Yes! If running in an AWS environment (EC2, ECS, Lambda), Build-Fixer can use IAM roles automatically. Simply:
1. Don't set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
2. Ensure your execution environment has an IAM role with appropriate permissions
3. boto3 will automatically use the role credentials

## Usage

### Q: Can I run Build-Fixer locally for testing?

**A**: Yes! 
```bash
# Set environment variables
export AWS_REGION=us-east-1
export S3_BUCKET_NAME=my-bucket
# ... (set other required variables)

# Run with example log
python -m build_fixer.main examples/sample_build_failure.log --verbose
```

### Q: How do I capture the build log in my pipeline?

**A**: Azure Pipelines automatically generates logs. You can:

**Option 1**: Use pipeline variables
```bash
# The log is available via Azure DevOps API
# Or save specific command output to a file
```

**Option 2**: Capture specific command output
```yaml
- script: |
    dotnet build > build.log 2>&1 || true
  displayName: 'Build (capture log)'
```

### Q: Can I customize the work item format?

**A**: Yes! Modify the `_format_description()` method in `azure_devops_manager.py` to change:
- HTML formatting
- Section structure
- Styling
- Additional fields

### Q: Can I analyze multiple build failures at once?

**A**: Currently, Build-Fixer processes one failure at a time. For batch processing:
```bash
for log in logs/*.log; do
    python -m build_fixer.main "$log"
done
```

Future versions may include native batch processing.

## Troubleshooting

### Q: Error: "Access Denied" when uploading to S3

**Solutions**:
1. Verify S3 bucket name is correct
2. Check IAM permissions include `s3:PutObject`
3. Ensure bucket exists and is in the correct region
4. Test with AWS CLI: `aws s3 ls s3://your-bucket`

### Q: Error: "ValidationException" from Bedrock

**Solutions**:
1. Verify Bedrock is available in your region
2. Check model access is enabled (AWS Console → Bedrock → Model access)
3. Ensure IAM permissions include `bedrock:InvokeModel`
4. Wait for model access approval (usually instant)

### Q: Error: "Failed to create work item"

**Solutions**:
1. Verify PAT has not expired
2. Check organization URL format: `https://dev.azure.com/orgname`
3. Ensure project name is exact match (case-sensitive)
4. Verify PAT has "Work Items: Read & Write" permission
5. Test connection manually:
```python
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication

credentials = BasicAuthentication('', 'your-pat')
connection = Connection(base_url='https://dev.azure.com/your-org', creds=credentials)
client = connection.clients.get_work_item_tracking_client()
print("Connection successful!")
```

### Q: Error: "ModuleNotFoundError"

**Solution**:
```bash
pip install -r requirements.txt --upgrade
```

### Q: The AI analysis is not helpful or inaccurate

**Solutions**:
1. Ensure log file contains the actual error output (not just build summary)
2. Try a more powerful model: `BEDROCK_MODEL_ID=anthropic.claude-3-opus-20240229-v1:0`
3. Increase log context (modify truncation in `bedrock_analyzer.py`)
4. Check if the log is in a language the model understands

### Q: Build-Fixer times out in my pipeline

**Solutions**:
1. Increase pipeline timeout settings
2. Use a faster Bedrock model (Haiku instead of Sonnet)
3. Reduce log size before analysis
4. Check network connectivity to AWS/Azure

### Q: I'm getting rate limited

**Solutions**:
- **Bedrock**: Default quotas are generous; request a limit increase if needed
- **Azure DevOps**: PATs have rate limits; consider using service principals for high volume
- **S3**: S3 has very high limits; rate limiting here is unlikely

## Advanced Usage

### Q: Can I use a different AI model?

**A**: Yes! Set the model ID:
```bash
export BEDROCK_MODEL_ID=anthropic.claude-3-opus-20240229-v1:0
```

Available options:
- `anthropic.claude-3-haiku-20240307-v1:0` (fastest)
- `anthropic.claude-3-sonnet-20240229-v1:0` (balanced, default)
- `anthropic.claude-3-opus-20240229-v1:0` (most capable)

### Q: Can I create Bugs instead of User Stories?

**A**: Yes! Set the work item type:
```bash
export WORK_ITEM_TYPE=Bug
```

### Q: How do I add custom tags?

**A**: Set the tags environment variable:
```bash
export WORK_ITEM_TAGS=build-failure,automated,urgent,team-alpha
```

### Q: Can I assign work items to specific people?

**A**: Yes:
```bash
export WORK_ITEM_ASSIGNED_TO=user@example.com
```

### Q: Can I set area and iteration paths?

**A**: Yes:
```bash
export WORK_ITEM_AREA_PATH="MyProject\\DevOps"
export WORK_ITEM_ITERATION_PATH="MyProject\\Sprint 5"
```

### Q: How do I integrate with Slack/Teams notifications?

**A**: Build-Fixer creates work items in Azure DevOps. You can:
1. Set up Azure DevOps notifications to Slack/Teams
2. Configure alerts for work items with specific tags
3. Extend Build-Fixer to send notifications directly (see [CONTRIBUTING.md](CONTRIBUTING.md))

## Cost Optimization

### Q: How can I reduce costs?

**A**: Several strategies:
1. Use Claude Haiku instead of Sonnet: `BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0`
2. Implement S3 lifecycle policies to delete old logs after 30-90 days
3. Only run Build-Fixer for critical build failures (main branch, production)
4. Cache analysis for identical error patterns (future enhancement)

### Q: What are the actual AWS costs?

**A**: Example for 100 failures/month:
- S3 storage: $0.10 (1GB of logs)
- S3 requests: $0.05 (upload/download)
- Bedrock (Haiku): $0.50 (cheapest model)
- Bedrock (Sonnet): $2.00 (default model)
- Bedrock (Opus): $7.50 (most expensive)

**Total: $0.65 - $7.65/month for 100 failures**

## Development and Extension

### Q: Can I extend Build-Fixer for my specific needs?

**A**: Absolutely! Build-Fixer is designed to be extensible:
- Modify prompt templates in `bedrock_analyzer.py`
- Add new storage backends alongside S3
- Create custom work item formatters
- Integrate with other systems
- See [ARCHITECTURE.md](ARCHITECTURE.md) for design details

### Q: How do I contribute?

**A**: See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. We welcome:
- Bug fixes
- New features
- Documentation improvements
- Test coverage
- Integration with other platforms

### Q: Is there a plugin architecture?

**A**: Not currently, but this is a great enhancement idea! Consider contributing this feature.

## Support

### Q: Where can I get help?

**A**: 
1. Check this FAQ
2. Review [SETUP.md](SETUP.md) for setup issues
3. Read [ARCHITECTURE.md](ARCHITECTURE.md) for design details
4. Open an issue on GitHub
5. Check existing GitHub issues for similar problems

### Q: How do I report a bug?

**A**: Open a GitHub issue with:
- Description of the problem
- Steps to reproduce
- Expected vs. actual behavior
- Environment details (OS, Python version, etc.)
- Relevant logs (sanitize sensitive data)

### Q: Can I get commercial support?

**A**: Build-Fixer is an open-source project. For commercial support:
- Consider hiring consultants familiar with the project
- Contribute to the project and become an expert yourself
- Sponsor development of specific features

## Roadmap

### Q: What features are planned?

**A**: Future enhancements may include:
- Support for GitHub Actions, Jenkins, GitLab CI
- Batch processing capabilities
- Advanced analytics and reporting
- Custom ML models for pattern recognition
- Web dashboard for monitoring
- Webhook support for event-driven architecture

See GitHub issues labeled "enhancement" for specific features under consideration.

## Still have questions?

Open an issue on GitHub with the label "question" and we'll add it to this FAQ!
