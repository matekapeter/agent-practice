import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Main Lambda handler for Bedrock Agent Action Groups
    Routes requests to appropriate functions based on the operation
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract the action group, function, and parameters from the event
        agent = event.get('agent', {})
        action_group = event.get('actionGroup', '')
        function = event.get('function', '')
        parameters = event.get('parameters', [])
        
        # Convert parameters list to a dictionary for easier access
        params_dict = {}
        for param in parameters:
            if 'name' in param and 'value' in param:
                params_dict[param['name']] = param['value']
        
        logger.info(f"Action Group: {action_group}, Function: {function}, Parameters: {params_dict}")
        
        # Route to appropriate handler based on function name
        if function == 'get_user_profile':
            response = get_user_profile(params_dict)
        elif function == 'update_user_preferences':
            response = update_user_preferences(params_dict)
        elif function == 'search_products':
            response = search_products(params_dict)
        elif function == 'get_order_status':
            response = get_order_status(params_dict)
        elif function == 'schedule_appointment':
            response = schedule_appointment(params_dict)
        elif function == 'send_notification':
            response = send_notification(params_dict)
        elif function == 'get_weather_info':
            response = get_weather_info(params_dict)
        elif function == 'calculate_pricing':
            response = calculate_pricing(params_dict)
        else:
            response = {
                'success': False,
                'error': f'Unknown function: {function}'
            }
        
        # Format response for Bedrock Agent
        return {
            'response': {
                'actionGroup': action_group,
                'function': function,
                'functionResponse': {
                    'responseBody': {
                        'TEXT': {
                            'body': json.dumps(response)
                        }
                    }
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            'response': {
                'actionGroup': action_group,
                'function': function,
                'functionResponse': {
                    'responseBody': {
                        'TEXT': {
                            'body': json.dumps({
                                'success': False,
                                'error': str(e)
                            })
                        }
                    }
                }
            }
        }

def get_user_profile(params: Dict[str, str]) -> Dict[str, Any]:
    """
    Retrieve user profile information
    """
    user_id = params.get('user_id')
    
    if not user_id:
        return {'success': False, 'error': 'user_id is required'}
    
    # Mock user data - in production, this would query a database
    mock_users = {
        'user123': {
            'user_id': 'user123',
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'preferences': {
                'communication': 'email',
                'language': 'English',
                'timezone': 'America/New_York',
                'notifications': True
            },
            'subscription_tier': 'premium',
            'member_since': '2020-01-15'
        },
        'user456': {
            'user_id': 'user456',
            'name': 'Jane Smith',
            'email': 'jane.smith@example.com',
            'preferences': {
                'communication': 'sms',
                'language': 'English',
                'timezone': 'America/Los_Angeles',
                'notifications': False
            },
            'subscription_tier': 'basic',
            'member_since': '2021-03-20'
        }
    }
    
    user_profile = mock_users.get(user_id)
    if user_profile:
        return {
            'success': True,
            'profile': user_profile
        }
    else:
        return {
            'success': False,
            'error': 'User not found'
        }

def update_user_preferences(params: Dict[str, str]) -> Dict[str, Any]:
    """
    Update user preferences
    """
    user_id = params.get('user_id')
    preferences = params.get('preferences')
    
    if not user_id:
        return {'success': False, 'error': 'user_id is required'}
    
    # Mock preference update - in production, this would update a database
    logger.info(f"Updating preferences for user {user_id}: {preferences}")
    
    return {
        'success': True,
        'message': 'User preferences updated successfully',
        'user_id': user_id,
        'updated_at': datetime.now().isoformat()
    }

def search_products(params: Dict[str, str]) -> Dict[str, Any]:
    """
    Search for products based on criteria
    """
    query = params.get('query', '')
    category = params.get('category', 'all')
    max_price = params.get('max_price')
    
    # Mock product data
    all_products = [
        {
            'id': 'prod001',
            'name': 'Wireless Headphones',
            'category': 'electronics',
            'price': 199.99,
            'rating': 4.5,
            'in_stock': True,
            'description': 'High-quality wireless headphones with noise cancellation'
        },
        {
            'id': 'prod002',
            'name': 'Running Shoes',
            'category': 'sports',
            'price': 129.99,
            'rating': 4.3,
            'in_stock': True,
            'description': 'Comfortable running shoes for all terrains'
        },
        {
            'id': 'prod003',
            'name': 'Budget Wireless Earbuds',
            'category': 'electronics',
            'price': 149.99,
            'rating': 4.2,
            'in_stock': True,
            'description': 'Affordable wireless earbuds with good sound quality'
        },
        {
            'id': 'prod004',
            'name': 'Cotton T-Shirt',
            'category': 'clothing',
            'price': 24.99,
            'rating': 4.0,
            'in_stock': False,
            'description': 'Comfortable 100% cotton t-shirt'
        },
        {
            'id': 'prod005',
            'name': 'Programming Book',
            'category': 'books',
            'price': 59.99,
            'rating': 4.7,
            'in_stock': True,
            'description': 'Comprehensive guide to modern programming practices'
        }
    ]
    
    # Filter products based on criteria
    filtered_products = []
    
    for product in all_products:
        # Category filter
        if category != 'all' and product['category'] != category:
            continue
        
        # Price filter
        if max_price:
            try:
                max_price_float = float(max_price)
                if product['price'] > max_price_float:
                    continue
            except ValueError:
                pass
        
        # Query filter (search in name and description)
        if query:
            query_lower = query.lower()
            if (query_lower not in product['name'].lower() and 
                query_lower not in product['description'].lower()):
                continue
        
        filtered_products.append(product)
    
    return {
        'success': True,
        'results': filtered_products,
        'total_found': len(filtered_products),
        'search_criteria': {
            'query': query,
            'category': category,
            'max_price': max_price
        }
    }

def get_order_status(params: Dict[str, str]) -> Dict[str, Any]:
    """
    Get order status information
    """
    order_id = params.get('order_id')
    
    if not order_id:
        return {'success': False, 'error': 'order_id is required'}
    
    # Mock order data
    mock_orders = {
        'order001': {
            'order_id': 'order001',
            'status': 'shipped',
            'tracking_number': 'TRK123456789',
            'estimated_delivery': '2024-01-20',
            'items': [
                {'name': 'Wireless Headphones', 'quantity': 1, 'price': 199.99}
            ],
            'total': 199.99,
            'order_date': '2024-01-15'
        },
        'order002': {
            'order_id': 'order002',
            'status': 'processing',
            'tracking_number': None,
            'estimated_delivery': '2024-01-25',
            'items': [
                {'name': 'Running Shoes', 'quantity': 1, 'price': 129.99},
                {'name': 'Cotton T-Shirt', 'quantity': 2, 'price': 49.98}
            ],
            'total': 179.97,
            'order_date': '2024-01-18'
        }
    }
    
    order = mock_orders.get(order_id)
    if order:
        return {
            'success': True,
            'order': order
        }
    else:
        return {
            'success': False,
            'error': 'Order not found'
        }

def schedule_appointment(params: Dict[str, str]) -> Dict[str, Any]:
    """
    Schedule a new appointment
    """
    user_id = params.get('user_id')
    service_type = params.get('service_type')
    preferred_date = params.get('preferred_date')
    preferred_time = params.get('preferred_time', '10:00 AM')
    
    if not all([user_id, service_type, preferred_date]):
        return {
            'success': False,
            'error': 'user_id, service_type, and preferred_date are required'
        }
    
    # Generate a unique appointment ID
    appointment_id = f"apt_{uuid.uuid4().hex[:8]}"
    
    # Mock appointment scheduling
    appointment = {
        'appointment_id': appointment_id,
        'user_id': user_id,
        'service_type': service_type,
        'scheduled_date': preferred_date,
        'scheduled_time': preferred_time,
        'status': 'confirmed',
        'created_at': datetime.now().isoformat()
    }
    
    logger.info(f"Scheduled appointment: {appointment}")
    
    return {
        'success': True,
        'appointment': appointment,
        'message': f'Appointment scheduled successfully for {preferred_date} at {preferred_time}'
    }

def send_notification(params: Dict[str, str]) -> Dict[str, Any]:
    """
    Send a notification to a user
    """
    user_id = params.get('user_id')
    message = params.get('message')
    notification_type = params.get('type', 'email')
    
    if not all([user_id, message]):
        return {
            'success': False,
            'error': 'user_id and message are required'
        }
    
    # Generate a unique notification ID
    notification_id = f"notif_{uuid.uuid4().hex[:8]}"
    
    # Mock notification sending
    notification = {
        'notification_id': notification_id,
        'user_id': user_id,
        'type': notification_type,
        'message': message,
        'sent_at': datetime.now().isoformat(),
        'status': 'sent'
    }
    
    logger.info(f"Sent notification: {notification}")
    
    return {
        'success': True,
        'notification': notification,
        'message': f'Notification sent successfully via {notification_type}'
    }

def get_weather_info(params: Dict[str, str]) -> Dict[str, Any]:
    """
    Get weather information for a location
    """
    location = params.get('location')
    
    if not location:
        return {'success': False, 'error': 'location is required'}
    
    # Mock weather data
    mock_weather = {
        'success': True,
        'weather': {
            'location': location,
            'current': {
                'temperature': 22.5,
                'condition': 'Partly Cloudy',
                'humidity': 65,
                'wind_speed': 12.3
            },
            'forecast': [
                {
                    'day': 'Today',
                    'high': 25,
                    'low': 18,
                    'condition': 'Partly Cloudy'
                },
                {
                    'day': 'Tomorrow',
                    'high': 27,
                    'low': 20,
                    'condition': 'Sunny'
                },
                {
                    'day': 'Day After',
                    'high': 24,
                    'low': 17,
                    'condition': 'Rain'
                }
            ],
            'last_updated': datetime.now().isoformat()
        }
    }
    
    logger.info(f"Retrieved weather for {location}")
    return mock_weather

def calculate_pricing(params: Dict[str, str]) -> Dict[str, Any]:
    """
    Calculate pricing including discounts and taxes
    """
    try:
        base_price = float(params.get('base_price', 0))
        quantity = int(params.get('quantity', 1))
        discount_code = params.get('discount_code', '')
        user_tier = params.get('user_tier', 'basic')
        
        if base_price <= 0:
            return {'success': False, 'error': 'base_price must be greater than 0'}
        
        # Calculate subtotal
        subtotal = base_price * quantity
        
        # Apply discounts
        discount_percentage = 0
        discount_amount = 0
        
        # Discount codes
        discount_codes = {
            'SAVE10': 10,
            'SAVE20': 20,
            'WELCOME': 15,
            'BULK25': 25
        }
        
        if discount_code in discount_codes:
            discount_percentage = discount_codes[discount_code]
        
        # User tier discounts
        tier_discounts = {
            'basic': 0,
            'premium': 5,
            'enterprise': 10
        }
        
        tier_discount = tier_discounts.get(user_tier, 0)
        total_discount = max(discount_percentage, tier_discount)  # Use the better discount
        
        discount_amount = subtotal * (total_discount / 100)
        discounted_total = subtotal - discount_amount
        
        # Calculate tax (8.5% tax rate)
        tax_rate = 0.085
        tax_amount = discounted_total * tax_rate
        
        # Final total
        final_total = discounted_total + tax_amount
        
        pricing = {
            'base_price': base_price,
            'quantity': quantity,
            'subtotal': round(subtotal, 2),
            'discount_applied': total_discount,
            'discount_amount': round(discount_amount, 2),
            'tax_rate': tax_rate,
            'tax_amount': round(tax_amount, 2),
            'total': round(final_total, 2)
        }
        
        return {
            'success': True,
            'pricing': pricing
        }
        
    except (ValueError, TypeError) as e:
        return {
            'success': False,
            'error': f'Invalid pricing parameters: {str(e)}'
        }