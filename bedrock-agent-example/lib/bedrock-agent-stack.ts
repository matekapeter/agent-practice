import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment';
import { BedrockAgent } from './constructs/bedrock-agent';
import { BedrockGuardrails } from './constructs/bedrock-guardrails';
import { KnowledgeBase } from './constructs/knowledge-base';
import { ActionGroups } from './constructs/action-groups';

export interface BedrockAgentStackProps extends cdk.StackProps {
  readonly agentName?: string;
  readonly foundationModel?: string;
  readonly knowledgeBaseName?: string;
  readonly guardrailName?: string;
  readonly idleSessionTTL?: number;
}

export class BedrockAgentStack extends cdk.Stack {
  public readonly agentId: string;
  public readonly agentAliasId: string;
  public readonly knowledgeBaseId: string;
  public readonly guardrailId: string;

  constructor(scope: Construct, id: string, props?: BedrockAgentStackProps) {
    super(scope, id, props);

    // Configuration with defaults
    const config = {
      agentName: props?.agentName || 'MyAIAgent',
      foundationModel: props?.foundationModel || 'anthropic.claude-3-haiku-20240307-v1:0',
      knowledgeBaseName: props?.knowledgeBaseName || 'MyKnowledgeBase',
      guardrailName: props?.guardrailName || 'MyGuardrail',
      idleSessionTTL: props?.idleSessionTTL || 3600,
    };

    // S3 bucket for knowledge base documents
    const knowledgeBaseBucket = new s3.Bucket(this, 'KnowledgeBaseBucket', {
      bucketName: `${config.agentName.toLowerCase()}-kb-${this.account}-${this.region}`,
      versioned: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    // S3 bucket for OpenAPI schemas
    const schemasBucket = new s3.Bucket(this, 'SchemasBucket', {
      bucketName: `${config.agentName.toLowerCase()}-schemas-${this.account}-${this.region}`,
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    // Deploy OpenAPI schemas
    new s3deploy.BucketDeployment(this, 'DeploySchemas', {
      sources: [s3deploy.Source.asset('./assets/openapi-schemas')],
      destinationBucket: schemasBucket,
      destinationKeyPrefix: 'schemas/',
    });

    // Deploy sample documents (optional)
    new s3deploy.BucketDeployment(this, 'DeploySampleDocs', {
      sources: [s3deploy.Source.asset('./assets/sample-documents')],
      destinationBucket: knowledgeBaseBucket,
      destinationKeyPrefix: 'documents/',
    });

    // Create Bedrock Guardrails
    const guardrails = new BedrockGuardrails(this, 'BedrockGuardrails', {
      guardrailName: config.guardrailName,
      description: 'Comprehensive guardrails for responsible AI',
    });

    // Create Knowledge Base with OpenSearch Serverless
    const knowledgeBase = new KnowledgeBase(this, 'KnowledgeBase', {
      knowledgeBaseName: config.knowledgeBaseName,
      description: 'Knowledge base for RAG capabilities',
      dataSourceBucket: knowledgeBaseBucket,
    });

    // Create Action Groups with Lambda functions
    const actionGroups = new ActionGroups(this, 'ActionGroups', {
      schemasBucket: schemasBucket,
      agentName: config.agentName,
    });

    // Create the main Bedrock Agent
    const agent = new BedrockAgent(this, 'BedrockAgent', {
      agentName: config.agentName,
      foundationModel: config.foundationModel,
      instruction: this.getAgentInstruction(),
      idleSessionTTL: config.idleSessionTTL,
      guardrailConfiguration: {
        guardrailIdentifier: guardrails.guardrailId,
        guardrailVersion: guardrails.guardrailVersion,
      },
      knowledgeBaseIds: [knowledgeBase.knowledgeBaseId],
      actionGroups: actionGroups.actionGroups,
    });

    // Set up dependencies
    agent.node.addDependency(guardrails);
    agent.node.addDependency(knowledgeBase);
    agent.node.addDependency(actionGroups);

    // Output important values
    new cdk.CfnOutput(this, 'AgentId', {
      value: agent.agentId,
      description: 'Bedrock Agent ID',
    });

    new cdk.CfnOutput(this, 'AgentAliasId', {
      value: agent.agentAliasId,
      description: 'Bedrock Agent Alias ID',
    });

    new cdk.CfnOutput(this, 'KnowledgeBaseId', {
      value: knowledgeBase.knowledgeBaseId,
      description: 'Knowledge Base ID',
    });

    new cdk.CfnOutput(this, 'GuardrailId', {
      value: guardrails.guardrailId,
      description: 'Guardrail ID',
    });

    new cdk.CfnOutput(this, 'KnowledgeBaseBucketName', {
      value: knowledgeBaseBucket.bucketName,
      description: 'S3 bucket for knowledge base documents',
    });

    // Store outputs for access from other methods
    this.agentId = agent.agentId;
    this.agentAliasId = agent.agentAliasId;
    this.knowledgeBaseId = knowledgeBase.knowledgeBaseId;
    this.guardrailId = guardrails.guardrailId;

    // Add tags to all resources
    cdk.Tags.of(this).add('Project', 'BedrockAgent');
    cdk.Tags.of(this).add('Environment', 'Demo');
  }

  private getAgentInstruction(): string {
    return `
You are an intelligent AI assistant designed to help users with various tasks and questions.

**Your Capabilities:**
1. **Knowledge Base**: You have access to a comprehensive knowledge base containing documents and information that you can search and reference to answer questions accurately.

2. **Weather Information**: You can provide current weather information for any location worldwide through your weather action group.

3. **General Assistance**: You can help with a wide variety of tasks including:
   - Answering questions on various topics
   - Providing explanations and clarifications
   - Offering suggestions and recommendations
   - Assisting with problem-solving

**Guidelines for Interaction:**
- Always be helpful, honest, and harmless in your responses
- When answering questions that might be covered in your knowledge base, search the knowledge base first to provide accurate, up-to-date information
- For weather-related queries, use your weather action group to get real-time data
- If you're uncertain about something, acknowledge your limitations and suggest alternative approaches
- Provide clear, concise, and well-structured responses
- Ask clarifying questions when user requests are ambiguous
- Maintain context throughout the conversation to provide coherent follow-up responses

**Response Format:**
- Structure your responses clearly with appropriate formatting
- Use bullet points or numbered lists when presenting multiple items
- Cite your knowledge base when referencing specific documents or information
- Be conversational yet professional in tone

**Limitations:**
- Always acknowledge when you don't know something rather than guessing
- Respect user privacy and don't ask for unnecessary personal information
- Stay within your defined capabilities and don't claim abilities you don't have

Remember: Your goal is to be a helpful, reliable, and trustworthy AI assistant that provides accurate information and useful assistance while maintaining appropriate boundaries and ethical standards.
    `.trim();
  }
}