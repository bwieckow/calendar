"""AWS service utilities for parameter store access."""
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
    ssm_client = boto3.client('ssm', region_name=region)
    parameter = ssm_client.get_parameter(
        Name=name,
        WithDecryption=True
    )
    return parameter['Parameter']['Value']
