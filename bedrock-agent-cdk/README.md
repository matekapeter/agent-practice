# AWS Native AI Agent with Bedrock Agents, Guardrails, and TypeScript CDK

This repository provides a comprehensive example of building an AWS-native AI agent using Amazon Bedrock Agents with proper prompt management, guardrails, knowledge bases, and action groups, all deployed using AWS CDK with TypeScript.

## 🏗️ Architecture Overview

This solution implements a production-ready AI agent that includes:

- **Amazon Bedrock Agent** with advanced prompt templates and orchestration
- **Bedrock Guardrails** for responsible AI implementation with content filtering, PII protection, and contextual grounding
- **Knowledge Base** with OpenSearch Serverless for RAG (Retrieval Augmented Generation) capabilities
- **Action Groups** with Lambda functions for external integrations and business logic
- **API Gateway** with Cognito authentication for secure external access
- **Comprehensive IAM roles and policies** following least privilege principles
- **Monitoring and logging** for observability

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway                              │
│                    (with Cognito Auth)                         │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Lambda Function                               │
│                 (Agent Invoker)                                │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Bedrock Agent                                │
│                 (with Guardrails)                              │
├─────────────────────┬───────────────────┬───────────────────────┤
│  Advanced Prompts   │  Action Groups    │   Knowledge Base      │
│  • Pre-processing   │  • Lambda Funcs   │  • OpenSearch         │
│  • Orchestration    │  • Business Logic │  • Vector Storage     │
│  • KB Response Gen  │  • External APIs  │  • RAG Capabilities   │
│  • Post-processing  │                   │                       │
└─────────────────────┴───────────────────┴───────────────────────┘
```

## 🚀 Features

### Advanced AI Capabilities
- **Intelligent Orchestration**: Multi-step reasoning with custom prompt templates
- **Knowledge Retrieval**: Vector-based semantic search with contextual grounding
- **Action Execution**: Business logic integration through Lambda functions
- **Memory Management**: Session context and conversation history
- **Streaming Support**: Real-time response streaming capabilities

### Security & Compliance
- **Comprehensive Guardrails**: Content filtering, PII detection, topic restrictions
- **Authentication**: Cognito User Pool integration
- **Authorization**: Fine-grained IAM permissions
- **Data Protection**: Encryption at rest and in transit
- **Audit Logging**: Complete request/response tracking

### Enterprise Ready
- **Scalable Architecture**: Serverless components that auto-scale
- **Multi-Environment**: Easy deployment across environments
- **Monitoring**: CloudWatch integration for observability
- **Cost Optimization**: Pay-per-use pricing model

## 📋 Prerequisites

Before you begin, ensure you have:

1. **AWS Account** with appropriate permissions
2. **AWS CLI** configured with your credentials
3. **Node.js** (version 18.x or later)
4. **npm** or **yarn** package manager
5. **AWS CDK** (version 2.100.0 or later)
6. **TypeScript** knowledge for customization

### Required AWS Services Access
- Amazon Bedrock (with model access enabled)
- AWS Lambda
- Amazon API Gateway
- Amazon Cognito
- Amazon OpenSearch Serverless
- Amazon S3
- AWS IAM
- AWS CloudWatch

## 🛠️ Installation & Deployment

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd bedrock-agent-cdk

# Install dependencies
npm install

# Bootstrap CDK (if not done previously)
cdk bootstrap
```

### 2. Enable Amazon Bedrock Models

Before deployment, ensure you have enabled access to the required foundation models in the AWS Bedrock console:

1. Go to the AWS Bedrock console
2. Navigate to "Model access" in the left sidebar
3. Request access to the following models:
   - Anthropic Claude 3.5 Sonnet
   - Anthropic Claude 3 Haiku
   - Amazon Nova Pro
   - Amazon Nova Lite
   - Amazon Titan Embeddings v2

### 3. Prepare Assets

Create the required asset directories and files:

```bash
# Create directories
mkdir -p assets/sample-documents
mkdir -p assets/action-group-schemas

# The sample files are already included in the repository
# Add your own documents to assets/sample-documents/
# Modify action group schemas in assets/action-group-schemas/
```

### 4. Deploy the Stacks

Deploy all stacks in the correct order:

```bash
# Deploy all stacks
npm run deploy

# Or deploy individual stacks
cdk deploy BedrockGuardrailsStack
cdk deploy BedrockKnowledgeBaseStack
cdk deploy LambdaFunctionStack
cdk deploy BedrockAgentStack
cdk deploy ApiGatewayStack
```

### 5. Post-Deployment Configuration

After deployment, you'll need to:

1. **Create a Cognito User** for API access:
```bash
aws cognito-idp admin-create-user \
  --user-pool-id <YOUR_USER_POOL_ID> \
  --username testuser \
  --temporary-password TempPass123! \
  --message-action SUPPRESS
```

2. **Trigger Knowledge Base Ingestion** (if needed):
```bash
aws bedrock-agent start-ingestion-job \
  --knowledge-base-id <YOUR_KB_ID> \
  --data-source-id <YOUR_DATA_SOURCE_ID>
```

## 📚 Usage Examples

### 1. API Gateway Integration

#### Authentication
First, authenticate with Cognito to get access tokens:

```bash
# Use AWS CLI or Cognito SDK to authenticate
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id <YOUR_CLIENT_ID> \
  --auth-parameters USERNAME=testuser,PASSWORD=<PASSWORD>
```

#### Invoke the Agent

```bash
curl -X POST https://<API_ID>.execute-api.<REGION>.amazonaws.com/prod/agent/invoke \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "inputText": "What are our company vacation policies?",
    "sessionId": "unique-session-id",
    "enableTrace": true
  }'
```

### 2. Direct Agent Invocation

```python
import boto3
import json

# Initialize the client
bedrock_agent = boto3.client('bedrock-agent-runtime')

# Invoke the agent
response = bedrock_agent.invoke_agent(
    agentId='<AGENT_ID>',
    agentAliasId='<AGENT_ALIAS_ID>',
    sessionId='unique-session-123',
    inputText='How do I schedule an appointment?'
)

# Process the response
result = ""
for event in response['completion']:
    if 'chunk' in event:
        result += event['chunk']['bytes'].decode('utf-8')

print(result)
```

### 3. Example Conversations

#### Knowledge Base Query
```
User: "What are the company's remote work policies?"
Agent: "Based on the company handbook, here are our remote work policies:
- Remote work options are available for eligible positions with manager approval
- Standard business hours are Monday through Friday, 9:00 AM to 5:00 PM
- Flexible work arrangements can be discussed with your manager
- Regular attendance expectations still apply..."
```

#### Action Group Execution
```
User: "Can you help me search for wireless headphones under $200?"
Agent: "I'll search for wireless headphones under $200 for you.

*[Executes search_products function]*

I found 2 wireless headphones under $200:
1. Wireless Headphones - $199.99 (4.5/5 stars, In Stock)
2. Budget Wireless Earbuds - $149.99 (4.2/5 stars, In Stock)

Would you like more details about either of these products?"
```

## 🔧 Customization

### Adding New Action Groups

1. **Update Lambda Function**: Add new function handlers in `lib/lambda-function-stack.ts`
2. **Create OpenAPI Schema**: Define the API schema in `assets/action-group-schemas/`
3. **Update Agent Configuration**: Add the new action group in `lib/bedrock-agent-stack.ts`

### Modifying Guardrails

Update the guardrail configuration in `lib/bedrock-guardrails-stack.ts`:

```typescript
// Add new denied topics
topicPolicyConfig: {
  topicsConfig: [
    {
      name: 'NewDeniedTopic',
      definition: 'Description of what to block',
      examples: ['Example phrases to block'],
      type: 'DENY'
    }
  ]
}
```

### Customizing Prompts

Modify the prompt templates in `lib/bedrock-agent-stack.ts`:

```typescript
promptOverrideConfiguration: {
  promptConfigurations: [
    {
      promptType: 'ORCHESTRATION',
      promptCreationMode: 'OVERRIDDEN',
      basePromptTemplate: 'Your custom prompt template...'
    }
  ]
}
```

### Adding Knowledge Base Documents

1. Add documents to `assets/sample-documents/`
2. Redeploy the knowledge base stack
3. Trigger a new ingestion job

## 🔍 Monitoring & Troubleshooting

### CloudWatch Logs

Monitor the following log groups:
- `/aws/lambda/bedrock-agent-action-group` - Action group execution logs
- `/aws/lambda/bedrock-agent-invoker` - API Gateway invocation logs
- `/aws/apigateway/bedrock-agent-api` - API Gateway access logs

### Common Issues

#### Agent Not Responding
1. Check if the agent is properly prepared
2. Verify IAM permissions
3. Review CloudWatch logs for errors

#### Guardrails Blocking Legitimate Requests
1. Review guardrail trace information
2. Adjust threshold settings
3. Update denied topics or word filters

#### Knowledge Base Not Finding Relevant Documents
1. Check document ingestion status
2. Review chunking strategy
3. Verify vector index configuration

### Testing

```bash
# Run CDK tests
npm test

# Validate CloudFormation templates
cdk synth

# Check for security issues
npm audit
```

## 🏢 Production Considerations

### Security Hardening
- Enable AWS CloudTrail for audit logging
- Implement VPC endpoints for private communication
- Use AWS Secrets Manager for sensitive configuration
- Enable AWS Config for compliance monitoring

### Cost Optimization
- Monitor Bedrock model invocation costs
- Implement API Gateway caching
- Use OpenSearch Serverless efficiently
- Set up cost alerts and budgets

### High Availability
- Deploy across multiple AZs
- Implement proper error handling and retries
- Set up health checks and monitoring
- Consider cross-region disaster recovery

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes and add tests
4. Commit your changes: `git commit -am 'Add new feature'`
5. Push to the branch: `git push origin feature/new-feature`
6. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- **Issues**: Create an issue in this repository
- **AWS Support**: Contact AWS Support for service-related issues
- **Community**: Join the AWS AI/ML community forums

## 🎯 Roadmap

- [ ] Add support for custom embedding models
- [ ] Implement agent collaboration features
- [ ] Add support for multimodal inputs (images, documents)
- [ ] Integrate with Amazon Bedrock Flows
- [ ] Add automated testing frameworks
- [ ] Implement CI/CD pipeline examples
- [ ] Add performance optimization guides

---

**Note**: This is a demonstration project. For production use, please review and customize the security settings, monitoring configurations, and cost optimizations according to your organization's requirements.