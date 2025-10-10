# Architectural Decision Records (ADR)

This directory contains Architectural Decision Records (ADRs) for the Build-Fixer project. ADRs document important architectural decisions made during the project lifecycle.

## What is an ADR?

An Architectural Decision Record (ADR) captures a significant architectural decision made along with its context and consequences. It serves as a historical record for why certain decisions were made.

## ADR Format

Each ADR follows this structure:

```
# [ADR Number]: [Title]

**Status**: [Proposed | Accepted | Deprecated | Superseded]
**Date**: YYYY-MM-DD
**Deciders**: [Names]

## Context
What is the issue that we're seeing that is motivating this decision or change?

## Decision
What is the change that we're proposing and/or doing?

## Consequences
What becomes easier or more difficult to do because of this change?

### Positive
- List of benefits

### Negative
- List of drawbacks or trade-offs

### Neutral
- Other impacts

## Alternatives Considered
What other options were evaluated?

## References
Links to relevant documentation, discussions, or resources
```

## Index of ADRs

1. [ADR-001: Use Synchronous Pipeline Integration](./001-synchronous-pipeline-integration.md) - **Accepted**
2. [ADR-002: AWS Bedrock for AI Analysis](./002-aws-bedrock-ai-analysis.md) - **Accepted**
3. [ADR-003: Service-Oriented Architecture](./003-service-oriented-architecture.md) - **Accepted**
4. [ADR-004: Environment-Based Configuration](./004-environment-configuration.md) - **Accepted**
5. [ADR-005: Multi-Cloud Strategy](./005-multi-cloud-strategy.md) - **Proposed**
6. [ADR-006: Security and Compliance Framework](./006-security-compliance.md) - **Proposed**
7. [ADR-007: Observability and Monitoring](./007-observability-monitoring.md) - **Proposed**

## Creating a New ADR

1. Copy the template from `adr-template.md`
2. Number it sequentially (e.g., `008-your-decision.md`)
3. Fill in all sections
4. Submit for review via pull request
5. Update this index after approval

## Best Practices

- Write ADRs for significant decisions that:
  - Affect structure, non-functional characteristics, dependencies, interfaces, or construction techniques
  - Impact multiple components or systems
  - Are difficult or expensive to reverse
  - Have long-term implications

- Keep ADRs:
  - Concise but complete
  - Focused on one decision
  - Written in present tense
  - Objective and factual

## Versioning

ADRs are immutable once accepted. If a decision needs to change:
1. Create a new ADR that supersedes the old one
2. Update the old ADR's status to "Superseded by ADR-XXX"
3. Reference the old ADR in the new one
