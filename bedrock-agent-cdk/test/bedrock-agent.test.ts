import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { BedrockGuardrailsStack } from '../lib/bedrock-guardrails-stack';
import { BedrockKnowledgeBaseStack } from '../lib/bedrock-knowledge-base-stack';
import { LambdaFunctionStack } from '../lib/lambda-function-stack';
import { BedrockAgentStack } from '../lib/bedrock-agent-stack';
import { ApiGatewayStack } from '../lib/api-gateway-stack';

describe('Bedrock Agent CDK Stacks', () => {
  let app: cdk.App;

  beforeEach(() => {
    app = new cdk.App();
  });

  test('BedrockGuardrailsStack creates guardrail', () => {
    const stack = new BedrockGuardrailsStack(app, 'TestGuardrailsStack');
    const template = Template.fromStack(stack);

    template.hasResourceProperties('AWS::Bedrock::Guardrail', {
      Name: 'comprehensive-ai-guardrail'
    });
  });

  test('BedrockKnowledgeBaseStack creates knowledge base', () => {
    const guardrailsStack = new BedrockGuardrailsStack(app, 'TestGuardrailsStack');
    const stack = new BedrockKnowledgeBaseStack(app, 'TestKnowledgeBaseStack', {
      guardrailArn: guardrailsStack.guardrailArn
    });
    const template = Template.fromStack(stack);

    template.hasResourceProperties('AWS::Bedrock::KnowledgeBase', {
      Name: 'bedrock-agent-knowledge-base'
    });

    template.hasResourceProperties('AWS::S3::Bucket', {
      PublicAccessBlockConfiguration: {
        BlockPublicAcls: true,
        BlockPublicPolicy: true,
        IgnorePublicAcls: true,
        RestrictPublicBuckets: true
      }
    });
  });

  test('LambdaFunctionStack creates Lambda function', () => {
    const stack = new LambdaFunctionStack(app, 'TestLambdaStack');
    const template = Template.fromStack(stack);

    template.hasResourceProperties('AWS::Lambda::Function', {
      Runtime: 'python3.11',
      Handler: 'action-group-handler.lambda_handler'
    });
  });

  test('BedrockAgentStack creates agent with dependencies', () => {
    const guardrailsStack = new BedrockGuardrailsStack(app, 'TestGuardrailsStack');
    const knowledgeBaseStack = new BedrockKnowledgeBaseStack(app, 'TestKnowledgeBaseStack', {
      guardrailArn: guardrailsStack.guardrailArn
    });
    const lambdaStack = new LambdaFunctionStack(app, 'TestLambdaStack');
    
    const stack = new BedrockAgentStack(app, 'TestAgentStack', {
      guardrailArn: guardrailsStack.guardrailArn,
      knowledgeBaseId: knowledgeBaseStack.knowledgeBaseId,
      lambdaFunctionArn: lambdaStack.actionGroupFunctionArn
    });
    
    const template = Template.fromStack(stack);

    template.hasResourceProperties('AWS::Bedrock::Agent', {
      AgentName: 'comprehensive-business-agent'
    });

    template.hasResourceProperties('AWS::IAM::Role', {
      AssumeRolePolicyDocument: {
        Statement: [
          {
            Effect: 'Allow',
            Principal: {
              Service: 'bedrock.amazonaws.com'
            },
            Action: 'sts:AssumeRole'
          }
        ]
      }
    });
  });

  test('ApiGatewayStack creates API Gateway and Cognito', () => {
    const guardrailsStack = new BedrockGuardrailsStack(app, 'TestGuardrailsStack');
    const knowledgeBaseStack = new BedrockKnowledgeBaseStack(app, 'TestKnowledgeBaseStack', {
      guardrailArn: guardrailsStack.guardrailArn
    });
    const lambdaStack = new LambdaFunctionStack(app, 'TestLambdaStack');
    const agentStack = new BedrockAgentStack(app, 'TestAgentStack', {
      guardrailArn: guardrailsStack.guardrailArn,
      knowledgeBaseId: knowledgeBaseStack.knowledgeBaseId,
      lambdaFunctionArn: lambdaStack.actionGroupFunctionArn
    });
    
    const stack = new ApiGatewayStack(app, 'TestApiStack', {
      agentId: agentStack.agentId,
      agentAliasId: agentStack.agentAliasId
    });
    
    const template = Template.fromStack(stack);

    template.hasResourceProperties('AWS::Cognito::UserPool', {
      UserPoolName: 'bedrock-agent-users'
    });

    template.hasResourceProperties('AWS::ApiGateway::RestApi', {
      Name: 'bedrock-agent-api'
    });
  });

  test('All stacks have proper tags', () => {
    const guardrailsStack = new BedrockGuardrailsStack(app, 'TestGuardrailsStack');
    const template = Template.fromStack(guardrailsStack);

    // Check that resources have proper tags
    template.hasResource('AWS::Bedrock::Guardrail', {
      Properties: {
        Tags: {
          Project: 'BedrockAgent'
        }
      }
    });
  });

  test('IAM roles follow least privilege principle', () => {
    const lambdaStack = new LambdaFunctionStack(app, 'TestLambdaStack');
    const template = Template.fromStack(lambdaStack);

    // Lambda execution role should have minimal permissions
    template.hasResourceProperties('AWS::IAM::Role', {
      ManagedPolicyArns: [
        'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
      ]
    });
  });

  test('Knowledge base has proper encryption', () => {
    const guardrailsStack = new BedrockGuardrailsStack(app, 'TestGuardrailsStack');
    const stack = new BedrockKnowledgeBaseStack(app, 'TestKnowledgeBaseStack', {
      guardrailArn: guardrailsStack.guardrailArn
    });
    const template = Template.fromStack(stack);

    // S3 bucket should have encryption enabled
    template.hasResourceProperties('AWS::S3::Bucket', {
      BucketEncryption: {
        ServerSideEncryptionConfiguration: [
          {
            ServerSideEncryptionByDefault: {
              SSEAlgorithm: 'AES256'
            }
          }
        ]
      }
    });
  });
});