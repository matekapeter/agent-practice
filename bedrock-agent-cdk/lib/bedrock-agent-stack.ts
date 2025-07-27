import * as cdk from 'aws-cdk-lib';
import * as bedrock from 'aws-cdk-lib/aws-bedrock';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as cr from 'aws-cdk-lib/custom-resources';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment';
import { Construct } from 'constructs';

export interface BedrockAgentStackProps extends cdk.StackProps {
  guardrailArn: string;
  knowledgeBaseId: string;
  lambdaFunctionArn: string;
}

export class BedrockAgentStack extends cdk.Stack {
  public readonly agentId: string;
  public readonly agentArn: string;
  public readonly agentAliasId: string;
  public readonly agentAliasArn: string;

  constructor(scope: Construct, id: string, props: BedrockAgentStackProps) {
    super(scope, id, props);

    // Create S3 bucket for agent schemas and configurations
    const schemaBucket = new s3.Bucket(this, 'AgentSchemaBucket', {
      bucketName: `bedrock-agent-schemas-${this.account}-${this.region}`,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
    });

    // Deploy action group schemas to S3
    new s3deploy.BucketDeployment(this, 'ActionGroupSchemas', {
      sources: [s3deploy.Source.asset('./assets/action-group-schemas')],
      destinationBucket: schemaBucket,
      destinationKeyPrefix: 'schemas/',
    });

    // Create IAM role for Bedrock Agent
    const agentRole = new iam.Role(this, 'BedrockAgentRole', {
      roleName: `AmazonBedrockExecutionRoleForAgents_${this.region}`,
      assumedBy: new iam.ServicePrincipal('bedrock.amazonaws.com'),
      description: 'IAM role for Bedrock Agent to access various AWS services',
    });

    // Add model invocation permissions
    agentRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          'bedrock:InvokeModel',
          'bedrock:InvokeModelWithResponseStream',
        ],
        resources: [
          `arn:aws:bedrock:${this.region}::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0`,
          `arn:aws:bedrock:${this.region}::foundation-model/anthropic.claude-3-haiku-20240307-v1:0`,
          `arn:aws:bedrock:${this.region}::foundation-model/amazon.nova-pro-v1:0`,
          `arn:aws:bedrock:${this.region}::foundation-model/amazon.nova-lite-v1:0`,
        ],
      })
    );

    // Add Lambda invocation permissions
    agentRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ['lambda:InvokeFunction'],
        resources: [props.lambdaFunctionArn],
      })
    );

    // Add Knowledge Base access permissions
    agentRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          'bedrock:Retrieve',
          'bedrock:RetrieveAndGenerate',
        ],
        resources: [`arn:aws:bedrock:${this.region}:${this.account}:knowledge-base/${props.knowledgeBaseId}`],
      })
    );

    // Add S3 access for schemas
    agentRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          's3:GetObject',
          's3:ListBucket',
        ],
        resources: [
          schemaBucket.bucketArn,
          `${schemaBucket.bucketArn}/*`,
        ],
      })
    );

    // Add guardrail access permissions
    agentRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          'bedrock:ApplyGuardrail',
        ],
        resources: [props.guardrailArn],
      })
    );

    // Create Bedrock Agent
    const agent = new bedrock.CfnAgent(this, 'BedrockAgent', {
      agentName: 'comprehensive-ai-agent',
      description: 'Comprehensive AI agent with advanced prompt management, guardrails, knowledge base, and action groups',
      foundationModel: 'anthropic.claude-3-5-sonnet-20241022-v2:0',
      agentResourceRoleArn: agentRole.roleArn,
      autoPrepare: true,
      idleSessionTtlInSeconds: 1800, // 30 minutes
      
      // Agent instructions with comprehensive guidance
      instruction: `You are a sophisticated AI assistant designed to help users with a wide variety of tasks. You have access to:

1. **Knowledge Base**: A comprehensive knowledge repository for answering questions with factual, up-to-date information
2. **Action Groups**: Functions to perform specific actions like user management, product search, order tracking, appointments, notifications, weather information, and pricing calculations
3. **Guardrails**: Safety measures to ensure responsible and appropriate interactions

## Your Capabilities:

### Information Retrieval
- Search and provide information from the knowledge base
- Answer questions with accuracy and cite sources when possible
- Explain complex topics in an accessible manner

### Business Operations
- Help users manage their profiles and preferences
- Search for products and services
- Track orders and provide status updates
- Schedule appointments and manage calendars
- Send notifications and alerts
- Provide weather information
- Calculate pricing and costs

### Communication Style
- Be helpful, professional, and friendly
- Provide clear and concise answers
- Ask clarifying questions when needed
- Acknowledge limitations and uncertainties
- Always prioritize user safety and privacy

### Safety Guidelines
- Never provide harmful, illegal, or inappropriate content
- Respect user privacy and handle PII appropriately
- Stay within your defined capabilities
- Escalate complex issues to human agents when necessary

When using action groups, always explain what you're doing and confirm actions with users when appropriate. Use the knowledge base to provide accurate, contextual information. Always follow the guardrails and safety measures in place.`,

      // Advanced prompt override configuration
      promptOverrideConfiguration: {
        promptConfigurations: [
          {
            promptType: 'PRE_PROCESSING',
            promptCreationMode: 'OVERRIDDEN',
            promptState: 'ENABLED',
            basePromptTemplate: `You are an intelligent AI agent that helps users with various tasks. Before processing any user input, you should:

1. Analyze the user's request to understand their intent
2. Determine if the request requires knowledge base search, action group functions, or both
3. Check if the request complies with safety guidelines
4. Plan your approach to provide the most helpful response

User input: <user_input>{{$input}}</user_input>

Instructions: <instructions>{{$instructions}}</instructions>

Agent scratchpad: <agent_scratchpad>{{$agent_scratchpad}}</agent_scratchpad>

Based on this input, think about:
- What information or actions the user needs
- Which tools (knowledge base or action groups) would be most helpful
- How to structure your response for clarity
- Any safety considerations

Your analysis:`,
            inferenceConfiguration: {
              temperature: 0.1,
              topP: 0.9,
              maximumLength: 2000,
              stopSequences: ['</analysis>'],
            },
          },
          {
            promptType: 'ORCHESTRATION',
            promptCreationMode: 'OVERRIDDEN',
            promptState: 'ENABLED',
            basePromptTemplate: `You are an intelligent AI agent with access to tools and knowledge. Your goal is to help the user with their request.

Available tools:
- Knowledge Base: Search for factual information from your knowledge repository
- Action Groups: Execute specific functions like user management, product search, order tracking, etc.

User request: <user_request>{{$input}}</user_request>

Instructions: <instructions>{{$instructions}}</instructions>

Chat history: <chat_history>{{$chat_history}}</chat_history>

Available functions: <functions>{{$functions}}</functions>

Knowledge base information: <knowledge_base>{{$knowledge_base}}</knowledge_base>

Think step by step:
1. Understand what the user wants
2. Decide which tools to use
3. Execute the appropriate actions
4. Provide a comprehensive response

Agent scratchpad: <agent_scratchpad>{{$agent_scratchpad}}</agent_scratchpad>

Your response:`,
            inferenceConfiguration: {
              temperature: 0.2,
              topP: 0.9,
              maximumLength: 3000,
              stopSequences: ['</response>'],
            },
          },
          {
            promptType: 'KNOWLEDGE_BASE_RESPONSE_GENERATION',
            promptCreationMode: 'OVERRIDDEN',
            promptState: 'ENABLED',
            basePromptTemplate: `You are generating a response based on information retrieved from the knowledge base. Use the provided information to answer the user's question accurately and comprehensively.

User question: <question>{{$input}}</question>

Retrieved information: <retrieved_info>{{$search_results}}</retrieved_info>

Instructions: <instructions>{{$instructions}}</instructions>

Guidelines for your response:
1. Use the retrieved information as your primary source
2. If the information is incomplete, acknowledge this
3. Provide citations or references when possible
4. Be clear and concise while being thorough
5. If the retrieved information doesn't answer the question, say so

Your response based on the knowledge base:`,
            inferenceConfiguration: {
              temperature: 0.1,
              topP: 0.9,
              maximumLength: 2000,
              stopSequences: ['</response>'],
            },
          },
          {
            promptType: 'POST_PROCESSING',
            promptCreationMode: 'OVERRIDDEN',
            promptState: 'ENABLED',
            basePromptTemplate: `You are finalizing your response to the user. Review your draft response and make any necessary improvements.

User request: <user_request>{{$input}}</user_request>

Draft response: <draft_response>{{$completion}}</draft_response>

Instructions: <instructions>{{$instructions}}</instructions>

Review checklist:
1. Is the response helpful and complete?
2. Is it clear and well-structured?
3. Does it address the user's specific needs?
4. Is it appropriate and safe?
5. Are there any improvements needed?

Provide your final, polished response:`,
            inferenceConfiguration: {
              temperature: 0.1,
              topP: 0.9,
              maximumLength: 2000,
              stopSequences: ['</final_response>'],
            },
          },
        ],
      },

      // Guardrail configuration
      guardrailConfiguration: {
        guardrailIdentifier: props.guardrailArn,
        guardrailVersion: 'DRAFT',
      },

      // Memory configuration for conversation context
      memoryConfiguration: {
        enabledMemoryTypes: ['SESSION_SUMMARY'],
        storageDays: 30,
        sessionSummaryConfiguration: {
          maxRecentSessions: 10,
        },
      },

      // Action Groups configuration
      actionGroups: [
        {
          actionGroupName: 'business-operations',
          description: 'Business operations including user management, product search, orders, and appointments',
          actionGroupExecutor: {
            lambda: props.lambdaFunctionArn,
          },
          actionGroupState: 'ENABLED',
          apiSchema: {
            s3: {
              s3BucketName: schemaBucket.bucketName,
              s3ObjectKey: 'schemas/business-operations-schema.json',
            },
          },
        },
        {
          actionGroupName: 'utility-services',
          description: 'Utility services like weather information, notifications, and pricing calculations',
          actionGroupExecutor: {
            lambda: props.lambdaFunctionArn,
          },
          actionGroupState: 'ENABLED',
          apiSchema: {
            s3: {
              s3BucketName: schemaBucket.bucketName,
              s3ObjectKey: 'schemas/utility-services-schema.json',
            },
          },
        },
      ],

      // Knowledge Base association
      knowledgeBases: [
        {
          knowledgeBaseId: props.knowledgeBaseId,
          description: 'Comprehensive knowledge base for factual information and documentation',
          knowledgeBaseState: 'ENABLED',
        },
      ],
    });

    // Create Agent Alias for deployment
    const agentAlias = new bedrock.CfnAgentAlias(this, 'BedrockAgentAlias', {
      agentId: agent.attrAgentId,
      agentAliasName: 'production',
      description: 'Production alias for the comprehensive AI agent',
      routingConfiguration: [
        {
          agentVersion: 'DRAFT',
        },
      ],
    });

    // Store outputs for use in other stacks
    this.agentId = agent.attrAgentId;
    this.agentArn = agent.attrAgentArn;
    this.agentAliasId = agentAlias.attrAgentAliasId;
    this.agentAliasArn = agentAlias.attrAgentAliasArn;

    // Export values for cross-stack references
    new cdk.CfnOutput(this, 'AgentId', {
      value: this.agentId,
      description: 'ID of the Bedrock Agent',
      exportName: `${this.stackName}-AgentId`,
    });

    new cdk.CfnOutput(this, 'AgentArn', {
      value: this.agentArn,
      description: 'ARN of the Bedrock Agent',
      exportName: `${this.stackName}-AgentArn`,
    });

    new cdk.CfnOutput(this, 'AgentAliasId', {
      value: this.agentAliasId,
      description: 'ID of the Bedrock Agent Alias',
      exportName: `${this.stackName}-AgentAliasId`,
    });

    new cdk.CfnOutput(this, 'AgentAliasArn', {
      value: this.agentAliasArn,
      description: 'ARN of the Bedrock Agent Alias',
      exportName: `${this.stackName}-AgentAliasArn`,
    });

    // Tag resources
    cdk.Tags.of(this).add('Component', 'Agent');
    cdk.Tags.of(this).add('Purpose', 'AIOrchestration');
  }
}