# ADR-001: Use Synchronous Pipeline Integration

**Status**: Accepted  
**Date**: 2024-01-15  
**Deciders**: Architecture Team  

## Context

Build-Fixer needs to integrate with Azure DevOps pipelines to analyze build failures and create actionable work items. We evaluated multiple integration patterns:

1. Synchronous execution as a pipeline task
2. Asynchronous queue-based processing
3. Webhook/event-driven architecture
4. Scheduled batch processing

The decision needs to balance:
- Time to value (how quickly teams get feedback)
- Implementation complexity
- Infrastructure requirements
- Pipeline performance impact
- Scalability needs

## Decision

We will implement **Approach 1: Synchronous Pipeline Integration** as the primary and recommended integration pattern.

Build-Fixer will run as a pipeline task that executes immediately after a build failure is detected. The task will:
- Read the build log
- Upload to S3 (optional)
- Analyze with Amazon Bedrock
- Create Azure DevOps work item
- Complete before pipeline finishes

## Consequences

### Positive

- **Immediate Value**: Teams get instant feedback in the pipeline logs
- **Simple Implementation**: No additional infrastructure (queues, webhooks, servers)
- **Easy Debugging**: All logs in one place within the pipeline
- **Low Learning Curve**: Familiar pipeline task pattern
- **Quick Adoption**: Can be added to existing pipelines with minimal changes
- **Clear Causality**: Direct link between failure and analysis
- **No External Dependencies**: Doesn't require additional services to be running

### Negative

- **Pipeline Duration**: Adds 1-2 minutes to failed pipeline execution time
- **Blocking**: Pipeline waits for analysis to complete
- **Limited Scalability**: Processes one failure at a time per pipeline
- **Resource Usage**: Consumes pipeline agent time during analysis
- **Single Point of Failure**: If Build-Fixer fails, it affects pipeline completion

### Neutral

- **Cost Impact**: Uses existing pipeline agent minutes (no additional compute cost)
- **Retry Logic**: Failures can be retried as part of pipeline retry
- **Credentials Management**: Uses same secret management as other pipeline tasks

## Alternatives Considered

### Asynchronous Queue-Based (Approach 2)
**Pros**: Non-blocking, scalable, resilient  
**Cons**: More complex infrastructure, delayed feedback, additional costs  
**Why Not Chosen**: Over-engineered for initial use case, adds operational overhead

### Webhook/Event-Driven (Approach 3)
**Pros**: Fully decoupled, serverless-friendly, multi-pipeline support  
**Cons**: Requires hosting infrastructure, network dependencies, cold start issues  
**Why Not Chosen**: Too complex for MVP, introduces hosting requirements

### Scheduled Batch Processing (Approach 4)
**Pros**: Simple, no pipeline changes, low overhead  
**Cons**: Delayed feedback (up to schedule interval), less immediate value  
**Why Not Chosen**: Defeats the purpose of immediate actionable insights

## Migration Path

While synchronous integration is our primary recommendation, the architecture is designed to support migration to other patterns:

1. **Phase 1 (Current)**: Synchronous pipeline integration
2. **Phase 2 (If needed)**: Add optional async mode for high-volume scenarios
3. **Phase 3 (If needed)**: Support hybrid approach with configurable processing modes

The codebase structure (service-oriented architecture) makes this migration path feasible without major refactoring.

## Success Criteria

This decision will be considered successful if:
- Adoption rate is >70% of teams that try it
- Analysis completes in <2 minutes on average
- Failure rate is <5%
- Teams report positive feedback on immediate insights
- No significant pipeline performance complaints

## Review

This decision should be reviewed after:
- 6 months of production use
- Processing >1000 build failures
- Receiving feedback from >10 teams
- If performance or scalability issues emerge

## References

- [ARCHITECTURE.md](../ARCHITECTURE.md) - Detailed comparison of all approaches
- Azure DevOps Pipeline Tasks Documentation
- Industry best practices for CI/CD failure handling
