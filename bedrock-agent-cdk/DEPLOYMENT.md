# Deployment Guide

This document provides step-by-step instructions for deploying the AWS Native AI Agent with Bedrock Agents, Guardrails, and TypeScript CDK.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Pre-Deployment Setup](#pre-deployment-setup)
3. [Deployment Methods](#deployment-methods)
4. [Post-Deployment Configuration](#post-deployment-configuration)
5. [Testing and Validation](#testing-and-validation)
6. [Troubleshooting](#troubleshooting)
7. [Clean Up](#clean-up)

## Prerequisites

### System Requirements

- **Operating System**: macOS, Linux, or Windows (with WSL2)
- **Node.js**: Version 18.x or later
- **Python**: Version 3.8 or later (for testing scripts)
- **AWS CLI**: Version 2.x
- **AWS CDK**: Version 2.100.0 or later

### AWS Account Requirements

- **AWS Account** with appropriate permissions
- **Bedrock Service** enabled in your target region
- **Model Access** enabled for required foundation models
- **IAM Permissions** for creating roles, policies, and resources

### Required AWS Services

Ensure these services are available in your target region:
- Amazon Bedrock
- AWS Lambda
- Amazon API Gateway
- Amazon Cognito
- Amazon OpenSearch Serverless
- Amazon S3
- AWS IAM
- AWS CloudWatch

## Pre-Deployment Setup

### 1. Install Prerequisites

#### Install Node.js and npm
```bash
# Using nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | bash
nvm install 18
nvm use 18

# Verify installation
node --version
npm --version
```

#### Install AWS CLI
```bash
# macOS
brew install awscli

# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Verify installation
aws --version
```

#### Install AWS CDK
```bash
npm install -g aws-cdk@latest

# Verify installation
cdk --version
```

### 2. Configure AWS CLI

```bash
aws configure
```

Provide your AWS credentials:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., us-east-1)
- Default output format (json)

### 3. Enable Bedrock Model Access

1. Go to the AWS Bedrock console in your target region
2. Navigate to **Model access** in the left sidebar
3. Request access to these models:
   - Anthropic Claude 3.5 Sonnet (`anthropic.claude-3-5-sonnet-20241022-v2:0`)
   - Anthropic Claude 3 Haiku (`anthropic.claude-3-haiku-20240307-v1:0`)
   - Amazon Nova Pro (`amazon.nova-pro-v1:0`)
   - Amazon Nova Lite (`amazon.nova-lite-v1:0`)
   - Amazon Titan Embeddings v2 (`amazon.titan-embed-text-v2:0`)

> **Note**: Model access requests may take some time to process. Wait for approval before proceeding.

### 4. Bootstrap CDK

If this is your first time using CDK in this region:

```bash
cdk bootstrap
```

## Deployment Methods

### Method 1: Automated Deployment (Recommended)

Use the provided deployment script for a fully automated deployment:

```bash
# Clone the repository
git clone <repository-url>
cd bedrock-agent-cdk

# Make the script executable (Linux/macOS)
chmod +x scripts/deploy.sh

# Run the deployment
./scripts/deploy.sh
```

The script will:
- Validate prerequisites
- Install dependencies
- Build the project
- Deploy all stacks in the correct order
- Configure post-deployment settings
- Create test user
- Generate deployment summary

### Method 2: Manual Deployment

For more control over the deployment process:

#### Step 1: Install Dependencies
```bash
npm install
```

#### Step 2: Build the Project
```bash
npm run build
```

#### Step 3: Deploy Stacks in Order

Deploy the stacks in the following sequence:

```bash
# 1. Deploy Guardrails Stack
cdk deploy BedrockGuardrailsStack

# 2. Deploy Knowledge Base Stack
cdk deploy BedrockKnowledgeBaseStack

# 3. Deploy Lambda Function Stack
cdk deploy LambdaFunctionStack

# 4. Deploy Bedrock Agent Stack
cdk deploy BedrockAgentStack

# 5. Deploy API Gateway Stack
cdk deploy ApiGatewayStack
```

## Post-Deployment Configuration

### 1. Retrieve Deployment Outputs

Get the outputs from your deployed stacks:

```bash
# Get all stack outputs
aws cloudformation describe-stacks --stack-name BedrockAgentStack --query 'Stacks[0].Outputs'
aws cloudformation describe-stacks --stack-name ApiGatewayStack --query 'Stacks[0].Outputs'
```

Important outputs to note:
- **Agent ID**: Required for testing
- **Agent Alias ID**: Required for testing
- **API Gateway URL**: For external access
- **User Pool ID**: For user management

### 2. Trigger Knowledge Base Ingestion

Start the data ingestion process:

```bash
# Get the Knowledge Base and Data Source IDs from outputs
KB_ID="<your-knowledge-base-id>"
DATA_SOURCE_ID="<your-data-source-id>"

# Start ingestion job
aws bedrock-agent start-ingestion-job \
  --knowledge-base-id $KB_ID \
  --data-source-id $DATA_SOURCE_ID
```

Monitor the ingestion status in the AWS Bedrock console.

### 3. Prepare the Agent

Prepare the agent for use:

```bash
# Get the Agent ID from outputs
AGENT_ID="<your-agent-id>"

# Prepare the agent
aws bedrock-agent prepare-agent --agent-id $AGENT_ID
```

### 4. Create Test Users

Create a test user in Cognito:

```bash
# Get the User Pool ID from outputs
USER_POOL_ID="<your-user-pool-id>"

# Create test user
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username testuser \
  --temporary-password "TempPass123!" \
  --message-action SUPPRESS \
  --user-attributes Name=email,Value=testuser@example.com
```

## Testing and Validation

### 1. Run Automated Tests

Use the provided test script:

```bash
# Install Python dependencies
pip install boto3

# Run comprehensive tests
python3 scripts/test-agent.py \
  --agent-id <your-agent-id> \
  --agent-alias-id <your-agent-alias-id> \
  --region us-east-1

# Run specific test categories
python3 scripts/test-agent.py \
  --agent-id <your-agent-id> \
  --agent-alias-id <your-agent-alias-id> \
  --test-type kb  # knowledge-base only
```

### 2. Manual Testing

#### Test Knowledge Base Queries
```bash
aws bedrock-agent-runtime invoke-agent \
  --agent-id <your-agent-id> \
  --agent-alias-id <your-agent-alias-id> \
  --session-id test-session-1 \
  --input-text "What are the company's vacation policies?"
```

#### Test Action Groups
```bash
aws bedrock-agent-runtime invoke-agent \
  --agent-id <your-agent-id> \
  --agent-alias-id <your-agent-alias-id> \
  --session-id test-session-2 \
  --input-text "Search for wireless headphones under $200"
```

### 3. API Gateway Testing

#### Get Authentication Token
```bash
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id <your-client-id> \
  --auth-parameters USERNAME=testuser,PASSWORD=<password>
```

#### Call the API
```bash
curl -X POST https://<api-id>.execute-api.<region>.amazonaws.com/prod/agent/invoke \
  -H "Authorization: Bearer <access-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "inputText": "Hello, I need help with my account",
    "sessionId": "test-session-api",
    "enableTrace": true
  }'
```

## Troubleshooting

### Common Issues

#### 1. Model Access Denied
**Error**: `AccessDeniedException: The model is not accessible`

**Solution**: 
- Check if you have requested access to the required models in the Bedrock console
- Wait for model access approval (can take several hours)

#### 2. CDK Bootstrap Issues
**Error**: `CDK is not bootstrapped in this environment`

**Solution**:
```bash
cdk bootstrap aws://<account-id>/<region>
```

#### 3. Agent Not Responding
**Error**: Agent invocation fails or returns empty responses

**Solution**:
- Ensure the agent is prepared: `aws bedrock-agent prepare-agent --agent-id <agent-id>`
- Check CloudWatch logs for errors
- Verify IAM permissions

#### 4. Knowledge Base Ingestion Fails
**Error**: Data ingestion job fails

**Solution**:
- Check S3 bucket permissions
- Verify document formats are supported
- Review ingestion job logs in CloudWatch

#### 5. API Gateway 403 Errors
**Error**: `403 Forbidden` when calling API

**Solution**:
- Verify authentication token is valid
- Check API Gateway authorizer configuration
- Ensure Cognito user pool is correctly configured

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
# CDK debug mode
cdk deploy --verbose

# AWS CLI debug mode
aws bedrock-agent invoke-agent --debug \
  --agent-id <agent-id> \
  --agent-alias-id <alias-id> \
  --session-id debug-session \
  --input-text "test"
```

### Log Analysis

Check CloudWatch logs for detailed error information:

- **Lambda Logs**: `/aws/lambda/bedrock-agent-action-group`
- **API Gateway Logs**: `/aws/apigateway/bedrock-agent-api`
- **Bedrock Agent Logs**: Available in CloudWatch with agent execution details

## Clean Up

### Delete All Resources

To remove all deployed resources:

```bash
# Delete stacks in reverse order
cdk destroy ApiGatewayStack
cdk destroy BedrockAgentStack
cdk destroy LambdaFunctionStack
cdk destroy BedrockKnowledgeBaseStack
cdk destroy BedrockGuardrailsStack
```

### Alternative: Delete All at Once
```bash
cdk destroy --all
```

### Manual Cleanup

Some resources may need manual cleanup:

1. **S3 Buckets**: Delete any remaining objects
2. **CloudWatch Logs**: Delete log groups if desired
3. **Bedrock Models**: Model access remains enabled
4. **CDK Bootstrap**: Keep for future CDK deployments

### Cost Verification

After cleanup, verify in the AWS Billing Console that no unexpected charges are occurring.

---

## Additional Resources

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [Bedrock Agent API Reference](https://docs.aws.amazon.com/bedrock/latest/APIReference/)
- [Troubleshooting Guide](TROUBLESHOOTING.md)

For support, please check the repository issues or AWS support channels.