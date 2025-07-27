#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { BedrockGuardrailsStack } from '../lib/bedrock-guardrails-stack';
import { BedrockKnowledgeBaseStack } from '../lib/bedrock-knowledge-base-stack';
import { BedrockAgentStack } from '../lib/bedrock-agent-stack';
import { LambdaFunctionStack } from '../lib/lambda-function-stack';
import { ApiGatewayStack } from '../lib/api-gateway-stack';

const app = new cdk.App();

// Environment configuration
const env = {
  account: process.env.CDK_DEFAULT_ACCOUNT,
  region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
};

// Define stack props
const stackProps: cdk.StackProps = {
  env,
  description: 'AWS Native AI Agent with Bedrock Agents, Guardrails, and TypeScript CDK',
  tags: {
    Project: 'BedrockAgent',
    Environment: 'Demo',
    CreatedBy: 'CDK',
  },
};

// Create Guardrails Stack first (foundation)
const guardrailsStack = new BedrockGuardrailsStack(app, 'BedrockGuardrailsStack', stackProps);

// Create Knowledge Base Stack
const knowledgeBaseStack = new BedrockKnowledgeBaseStack(app, 'BedrockKnowledgeBaseStack', {
  ...stackProps,
  guardrailArn: guardrailsStack.guardrailArn,
});

// Create Lambda Functions Stack for action groups
const lambdaStack = new LambdaFunctionStack(app, 'LambdaFunctionStack', stackProps);

// Create Bedrock Agent Stack (depends on guardrails, knowledge base, and lambda)
const agentStack = new BedrockAgentStack(app, 'BedrockAgentStack', {
  ...stackProps,
  guardrailArn: guardrailsStack.guardrailArn,
  knowledgeBaseId: knowledgeBaseStack.knowledgeBaseId,
  lambdaFunctionArn: lambdaStack.actionGroupFunctionArn,
});

// Create API Gateway Stack for external access
const apiStack = new ApiGatewayStack(app, 'ApiGatewayStack', {
  ...stackProps,
  agentId: agentStack.agentId,
  agentAliasId: agentStack.agentAliasId,
});

// Add dependencies
knowledgeBaseStack.addDependency(guardrailsStack);
agentStack.addDependency(guardrailsStack);
agentStack.addDependency(knowledgeBaseStack);
agentStack.addDependency(lambdaStack);
apiStack.addDependency(agentStack);

// Add stack outputs for cross-stack references
app.synth();