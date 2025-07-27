# AWS Native AI Agent with Bedrock Agents, Guardrails, and TypeScript CDK

This repository provides a comprehensive example of building an AWS-native AI agent using Amazon Bedrock Agents with proper prompt management, guardrails, knowledge bases, and action groups, all deployed using AWS CDK with TypeScript.

## Architecture Overview

This solution implements a production-ready AI agent that includes:

- **Amazon Bedrock Agent** with advanced prompt templates
- **Bedrock Guardrails** for responsible AI implementation
- **Knowledge Base** with OpenSearch Serverless for RAG capabilities
- **Action Groups** with Lambda functions for external integrations
- **Comprehensive IAM roles and policies** following least privilege principles
- **Monitoring and logging** for observability

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User/Client   │───▶│  Bedrock Agent   │───▶│  Foundation     │
└─────────────────┘    └──────────────────┘    │  Model (Claude) │
                                │               └─────────────────┘
                                │
                        ┌───────▼────────┐
                        │  Guardrails    │
                        └───────┬────────┘
                                │
                    ┌───────────▼─────────────┐
                    │                         │
            ┌───────▼────────┐    ┌──────────▼─────────┐
            │ Knowledge Base │    │   Action Groups    │
            │ (OpenSearch)   │    │   (Lambda Fns)     │
            └────────────────┘    └────────────────────┘
```

## Features

### 🤖 **Bedrock Agent**
- Claude 3 Haiku foundation model
- Advanced prompt templates for precise control
- Session management with configurable TTL
- Multi-turn conversation support

### 🛡️ **Guardrails**
- Content filtering (hate, violence, misconduct, etc.)
- PII detection and protection
- Custom word filtering
- Prompt injection protection

### 🧠 **Knowledge Base**
- OpenSearch Serverless vector store
- S3 data source with automatic ingestion
- Embeddings using Amazon Titan
- Configurable chunking strategy

### ⚡ **Action Groups**
- Lambda-backed business logic
- OpenAPI schema definitions
- Weather information service example
- Secure cross-service communication

### 📊 **Observability**
- CloudWatch logs for all components
- Structured logging in Lambda functions
- Agent invocation tracing
- Performance monitoring

## Prerequisites

- AWS CLI configured with appropriate permissions
- Node.js 18+ and npm
- AWS CDK v2 installed (`npm install -g aws-cdk`)
- Docker (for Lambda bundling)

## Quick Start

1. **Clone and setup**
   ```bash
   git clone <repository>
   cd bedrock-agent-example
   npm install
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your preferences
   ```

3. **Bootstrap CDK (if not done before)**
   ```bash
   cdk bootstrap
   ```

4. **Deploy the infrastructure**
   ```bash
   npm run deploy
   ```

5. **Upload sample documents**
   ```bash
   aws s3 cp sample-docs/ s3://your-knowledge-base-bucket/documents/ --recursive
   ```

6. **Test the agent**
   ```bash
   npm run test-agent
   ```

## Project Structure

```
bedrock-agent-example/
├── lib/
│   ├── bedrock-agent-stack.ts         # Main CDK stack
│   ├── constructs/
│   │   ├── bedrock-agent.ts           # Agent construct
│   │   ├── bedrock-guardrails.ts      # Guardrails construct
│   │   ├── knowledge-base.ts          # Knowledge base construct
│   │   └── action-groups.ts           # Action groups construct
│   └── lambda/
│       ├── weather-action/            # Weather service action
│       └── knowledge-sync/            # KB sync automation
├── assets/
│   ├── openapi-schemas/               # API schemas for actions
│   └── sample-documents/              # Sample knowledge base docs
├── test/
│   └── bedrock-agent.test.ts         # Unit tests
└── scripts/
    └── test-agent.js                 # Agent testing script
```

## Configuration

### Environment Variables

```env
# Required
AWS_REGION=us-east-1
AGENT_NAME=my-ai-agent
FOUNDATION_MODEL=anthropic.claude-3-haiku-20240307-v1:0

# Optional
KNOWLEDGE_BASE_NAME=my-knowledge-base
GUARDRAIL_NAME=my-guardrail
IDLE_SESSION_TTL=3600
```

### Agent Instructions

The agent is configured with comprehensive instructions that can be customized in `lib/constructs/bedrock-agent.ts`:

```typescript
const agentInstruction = `
You are an intelligent AI assistant that helps users with various tasks.

Capabilities:
1. Answer questions using your knowledge base
2. Get current weather information for any location
3. Provide helpful and accurate information

Guidelines:
- Always be helpful, harmless, and honest
- Use the knowledge base for domain-specific questions
- Use action groups for external data like weather
- If unsure, acknowledge limitations and suggest alternatives
`;
```

## Usage Examples

### Basic Conversation
```typescript
import { BedrockAgentRuntimeClient, InvokeAgentCommand } from "@aws-sdk/client-bedrock-agent-runtime";

const client = new BedrockAgentRuntimeClient({ region: "us-east-1" });

const response = await client.send(new InvokeAgentCommand({
  agentId: "AGENT_ID",
  agentAliasId: "ALIAS_ID",
  sessionId: "unique-session-id",
  inputText: "What's the weather like in San Francisco?"
}));
```

### Using the Knowledge Base
```
User: "What are the best practices for machine learning deployment?"
Agent: [Searches knowledge base and provides relevant information from uploaded documents]
```

### Action Group Integration
```
User: "What's the current weather in Tokyo?"
Agent: [Calls weather action group and returns real-time weather data]
```

## Advanced Features

### Custom Prompt Templates

The agent supports advanced prompt templates for fine-grained control:

```typescript
const promptOverrideConfiguration = {
  promptConfigurations: [
    {
      promptType: "PRE_PROCESSING",
      promptCreationMode: "OVERRIDDEN",
      promptState: "ENABLED",
      basePromptTemplate: customPreProcessingPrompt,
      inferenceConfiguration: {
        temperature: 0.1,
        topP: 0.9,
        topK: 250,
        maximumLength: 2048,
      }
    }
  ]
};
```

### Guardrails Configuration

```typescript
const guardrailConfig = {
  contentPolicyConfig: {
    filtersConfig: [
      {
        type: "SEXUAL",
        inputStrength: "HIGH",
        outputStrength: "HIGH"
      },
      // ... more filters
    ]
  },
  sensitiveInformationPolicyConfig: {
    piiEntitiesConfig: [
      {
        type: "EMAIL",
        action: "BLOCK"
      }
    ]
  }
};
```

### Knowledge Base Chunking

```typescript
const vectorIngestionConfiguration = {
  chunkingConfiguration: {
    chunkingStrategy: "FIXED_SIZE",
    fixedSizeChunkingConfiguration: {
      maxTokens: 300,
      overlapPercentage: 20
    }
  }
};
```

## Monitoring and Debugging

### CloudWatch Logs
- Agent invocations: `/aws/bedrock/agents/{agentId}`
- Lambda functions: `/aws/lambda/{functionName}`
- Knowledge base: `/aws/bedrock/knowledgebases/{kbId}`

### Agent Tracing
Enable detailed tracing to see the agent's decision-making process:

```typescript
const invokeCommand = new InvokeAgentCommand({
  agentId,
  agentAliasId,
  sessionId,
  inputText,
  enableTrace: true
});
```

## Cost Optimization

### Strategies Implemented
1. **Efficient Chunking**: Optimized chunk size and overlap
2. **Session Management**: Configurable TTL to balance UX and cost
3. **Resource Cleanup**: Automatic cleanup of temporary resources
4. **Selective Model Use**: Cost-effective model selection

### Cost Monitoring
```bash
# Get cost breakdown for Bedrock services
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE
```

## Security Best Practices

### IAM Roles
- **Agent Role**: Minimal permissions for Bedrock operations
- **Lambda Roles**: Function-specific permissions only
- **Knowledge Base Role**: Read-only access to S3 and OpenSearch

### Data Protection
- All data encrypted in transit and at rest
- VPC deployment options for enhanced isolation
- Secure API key management for external services

### Guardrails
- Comprehensive content filtering
- PII detection and redaction
- Custom policy enforcement

## Troubleshooting

### Common Issues

1. **Agent Creation Fails**
   ```bash
   # Check CloudFormation events
   aws cloudformation describe-stack-events --stack-name BedrockAgentStack
   ```

2. **Knowledge Base Sync Issues**
   ```bash
   # Check sync job status
   aws bedrock-agent get-ingestion-job \
     --knowledge-base-id KB_ID \
     --data-source-id DS_ID \
     --ingestion-job-id JOB_ID
   ```

3. **Lambda Function Errors**
   ```bash
   # Check function logs
   aws logs tail /aws/lambda/weather-action-function
   ```

### Debug Mode
Set `DEBUG=true` in your environment to enable verbose logging.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Resources

- [Amazon Bedrock Agents Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/)
- [Best Practices Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-best-practices.html)

## Support

For issues and questions:
- Check the [troubleshooting guide](#troubleshooting)
- Search existing [GitHub issues](../../issues)
- Create a new issue with detailed information

---

**Note**: This is a demonstration project. For production use, ensure you review and adjust security settings, cost controls, and compliance requirements according to your organization's needs.