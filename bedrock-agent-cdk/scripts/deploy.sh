#!/bin/bash

# AWS Bedrock Agent CDK Deployment Script
# This script deploys the entire Bedrock Agent infrastructure in the correct order

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if AWS CLI is installed and configured
check_aws_cli() {
    log_info "Checking AWS CLI configuration..."
    
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS CLI is not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    REGION=$(aws configure get region)
    
    log_success "AWS CLI configured for account $ACCOUNT_ID in region $REGION"
}

# Check if CDK is installed and bootstrapped
check_cdk() {
    log_info "Checking CDK installation and bootstrap status..."
    
    if ! command -v cdk &> /dev/null; then
        log_error "AWS CDK is not installed. Please install it with: npm install -g aws-cdk"
        exit 1
    fi
    
    CDK_VERSION=$(cdk --version)
    log_info "CDK Version: $CDK_VERSION"
    
    # Check if CDK is bootstrapped
    if ! aws cloudformation describe-stacks --stack-name CDKToolkit &> /dev/null; then
        log_warning "CDK is not bootstrapped in this region. Running cdk bootstrap..."
        cdk bootstrap
        log_success "CDK bootstrap completed"
    else
        log_info "CDK is already bootstrapped"
    fi
}

# Check Bedrock model access
check_bedrock_models() {
    log_info "Checking Bedrock model access..."
    
    # List of required models
    REQUIRED_MODELS=(
        "anthropic.claude-3-5-sonnet-20241022-v2:0"
        "anthropic.claude-3-haiku-20240307-v1:0"
        "amazon.nova-pro-v1:0"
        "amazon.nova-lite-v1:0"
        "amazon.titan-embed-text-v2:0"
    )
    
    for model in "${REQUIRED_MODELS[@]}"; do
        if aws bedrock get-foundation-model --model-identifier "$model" &> /dev/null; then
            log_success "Model access confirmed: $model"
        else
            log_warning "Model access not confirmed: $model"
            log_warning "Please enable model access in the Bedrock console"
        fi
    done
}

# Install dependencies
install_dependencies() {
    log_info "Installing project dependencies..."
    
    if [ ! -f package.json ]; then
        log_error "package.json not found. Are you in the correct directory?"
        exit 1
    fi
    
    npm install
    log_success "Dependencies installed"
}

# Build the project
build_project() {
    log_info "Building TypeScript project..."
    npm run build
    log_success "Project built successfully"
}

# Deploy stacks in order
deploy_stacks() {
    log_info "Starting deployment of all stacks..."
    
    # 1. Deploy Guardrails Stack
    log_info "Deploying Bedrock Guardrails Stack..."
    cdk deploy BedrockGuardrailsStack --require-approval never
    log_success "Guardrails Stack deployed"
    
    # 2. Deploy Knowledge Base Stack
    log_info "Deploying Bedrock Knowledge Base Stack..."
    cdk deploy BedrockKnowledgeBaseStack --require-approval never
    log_success "Knowledge Base Stack deployed"
    
    # 3. Deploy Lambda Function Stack
    log_info "Deploying Lambda Function Stack..."
    cdk deploy LambdaFunctionStack --require-approval never
    log_success "Lambda Function Stack deployed"
    
    # 4. Deploy Bedrock Agent Stack
    log_info "Deploying Bedrock Agent Stack..."
    cdk deploy BedrockAgentStack --require-approval never
    log_success "Bedrock Agent Stack deployed"
    
    # 5. Deploy API Gateway Stack
    log_info "Deploying API Gateway Stack..."
    cdk deploy ApiGatewayStack --require-approval never
    log_success "API Gateway Stack deployed"
    
    log_success "All stacks deployed successfully!"
}

# Get stack outputs
get_stack_outputs() {
    log_info "Retrieving stack outputs..."
    
    # Get outputs from each stack
    GUARDRAIL_OUTPUTS=$(aws cloudformation describe-stacks --stack-name BedrockGuardrailsStack --query 'Stacks[0].Outputs' --output json 2>/dev/null || echo '[]')
    KB_OUTPUTS=$(aws cloudformation describe-stacks --stack-name BedrockKnowledgeBaseStack --query 'Stacks[0].Outputs' --output json 2>/dev/null || echo '[]')
    LAMBDA_OUTPUTS=$(aws cloudformation describe-stacks --stack-name LambdaFunctionStack --query 'Stacks[0].Outputs' --output json 2>/dev/null || echo '[]')
    AGENT_OUTPUTS=$(aws cloudformation describe-stacks --stack-name BedrockAgentStack --query 'Stacks[0].Outputs' --output json 2>/dev/null || echo '[]')
    API_OUTPUTS=$(aws cloudformation describe-stacks --stack-name ApiGatewayStack --query 'Stacks[0].Outputs' --output json 2>/dev/null || echo '[]')
    
    # Save all outputs to a file
    cat > deployment-outputs.json << EOF
{
  "guardrails": $GUARDRAIL_OUTPUTS,
  "knowledgeBase": $KB_OUTPUTS,
  "lambda": $LAMBDA_OUTPUTS,
  "agent": $AGENT_OUTPUTS,
  "apiGateway": $API_OUTPUTS
}
EOF
    
    log_success "Deployment outputs saved to deployment-outputs.json"
}

# Trigger Knowledge Base ingestion
trigger_kb_ingestion() {
    log_info "Triggering Knowledge Base data ingestion..."
    
    # Extract KB ID and Data Source ID from outputs
    KB_ID=$(aws cloudformation describe-stacks --stack-name BedrockKnowledgeBaseStack --query 'Stacks[0].Outputs[?OutputKey==`KnowledgeBaseId`].OutputValue' --output text 2>/dev/null || echo "")
    DATA_SOURCE_ID=$(aws cloudformation describe-stacks --stack-name BedrockKnowledgeBaseStack --query 'Stacks[0].Outputs[?OutputKey==`DataSourceId`].OutputValue' --output text 2>/dev/null || echo "")
    
    if [ -n "$KB_ID" ] && [ -n "$DATA_SOURCE_ID" ]; then
        log_info "Starting ingestion job for Knowledge Base: $KB_ID"
        INGESTION_JOB_ID=$(aws bedrock-agent start-ingestion-job \
            --knowledge-base-id "$KB_ID" \
            --data-source-id "$DATA_SOURCE_ID" \
            --query 'ingestionJob.ingestionJobId' \
            --output text)
        
        log_success "Ingestion job started with ID: $INGESTION_JOB_ID"
        log_info "You can check the status in the AWS Bedrock console"
    else
        log_warning "Could not retrieve Knowledge Base or Data Source ID. Please trigger ingestion manually."
    fi
}

# Prepare agent
prepare_agent() {
    log_info "Preparing Bedrock Agent..."
    
    AGENT_ID=$(aws cloudformation describe-stacks --stack-name BedrockAgentStack --query 'Stacks[0].Outputs[?OutputKey==`AgentId`].OutputValue' --output text 2>/dev/null || echo "")
    
    if [ -n "$AGENT_ID" ]; then
        log_info "Preparing agent: $AGENT_ID"
        aws bedrock-agent prepare-agent --agent-id "$AGENT_ID" > /dev/null
        log_success "Agent prepared successfully"
    else
        log_warning "Could not retrieve Agent ID. Please prepare the agent manually."
    fi
}

# Create test user in Cognito
create_test_user() {
    log_info "Creating test user in Cognito..."
    
    USER_POOL_ID=$(aws cloudformation describe-stacks --stack-name ApiGatewayStack --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' --output text 2>/dev/null || echo "")
    
    if [ -n "$USER_POOL_ID" ]; then
        # Create test user
        aws cognito-idp admin-create-user \
            --user-pool-id "$USER_POOL_ID" \
            --username testuser \
            --temporary-password "TempPass123!" \
            --message-action SUPPRESS \
            --user-attributes Name=email,Value=testuser@example.com > /dev/null 2>&1 && \
        log_success "Test user 'testuser' created successfully" || \
        log_warning "Test user may already exist or creation failed"
        
        log_info "Test user credentials:"
        log_info "  Username: testuser"
        log_info "  Temporary Password: TempPass123!"
        log_info "  Note: User must change password on first login"
    else
        log_warning "Could not retrieve User Pool ID. Please create test user manually."
    fi
}

# Display deployment summary
display_summary() {
    log_info "Deployment Summary"
    echo "=================================="
    
    # Extract key information
    AGENT_ID=$(aws cloudformation describe-stacks --stack-name BedrockAgentStack --query 'Stacks[0].Outputs[?OutputKey==`AgentId`].OutputValue' --output text 2>/dev/null || echo "N/A")
    AGENT_ALIAS_ID=$(aws cloudformation describe-stacks --stack-name BedrockAgentStack --query 'Stacks[0].Outputs[?OutputKey==`AgentAliasId`].OutputValue' --output text 2>/dev/null || echo "N/A")
    API_URL=$(aws cloudformation describe-stacks --stack-name ApiGatewayStack --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' --output text 2>/dev/null || echo "N/A")
    USER_POOL_ID=$(aws cloudformation describe-stacks --stack-name ApiGatewayStack --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' --output text 2>/dev/null || echo "N/A")
    
    echo "Agent ID: $AGENT_ID"
    echo "Agent Alias ID: $AGENT_ALIAS_ID"
    echo "API Gateway URL: $API_URL"
    echo "Cognito User Pool ID: $USER_POOL_ID"
    echo "=================================="
    
    log_success "Deployment completed successfully!"
    log_info "Next steps:"
    echo "1. Wait for Knowledge Base ingestion to complete"
    echo "2. Test the agent using the provided test script:"
    echo "   python3 scripts/test-agent.py --agent-id $AGENT_ID --agent-alias-id $AGENT_ALIAS_ID"
    echo "3. Access the API at: $API_URL"
    echo "4. Check deployment-outputs.json for detailed information"
}

# Main execution
main() {
    log_info "Starting AWS Bedrock Agent deployment..."
    
    check_aws_cli
    check_cdk
    check_bedrock_models
    install_dependencies
    build_project
    deploy_stacks
    get_stack_outputs
    trigger_kb_ingestion
    prepare_agent
    create_test_user
    display_summary
}

# Run main function
main "$@"