"""Validation utilities for API key and PayU signatures."""
import os
import hashlib

from utils.aws_services import get_ssm_parameter


def validate_api_key(headers):
    """
    Validate the API key from request headers.
    
    Args:
        headers (dict): Request headers
        
    Returns:
        bool: True if API key is valid, False otherwise
    """
    api_key = headers.get('x-api-key')
    API_KEY_PARAM = os.getenv('API_KEY_PARAM', '/ops-master/cloudfront/dev/apikey')
    expected_api_key = get_ssm_parameter(API_KEY_PARAM)
    
    if api_key != expected_api_key:
        print('Error: Invalid API key')
        return False
    return True


def validate_payu_signature(headers, body):
    """
    Validates the PayU signature of an incoming POST notification.
    Follows the process described in the PayU documentation.
    
    Args:
        headers (dict): Request headers
        body (str): Request body as string
        
    Returns:
        bool: True if signature is valid, False otherwise
    """
    signature_header = headers.get('openpayu-signature')
    if not signature_header:
        print('Error: Missing openpayu-signature header')
        return False

    # Extract the signature part from the header
    try:
        signature = next(
            part.split('=')[1] 
            for part in signature_header.split(';') 
            if part.startswith('signature=')
        )
    except (IndexError, StopIteration):
        print('Error: Invalid openpayu-signature format')
        return False
    
    print(f'PayU signature: {signature}')

    if not signature:
        print('Error: Missing PayU signature header')
        return False

    SECOND_KEY_PARAM = os.getenv('SECOND_KEY_PARAM', 'calendar-payu-second-key')
    second_key = get_ssm_parameter(SECOND_KEY_PARAM)
    concatenated_string = f"{body}{second_key}"

    # Calculate the expected signature using MD5
    expected_signature = hashlib.md5(concatenated_string.encode('utf-8')).hexdigest()

    # Compare the provided signature with the expected signature
    if signature != expected_signature:
        print(f'Error: Invalid PayU signature. Expected: {expected_signature}, Received: {signature}')
        return False
    
    print('PayU signature is valid')
    return True
