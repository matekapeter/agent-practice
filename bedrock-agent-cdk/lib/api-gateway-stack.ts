import * as cdk from 'aws-cdk-lib';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import { Construct } from 'constructs';

export interface ApiGatewayStackProps extends cdk.StackProps {
  agentId: string;
  agentAliasId: string;
}

export class ApiGatewayStack extends cdk.Stack {
  public readonly apiUrl: string;
  public readonly userPoolId: string;
  public readonly userPoolClientId: string;

  constructor(scope: Construct, id: string, props: ApiGatewayStackProps) {
    super(scope, id, props);

    // Create Cognito User Pool for authentication
    const userPool = new cognito.UserPool(this, 'BedrockAgentUserPool', {
      userPoolName: 'bedrock-agent-users',
      selfSignUpEnabled: true,
      signInAliases: {
        email: true,
        username: true,
      },
      autoVerify: {
        email: true,
      },
      passwordPolicy: {
        minLength: 8,
        requireLowercase: true,
        requireUppercase: true,
        requireDigits: true,
        requireSymbols: true,
      },
      accountRecovery: cognito.AccountRecovery.EMAIL_ONLY,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // Create Cognito User Pool Client
    const userPoolClient = new cognito.UserPoolClient(this, 'BedrockAgentUserPoolClient', {
      userPool,
      userPoolClientName: 'bedrock-agent-client',
      generateSecret: false,
      authFlows: {
        userPassword: true,
        userSrp: true,
      },
      oAuth: {
        flows: {
          authorizationCodeGrant: true,
        },
        scopes: [
          cognito.OAuthScope.EMAIL,
          cognito.OAuthScope.OPENID,
          cognito.OAuthScope.PROFILE,
        ],
      },
    });

    // Create CloudWatch Log Group for API Gateway
    const apiLogGroup = new logs.LogGroup(this, 'ApiGatewayLogGroup', {
      logGroupName: `/aws/apigateway/bedrock-agent-api`,
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // Create Lambda function to handle Bedrock Agent invocation
    const agentInvokerFunction = new lambda.Function(this, 'AgentInvokerFunction', {
      functionName: 'bedrock-agent-invoker',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'index.lambda_handler',
      code: lambda.Code.fromInline(`
import json
import boto3
import logging
from typing import Dict, Any
import uuid

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize Bedrock Agent Runtime client
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Lambda handler to invoke Bedrock Agent and return the response.
    """
    try:
        logger.info(f"Received event: {json.dumps(event, default=str)}")
        
        # Extract request information
        http_method = event.get('httpMethod', 'POST')
        path = event.get('path', '')
        body = event.get('body', '{}')
        headers = event.get('headers', {})
        
        # Parse request body
        if isinstance(body, str):
            try:
                request_data = json.loads(body)
            except json.JSONDecodeError:
                return create_error_response(400, "Invalid JSON in request body")
        else:
            request_data = body
        
        # Extract required parameters
        agent_id = request_data.get('agentId') or '${props.agentId}'
        agent_alias_id = request_data.get('agentAliasId') or '${props.agentAliasId}'
        session_id = request_data.get('sessionId') or str(uuid.uuid4())
        input_text = request_data.get('inputText') or request_data.get('message', '')
        enable_trace = request_data.get('enableTrace', False)
        end_session = request_data.get('endSession', False)
        
        if not input_text:
            return create_error_response(400, "inputText or message is required")
        
        logger.info(f"Invoking agent {agent_id} with alias {agent_alias_id}")
        logger.info(f"Session ID: {session_id}")
        logger.info(f"Input: {input_text}")
        
        # Prepare the request to Bedrock Agent
        invoke_params = {
            'agentId': agent_id,
            'agentAliasId': agent_alias_id,
            'sessionId': session_id,
            'inputText': input_text,
            'enableTrace': enable_trace,
            'endSession': end_session
        }
        
        # Handle different API endpoints
        if path.endswith('/invoke'):
            return handle_invoke_agent(invoke_params)
        elif path.endswith('/invoke-stream'):
            return handle_invoke_agent_stream(invoke_params)
        else:
            return handle_invoke_agent(invoke_params)
            
    except Exception as e:
        logger.error(f"Error invoking Bedrock Agent: {str(e)}")
        return create_error_response(500, f"Internal server error: {str(e)}")

def handle_invoke_agent(invoke_params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle non-streaming agent invocation."""
    try:
        response = bedrock_agent_runtime.invoke_agent(**invoke_params)
        
        # Process the response stream
        result_text = ""
        citations = []
        trace_data = []
        
        for event in response.get('completion', []):
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    result_text += chunk['bytes'].decode('utf-8')
                if 'attribution' in chunk:
                    citations.extend(chunk['attribution'].get('citations', []))
            elif 'trace' in event:
                trace_data.append(event['trace'])
        
        # Prepare response
        response_data = {
            'sessionId': invoke_params['sessionId'],
            'response': result_text,
            'citations': citations,
            'responseMetadata': {
                'agentId': invoke_params['agentId'],
                'agentAliasId': invoke_params['agentAliasId'],
                'timestamp': response.get('ResponseMetadata', {}).get('HTTPHeaders', {}).get('date', ''),
            }
        }
        
        if invoke_params.get('enableTrace'):
            response_data['trace'] = trace_data
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            },
            'body': json.dumps(response_data, default=str)
        }
        
    except Exception as e:
        logger.error(f"Error in handle_invoke_agent: {str(e)}")
        return create_error_response(500, f"Error invoking agent: {str(e)}")

def handle_invoke_agent_stream(invoke_params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle streaming agent invocation (simplified for HTTP response)."""
    # For API Gateway, we'll collect the stream and return as a single response
    # In a real application, you might want to use WebSockets for true streaming
    return handle_invoke_agent(invoke_params)

def create_error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Create a standardized error response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        },
        'body': json.dumps({
            'error': {
                'code': status_code,
                'message': message
            }
        })
    }
      `),
      timeout: cdk.Duration.minutes(5),
      memorySize: 512,
      environment: {
        'AGENT_ID': props.agentId,
        'AGENT_ALIAS_ID': props.agentAliasId,
        'LOG_LEVEL': 'INFO',
      },
    });

    // Add permissions for the Lambda function to invoke Bedrock Agent
    agentInvokerFunction.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          'bedrock:InvokeAgent',
        ],
        resources: [
          `arn:aws:bedrock:${this.region}:${this.account}:agent-alias/${props.agentId}/${props.agentAliasId}`,
        ],
      })
    );

    // Create Cognito Authorizer
    const cognitoAuthorizer = new apigateway.CognitoUserPoolsAuthorizer(this, 'CognitoAuthorizer', {
      cognitoUserPools: [userPool],
      authorizerName: 'BedrockAgentAuthorizer',
      identitySource: 'method.request.header.Authorization',
    });

    // Create API Gateway
    const api = new apigateway.RestApi(this, 'BedrockAgentApi', {
      restApiName: 'Bedrock Agent API',
      description: 'REST API for interacting with Bedrock Agent',
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: ['Content-Type', 'Authorization'],
      },
      deployOptions: {
        stageName: 'prod',
        accessLogDestination: new apigateway.LogGroupLogDestination(apiLogGroup),
        accessLogFormat: apigateway.AccessLogFormat.jsonWithStandardFields({
          caller: true,
          httpMethod: true,
          ip: true,
          protocol: true,
          requestTime: true,
          resourcePath: true,
          responseLength: true,
          status: true,
          user: true,
        }),
        loggingLevel: apigateway.MethodLoggingLevel.INFO,
        dataTraceEnabled: true,
        metricsEnabled: true,
      },
      policy: new iam.PolicyDocument({
        statements: [
          new iam.PolicyStatement({
            effect: iam.Effect.ALLOW,
            principals: [new iam.AnyPrincipal()],
            actions: ['execute-api:Invoke'],
            resources: ['*'],
          }),
        ],
      }),
    });

    // Create request models for validation
    const invokeRequestModel = api.addModel('InvokeRequestModel', {
      contentType: 'application/json',
      modelName: 'InvokeRequest',
      schema: {
        schema: apigateway.JsonSchemaVersion.DRAFT4,
        title: 'Invoke Agent Request',
        type: apigateway.JsonSchemaType.OBJECT,
        properties: {
          inputText: {
            type: apigateway.JsonSchemaType.STRING,
            description: 'The text input to send to the agent',
            minLength: 1,
            maxLength: 4000,
          },
          sessionId: {
            type: apigateway.JsonSchemaType.STRING,
            description: 'Session ID for conversation continuity (optional)',
            pattern: '^[a-zA-Z0-9-]+$',
          },
          enableTrace: {
            type: apigateway.JsonSchemaType.BOOLEAN,
            description: 'Enable trace information in the response',
          },
          endSession: {
            type: apigateway.JsonSchemaType.BOOLEAN,
            description: 'End the current session after this request',
          },
        },
        required: ['inputText'],
      },
    });

    // Create request validator
    const requestValidator = new apigateway.RequestValidator(this, 'RequestValidator', {
      restApi: api,
      requestValidatorName: 'Validate body and parameters',
      validateRequestBody: true,
      validateRequestParameters: true,
    });

    // Create agent resource
    const agentResource = api.root.addResource('agent');

    // Add invoke endpoint
    const invokeResource = agentResource.addResource('invoke');
    invokeResource.addMethod('POST', new apigateway.LambdaIntegration(agentInvokerFunction), {
      authorizer: cognitoAuthorizer,
      authorizationType: apigateway.AuthorizationType.COGNITO,
      requestValidator,
      requestModels: {
        'application/json': invokeRequestModel,
      },
      methodResponses: [
        {
          statusCode: '200',
          responseModels: {
            'application/json': apigateway.Model.EMPTY_MODEL,
          },
          responseParameters: {
            'method.response.header.Access-Control-Allow-Origin': true,
            'method.response.header.Access-Control-Allow-Methods': true,
            'method.response.header.Access-Control-Allow-Headers': true,
          },
        },
        {
          statusCode: '400',
          responseModels: {
            'application/json': apigateway.Model.ERROR_MODEL,
          },
        },
        {
          statusCode: '500',
          responseModels: {
            'application/json': apigateway.Model.ERROR_MODEL,
          },
        },
      ],
    });

    // Add streaming endpoint (for future enhancement)
    const streamResource = agentResource.addResource('invoke-stream');
    streamResource.addMethod('POST', new apigateway.LambdaIntegration(agentInvokerFunction), {
      authorizer: cognitoAuthorizer,
      authorizationType: apigateway.AuthorizationType.COGNITO,
      requestValidator,
      requestModels: {
        'application/json': invokeRequestModel,
      },
    });

    // Add health check endpoint (no auth required)
    const healthResource = api.root.addResource('health');
    healthResource.addMethod('GET', new apigateway.MockIntegration({
      integrationResponses: [
        {
          statusCode: '200',
          responseTemplates: {
            'application/json': JSON.stringify({
              status: 'healthy',
              timestamp: '$context.requestTime',
              service: 'bedrock-agent-api',
            }),
          },
        },
      ],
      requestTemplates: {
        'application/json': '{"statusCode": 200}',
      },
    }), {
      methodResponses: [
        {
          statusCode: '200',
          responseModels: {
            'application/json': apigateway.Model.EMPTY_MODEL,
          },
        },
      ],
    });

    // Add usage plan for rate limiting
    const usagePlan = api.addUsagePlan('BedrockAgentUsagePlan', {
      name: 'Bedrock Agent Usage Plan',
      description: 'Usage plan for Bedrock Agent API',
      throttle: {
        rateLimit: 100, // requests per second
        burstLimit: 200, // burst capacity
      },
      quota: {
        limit: 10000, // requests per period
        period: apigateway.Period.DAY,
      },
      apiStages: [
        {
          api,
          stage: api.deploymentStage,
        },
      ],
    });

    // Create API key for programmatic access
    const apiKey = api.addApiKey('BedrockAgentApiKey', {
      apiKeyName: 'bedrock-agent-api-key',
      description: 'API key for Bedrock Agent API',
    });

    usagePlan.addApiKey(apiKey);

    // Store outputs
    this.apiUrl = api.url;
    this.userPoolId = userPool.userPoolId;
    this.userPoolClientId = userPoolClient.userPoolClientId;

    // Export values
    new cdk.CfnOutput(this, 'ApiUrl', {
      value: this.apiUrl,
      description: 'URL of the Bedrock Agent API',
      exportName: `${this.stackName}-ApiUrl`,
    });

    new cdk.CfnOutput(this, 'UserPoolId', {
      value: this.userPoolId,
      description: 'Cognito User Pool ID',
      exportName: `${this.stackName}-UserPoolId`,
    });

    new cdk.CfnOutput(this, 'UserPoolClientId', {
      value: this.userPoolClientId,
      description: 'Cognito User Pool Client ID',
      exportName: `${this.stackName}-UserPoolClientId`,
    });

    new cdk.CfnOutput(this, 'ApiKeyId', {
      value: apiKey.keyId,
      description: 'API Key ID for programmatic access',
      exportName: `${this.stackName}-ApiKeyId`,
    });

    // Tag resources
    cdk.Tags.of(this).add('Component', 'API');
    cdk.Tags.of(this).add('Purpose', 'AgentInterface');
  }
}