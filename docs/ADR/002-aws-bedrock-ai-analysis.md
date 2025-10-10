# ADR-002: AWS Bedrock for AI Analysis

**Status**: Accepted  
**Date**: 2024-01-15  
**Deciders**: Architecture Team, AI/ML Team  

## Context

Build-Fixer requires AI-powered analysis of build logs to identify root causes and recommend fixes. The solution needs to:
- Understand complex error patterns in build logs
- Generate actionable recommendations
- Handle various programming languages and frameworks
- Provide consistent, high-quality analysis
- Be cost-effective at scale
- Maintain data privacy and security

We evaluated several AI/ML options:
1. Amazon Bedrock (Claude models)
2. Azure OpenAI Service
3. OpenAI API directly
4. Custom ML model (self-trained)
5. Google Cloud Vertex AI

## Decision

We will use **Amazon Bedrock with Claude 3 Sonnet** as our primary AI analysis engine.

Key implementation details:
- Model: `anthropic.claude-3-sonnet-20240229-v1:0`
- Fallback: `anthropic.claude-3-haiku` for cost optimization (future)
- SDK: AWS SDK for JavaScript v3 (`@aws-sdk/client-bedrock-runtime`)
- Region: Configurable, default `us-east-1`

## Consequences

### Positive

- **High Quality**: Claude 3 Sonnet provides excellent reasoning for technical problems
- **Context Window**: 200K tokens allows analyzing large build logs without truncation
- **Data Privacy**: Bedrock doesn't use customer data for training
- **Enterprise Ready**: AWS compliance certifications (SOC 2, HIPAA, GDPR)
- **Cost Effective**: Pay-per-use model, ~$0.003-0.015 per analysis
- **Low Latency**: Typically <5 seconds for analysis
- **AWS Integration**: Seamless integration with S3, IAM, CloudWatch
- **Vendor Support**: Enterprise support available through AWS
- **Multi-Region**: Can deploy in multiple AWS regions for redundancy

### Negative

- **AWS Dependency**: Requires AWS account and Bedrock access
- **Model Access**: Need to request access to Claude models (usually instant)
- **Regional Availability**: Bedrock not available in all AWS regions
- **Vendor Lock-in**: Migration to other AI providers requires code changes
- **Cost Variability**: Costs can increase with log size and frequency
- **Cold Start**: First request may have slight latency
- **Limited Customization**: Cannot fine-tune Bedrock models

### Neutral

- **API Rate Limits**: Need to implement retry logic for high-volume scenarios
- **Token Limits**: Need to truncate very large logs (handled in current implementation)
- **Model Updates**: AWS manages model versions and updates

## Alternatives Considered

### Azure OpenAI Service
**Pros**: Native Azure integration, good for Azure-only shops  
**Cons**: More expensive, requires separate Azure subscription, OpenAI models not as strong for technical analysis  
**Why Not Chosen**: Higher cost, less suitable for multi-cloud strategy

### OpenAI API (Direct)
**Pros**: Latest models, simple API, well-documented  
**Cons**: Data privacy concerns, no enterprise SLA, rate limits, training data usage  
**Why Not Chosen**: Data privacy risks for enterprise customers, lacks compliance certifications

### Custom ML Model
**Pros**: Full control, no external dependencies, customizable  
**Cons**: Requires ML expertise, training data, infrastructure, maintenance  
**Why Not Chosen**: Too expensive and time-consuming to develop and maintain

### Google Cloud Vertex AI
**Pros**: Good integration with GCP, access to Gemini models  
**Cons**: Another cloud provider, less mature than Bedrock, limited model options  
**Why Not Chosen**: Adds third cloud provider, less comprehensive model selection

## Technical Implementation

### Prompt Engineering Strategy
```
System: You are a DevOps expert analyzing build failures
Task: Analyze the following build log and provide:
1. Root Cause Analysis (2-3 sentences)
2. Recommended Fixes (3-5 actionable steps)
Format: Use markdown with clear sections
```

### Error Handling
- Retry with exponential backoff for throttling
- Fallback to simpler models if primary fails
- Graceful degradation if AI unavailable

### Cost Optimization
- Intelligent log truncation (keep first 200 + last 800 lines)
- Cache common error patterns (future)
- Use smaller models (Haiku) for simple failures (future)

## Migration and Extension Strategy

The architecture supports future enhancements:

1. **Multi-Model Support**: Abstract AI provider behind interface
2. **Model Selection**: Choose model based on log complexity
3. **A/B Testing**: Compare different models for quality
4. **Custom Fine-tuning**: If needed, migrate to fine-tuned models

Example future architecture:
```javascript
interface AIProvider {
  analyzeLog(logContent: string): Promise<Analysis>
}

class BedrockProvider implements AIProvider { ... }
class AzureOpenAIProvider implements AIProvider { ... }
class CustomModelProvider implements AIProvider { ... }
```

## Cost Analysis

Based on typical usage:

| Scenario | Logs/Month | Cost/Month | Notes |
|----------|------------|------------|-------|
| Small Team | 100 | $1-2 | Occasional failures |
| Medium Team | 500 | $5-10 | Regular CI/CD |
| Large Team | 2000 | $20-30 | High-frequency builds |
| Enterprise | 10000+ | $100-150 | Multi-team, 24/7 pipelines |

Compare to manual analysis cost:
- Manual: 30 min × $50/hr = $25 per failure
- Automated: $0.01 per failure
- **ROI**: ~2500x cost reduction

## Security and Compliance

- **Data Residency**: Logs processed in specified AWS region
- **Encryption**: In-transit (TLS 1.2+) and at-rest encryption
- **Access Control**: IAM policies for least-privilege access
- **Audit Trail**: CloudTrail logs all Bedrock API calls
- **Compliance**: SOC 2, ISO 27001, HIPAA, GDPR compliant

## Success Metrics

Track these metrics to validate the decision:
- **Quality**: >80% of recommendations rated helpful by developers
- **Performance**: <10 seconds average analysis time
- **Cost**: <$0.02 per build failure analyzed
- **Availability**: >99.9% success rate
- **Adoption**: >70% of teams using AI analysis

## Review Criteria

Re-evaluate this decision if:
- Analysis quality drops below 70% helpful rating
- Costs exceed $0.05 per analysis
- Better models become available (e.g., Claude 4)
- Significant compliance or privacy concerns emerge
- AWS Bedrock becomes unavailable or deprecated

## References

- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Claude 3 Model Card](https://www.anthropic.com/claude)
- [AWS Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/)
- [Data Privacy Whitepaper](https://aws.amazon.com/bedrock/security-compliance/)
- Internal Cost Analysis (Q1 2024)
