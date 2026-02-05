"""AWS service utilities for parameter store access."""
import os
import boto3


def get_ssm_parameter(name, region='eu-west-1'):
    """
    Retrieve a parameter from AWS Systems Manager Parameter Store.
    
    Args:
        name (str): Parameter name to retrieve
        region (str): AWS region (default: eu-west-1)
        
    Returns:
        str: The parameter value
    """
    # Use AWS_PROFILE if set for local development
    aws_profile = os.getenv('AWS_PROFILE')
    session_kwargs = {'region_name': region}
    if aws_profile:
        session_kwargs['profile_name'] = aws_profile
        session = boto3.Session(**session_kwargs)
        ssm_client = session.client('ssm')
    else:
        ssm_client = boto3.client('ssm', region_name=region)
    
    parameter = ssm_client.get_parameter(
        Name=name,
        WithDecryption=True
    )
    return parameter['Parameter']['Value']
