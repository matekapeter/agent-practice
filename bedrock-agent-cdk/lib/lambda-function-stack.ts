import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as logs from 'aws-cdk-lib/aws-logs';
import { Construct } from 'constructs';

export class LambdaFunctionStack extends cdk.Stack {
  public readonly actionGroupFunctionArn: string;
  public readonly actionGroupFunction: lambda.Function;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Create CloudWatch Log Group for Lambda function
    const logGroup = new logs.LogGroup(this, 'ActionGroupFunctionLogGroup', {
      logGroupName: `/aws/lambda/bedrock-agent-action-group`,
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // Create Lambda function for Bedrock Agent action groups
    this.actionGroupFunction = new lambda.Function(this, 'ActionGroupFunction', {
      functionName: 'bedrock-agent-action-group',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'index.lambda_handler',
      code: lambda.Code.fromInline(`
import json
import boto3
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses')

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Main Lambda handler for Bedrock Agent action groups.
    Processes different action group functions based on the event.
    """
    try:
        logger.info(f"Received event: {json.dumps(event, default=str)}")
        
        # Extract function information from the event
        agent = event.get('agent', {})
        action_group = event.get('actionGroup', '')
        function_name = event.get('function', '')
        parameters = event.get('parameters', [])
        
        # Convert parameters list to dictionary
        params_dict = {}
        for param in parameters:
            params_dict[param['name']] = param['value']
        
        logger.info(f"Function: {function_name}, Parameters: {params_dict}")
        
        # Route to appropriate function based on function name
        if function_name == 'get_user_profile':
            result = get_user_profile(params_dict)
        elif function_name == 'update_user_preferences':
            result = update_user_preferences(params_dict)
        elif function_name == 'search_products':
            result = search_products(params_dict)
        elif function_name == 'get_order_status':
            result = get_order_status(params_dict)
        elif function_name == 'schedule_appointment':
            result = schedule_appointment(params_dict)
        elif function_name == 'send_notification':
            result = send_notification(params_dict)
        elif function_name == 'get_weather_info':
            result = get_weather_info(params_dict)
        elif function_name == 'calculate_pricing':
            result = calculate_pricing(params_dict)
        else:
            result = {"error": f"Unknown function: {function_name}"}
        
        # Format response for Bedrock Agent
        response = {
            "actionGroup": action_group,
            "function": function_name,
            "functionResponse": {
                "responseBody": {
                    "TEXT": {
                        "body": json.dumps(result)
                    }
                }
            }
        }
        
        logger.info(f"Response: {json.dumps(response, default=str)}")
        return response
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        error_response = {
            "actionGroup": action_group,
            "function": function_name,
            "functionResponse": {
                "responseBody": {
                    "TEXT": {
                        "body": json.dumps({"error": str(e)})
                    }
                }
            }
        }
        return error_response

def get_user_profile(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get user profile information."""
    user_id = params.get('user_id')
    
    if not user_id:
        return {"error": "user_id parameter is required"}
    
    # Mock user profile data
    user_profiles = {
        "user123": {
            "user_id": "user123",
            "name": "John Doe",
            "email": "john.doe@example.com",
            "preferences": {
                "communication": "email",
                "language": "en",
                "timezone": "UTC-5"
            },
            "subscription_tier": "premium",
            "member_since": "2022-01-15"
        },
        "user456": {
            "user_id": "user456",
            "name": "Jane Smith",
            "email": "jane.smith@example.com",
            "preferences": {
                "communication": "sms",
                "language": "en",
                "timezone": "UTC-8"
            },
            "subscription_tier": "basic",
            "member_since": "2023-03-20"
        }
    }
    
    profile = user_profiles.get(user_id)
    if profile:
        return {"success": True, "profile": profile}
    else:
        return {"success": False, "message": "User profile not found"}

def update_user_preferences(params: Dict[str, Any]) -> Dict[str, Any]:
    """Update user preferences."""
    user_id = params.get('user_id')
    preferences = params.get('preferences', {})
    
    if not user_id:
        return {"error": "user_id parameter is required"}
    
    # Mock preference update
    updated_preferences = {
        "communication": preferences.get('communication', 'email'),
        "language": preferences.get('language', 'en'),
        "timezone": preferences.get('timezone', 'UTC'),
        "notifications": preferences.get('notifications', True)
    }
    
    return {
        "success": True,
        "message": "Preferences updated successfully",
        "updated_preferences": updated_preferences
    }

def search_products(params: Dict[str, Any]) -> Dict[str, Any]:
    """Search for products based on criteria."""
    query = params.get('query', '')
    category = params.get('category', 'all')
    max_price = params.get('max_price', 1000)
    
    # Mock product data
    products = [
        {
            "id": "prod001",
            "name": "Wireless Headphones",
            "category": "electronics",
            "price": 199.99,
            "rating": 4.5,
            "in_stock": True
        },
        {
            "id": "prod002",
            "name": "Smart Watch",
            "category": "electronics",
            "price": 299.99,
            "rating": 4.3,
            "in_stock": True
        },
        {
            "id": "prod003",
            "name": "Running Shoes",
            "category": "sports",
            "price": 129.99,
            "rating": 4.7,
            "in_stock": False
        }
    ]
    
    # Filter products based on criteria
    filtered_products = []
    for product in products:
        if (category == 'all' or product['category'] == category) and \
           product['price'] <= float(max_price) and \
           (not query or query.lower() in product['name'].lower()):
            filtered_products.append(product)
    
    return {
        "success": True,
        "query": query,
        "category": category,
        "max_price": max_price,
        "results": filtered_products,
        "total_found": len(filtered_products)
    }

def get_order_status(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get order status information."""
    order_id = params.get('order_id')
    
    if not order_id:
        return {"error": "order_id parameter is required"}
    
    # Mock order data
    orders = {
        "ORD001": {
            "order_id": "ORD001",
            "status": "shipped",
            "tracking_number": "TRK123456789",
            "estimated_delivery": "2024-01-15",
            "items": [
                {"name": "Wireless Headphones", "quantity": 1, "price": 199.99}
            ],
            "total": 199.99
        },
        "ORD002": {
            "order_id": "ORD002",
            "status": "processing",
            "tracking_number": None,
            "estimated_delivery": "2024-01-18",
            "items": [
                {"name": "Smart Watch", "quantity": 1, "price": 299.99}
            ],
            "total": 299.99
        }
    }
    
    order = orders.get(order_id)
    if order:
        return {"success": True, "order": order}
    else:
        return {"success": False, "message": "Order not found"}

def schedule_appointment(params: Dict[str, Any]) -> Dict[str, Any]:
    """Schedule an appointment."""
    user_id = params.get('user_id')
    service_type = params.get('service_type')
    preferred_date = params.get('preferred_date')
    preferred_time = params.get('preferred_time')
    
    if not all([user_id, service_type, preferred_date]):
        return {"error": "user_id, service_type, and preferred_date are required"}
    
    # Mock appointment scheduling
    appointment_id = f"APT{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    return {
        "success": True,
        "message": "Appointment scheduled successfully",
        "appointment": {
            "appointment_id": appointment_id,
            "user_id": user_id,
            "service_type": service_type,
            "scheduled_date": preferred_date,
            "scheduled_time": preferred_time or "10:00 AM",
            "status": "confirmed"
        }
    }

def send_notification(params: Dict[str, Any]) -> Dict[str, Any]:
    """Send a notification to the user."""
    user_id = params.get('user_id')
    message = params.get('message')
    notification_type = params.get('type', 'email')
    
    if not all([user_id, message]):
        return {"error": "user_id and message are required"}
    
    # Mock notification sending
    notification_id = f"NOT{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    return {
        "success": True,
        "message": "Notification sent successfully",
        "notification": {
            "notification_id": notification_id,
            "user_id": user_id,
            "type": notification_type,
            "message": message,
            "sent_at": datetime.now().isoformat(),
            "status": "delivered"
        }
    }

def get_weather_info(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get weather information for a location."""
    location = params.get('location')
    
    if not location:
        return {"error": "location parameter is required"}
    
    # Mock weather data
    weather_data = {
        "location": location,
        "current": {
            "temperature": 72,
            "condition": "Partly Cloudy",
            "humidity": 65,
            "wind_speed": 8
        },
        "forecast": [
            {"day": "Today", "high": 75, "low": 60, "condition": "Sunny"},
            {"day": "Tomorrow", "high": 78, "low": 62, "condition": "Cloudy"},
            {"day": "Day After", "high": 73, "low": 58, "condition": "Rain"}
        ],
        "last_updated": datetime.now().isoformat()
    }
    
    return {"success": True, "weather": weather_data}

def calculate_pricing(params: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate pricing for a service or product."""
    base_price = float(params.get('base_price', 0))
    quantity = int(params.get('quantity', 1))
    discount_code = params.get('discount_code', '')
    user_tier = params.get('user_tier', 'basic')
    
    if base_price <= 0:
        return {"error": "base_price must be greater than 0"}
    
    # Calculate pricing
    subtotal = base_price * quantity
    
    # Apply tier discount
    tier_discounts = {
        'basic': 0.0,
        'premium': 0.1,
        'enterprise': 0.15
    }
    tier_discount = tier_discounts.get(user_tier, 0.0)
    
    # Apply discount code
    code_discounts = {
        'SAVE10': 0.1,
        'SAVE20': 0.2,
        'WELCOME': 0.15
    }
    code_discount = code_discounts.get(discount_code.upper(), 0.0)
    
    # Calculate total discount
    total_discount = max(tier_discount, code_discount)  # Use higher discount
    discount_amount = subtotal * total_discount
    
    # Calculate tax (assuming 8.5% tax rate)
    tax_rate = 0.085
    tax_amount = (subtotal - discount_amount) * tax_rate
    
    total = subtotal - discount_amount + tax_amount
    
    return {
        "success": True,
        "pricing": {
            "base_price": base_price,
            "quantity": quantity,
            "subtotal": round(subtotal, 2),
            "discount_applied": total_discount,
            "discount_amount": round(discount_amount, 2),
            "tax_rate": tax_rate,
            "tax_amount": round(tax_amount, 2),
            "total": round(total, 2)
        }
    }
      `),
      timeout: cdk.Duration.minutes(5),
      memorySize: 256,
      environment: {
        'LOG_LEVEL': 'INFO',
      },
      logGroup: logGroup,
    });

    // Add IAM permissions for the Lambda function
    this.actionGroupFunction.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          'dynamodb:GetItem',
          'dynamodb:PutItem',
          'dynamodb:UpdateItem',
          'dynamodb:Query',
          'dynamodb:Scan',
        ],
        resources: ['*'], // In production, restrict to specific table ARNs
      })
    );

    this.actionGroupFunction.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          'ses:SendEmail',
          'ses:SendRawEmail',
        ],
        resources: ['*'], // In production, restrict to specific SES resources
      })
    );

    // Grant Bedrock permission to invoke the Lambda function
    this.actionGroupFunction.addPermission('BedrockInvokePermission', {
      principal: new iam.ServicePrincipal('bedrock.amazonaws.com'),
      action: 'lambda:InvokeFunction',
    });

    // Store function ARN for use in other stacks
    this.actionGroupFunctionArn = this.actionGroupFunction.functionArn;

    // Export values for cross-stack references
    new cdk.CfnOutput(this, 'ActionGroupFunctionArn', {
      value: this.actionGroupFunctionArn,
      description: 'ARN of the Lambda function for Bedrock Agent action groups',
      exportName: `${this.stackName}-ActionGroupFunctionArn`,
    });

    new cdk.CfnOutput(this, 'ActionGroupFunctionName', {
      value: this.actionGroupFunction.functionName,
      description: 'Name of the Lambda function for Bedrock Agent action groups',
      exportName: `${this.stackName}-ActionGroupFunctionName`,
    });

    // Tag resources
    cdk.Tags.of(this).add('Component', 'ActionGroups');
    cdk.Tags.of(this).add('Purpose', 'BusinessLogic');
  }
}