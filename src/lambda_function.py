"""
AWS Lambda function for Calendar Event Management.

This Lambda function handles:
- GET requests: Retrieve upcoming calendar events with attendee counts
- POST requests: Send calendar invitations via email and track participants

The function is organized into modular components:
- handlers/: Request handling logic
- services/: Business logic (calendar, email, DynamoDB)
- utils/: Utility functions (AWS services, validators)
"""
import sys
import os

# Add the src directory to the Python path for local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.calendar_service import get_calendar_feed
from handlers.request_handlers import handle_get_request, handle_post_request
from utils.validators import validate_api_key, validate_payu_signature


def lambda_handler(event, context):
    """
    Main Lambda handler function.
    
    Routes requests to appropriate handlers based on HTTP method:
    - GET: Retrieve calendar events
    - POST: Send calendar invitation
    
    Args:
        event (dict): Lambda event object from CloudFront
        context: Lambda context object
        
    Returns:
        dict: Response with statusCode and body
    """
    try:
        # Validate API key for all requests
        headers = event.get('headers', {})
        if not validate_api_key(headers):
            return {
                'statusCode': 403,
                'body': 'Forbidden: Invalid API key'
            }

        # Fetch calendar feed
        calendar = get_calendar_feed()
        
        # Route based on HTTP method
        http_method = event['requestContext']['http']['method']

        if http_method == 'GET':
            return handle_get_request(event, calendar)
            
        elif http_method == 'POST':
            # Validate PayU signature for POST requests
            body = event.get('body', '')
            # if not validate_payu_signature(headers, body):
            #     return {
            #         'statusCode': 403,
            #         'body': 'Forbidden: Invalid PayU signature'
            #     }
            return handle_post_request(event, calendar)
            
        else:
            print('Error: Method Not Allowed')
            return {
                'statusCode': 405,
                'body': 'Method Not Allowed'
            }
            
    except Exception as e:
        print(f'Error in lambda_handler: {str(e)}')
        return {
            'statusCode': 500,
            'body': f'Internal server error: {str(e)}'
        }
