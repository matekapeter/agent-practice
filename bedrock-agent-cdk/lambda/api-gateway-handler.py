import json
import logging
import boto3
import base64
from typing import Dict, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize Bedrock Agent Runtime client
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    API Gateway Lambda handler for invoking Bedrock Agent
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract HTTP method and path
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        
        # Handle CORS preflight requests
        if http_method == 'OPTIONS':
            return cors_response(200, {'message': 'CORS preflight'})
        
        # Parse request body
        body = event.get('body', '{}')
        if event.get('isBase64Encoded', False):
            body = base64.b64decode(body).decode('utf-8')
        
        try:
            request_data = json.loads(body)
        except json.JSONDecodeError:
            return cors_response(400, {'error': 'Invalid JSON in request body'})
        
        # Route based on path
        if path == '/agent/invoke':
            return handle_agent_invoke(request_data)
        elif path == '/agent/health':
            return handle_health_check()
        else:
            return cors_response(404, {'error': 'Endpoint not found'})
            
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return cors_response(500, {'error': 'Internal server error'})

def handle_agent_invoke(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle agent invocation requests
    """
    try:
        # Extract required parameters
        input_text = request_data.get('inputText', '')
        session_id = request_data.get('sessionId', 'default-session')
        enable_trace = request_data.get('enableTrace', False)
        
        if not input_text:
            return cors_response(400, {'error': 'inputText is required'})
        
        # Get agent configuration from environment variables
        import os
        agent_id = os.environ.get('AGENT_ID')
        agent_alias_id = os.environ.get('AGENT_ALIAS_ID')
        
        if not agent_id or not agent_alias_id:
            return cors_response(500, {'error': 'Agent configuration not found'})
        
        logger.info(f"Invoking agent {agent_id} with input: {input_text}")
        
        # Invoke the Bedrock Agent
        response = bedrock_agent_runtime.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id,
            inputText=input_text,
            enableTrace=enable_trace
        )
        
        # Process the streaming response
        result_text = ""
        traces = []
        
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    result_text += chunk['bytes'].decode('utf-8')
            elif 'trace' in event and enable_trace:
                traces.append(event['trace'])
        
        # Prepare response
        agent_response = {
            'sessionId': session_id,
            'text': result_text,
            'inputText': input_text
        }
        
        if enable_trace and traces:
            agent_response['traces'] = traces
        
        return cors_response(200, agent_response)
        
    except Exception as e:
        logger.error(f"Error invoking agent: {str(e)}")
        return cors_response(500, {'error': f'Failed to invoke agent: {str(e)}'})

def handle_health_check() -> Dict[str, Any]:
    """
    Handle health check requests
    """
    return cors_response(200, {
        'status': 'healthy',
        'service': 'bedrock-agent-api',
        'timestamp': boto3.client('sts').get_caller_identity().get('Arn', 'unknown')
    })

def cors_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a response with CORS headers
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
            'Access-Control-Max-Age': '86400'
        },
        'body': json.dumps(body)
    }