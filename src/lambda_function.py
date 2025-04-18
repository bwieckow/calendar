import os
import datetime
import boto3
import google.auth.transport.requests
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import json

SCOPES = ["https://www.googleapis.com/auth/calendar"]

def get_ssm_parameter(name):
    ssm_client = boto3.client('ssm', region_name='eu-west-1')
    parameter = ssm_client.get_parameter(
        Name=name,
        WithDecryption=True
    )
    return parameter['Parameter']['Value']

def put_ssm_parameter(name, value):
    ssm_client = boto3.client('ssm', region_name='eu-west-1')
    ssm_client.put_parameter(
        Name=name,
        Value=value,
        Type='String',
        Overwrite=True
    )

def authenticate():
    creds = None
    token_file = "/tmp/token.json"

    # Get client_secret.json from SSM Parameter Store
    client_secret_json = get_ssm_parameter('calendar-google-credentials-json')
    with open('/tmp/client_secret.json', 'w') as f:
        f.write(client_secret_json)

    # Get token.json from SSM Parameter Store
    token_json = get_ssm_parameter('calendar-token-json')
    with open(token_file, 'w') as f:
        f.write(token_json)

    # Load existing token if available
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    # If no valid credentials, perform authentication
    if not creds or not creds.valid:
        try:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(google.auth.transport.requests.Request())
                print("Token refreshed successfully.")
            else:
                raise Exception("No valid refresh token available.")
        except Exception as e:
            print(f"Error refreshing token: {str(e)}")
            flow = InstalledAppFlow.from_client_secrets_file("/tmp/client_secret.json", SCOPES)
            creds = flow.run_local_server(port=8080)
            print("Authenticated successfully.")

        # Save credentials for future use
        with open(token_file, "w") as token:
            token.write(creds.to_json())

        # Update token.json in SSM Parameter Store
        put_ssm_parameter('calendar-token-json', creds.to_json())

    return creds

def get_calendar_service():
    creds = authenticate()
    service = build('calendar', 'v3', credentials=creds)
    return service

def get_time_range_for_date(date):
    start_of_day = datetime.datetime.combine(date, datetime.time.min).isoformat() + 'Z'
    end_date = date + datetime.timedelta(days=90)  # 3 months later
    end_of_day = datetime.datetime.combine(end_date, datetime.time.max).isoformat() + 'Z'
    return start_of_day, end_of_day

def get_events_for_date(service, start_of_day, end_of_day):
    print(f'Getting events for date from {start_of_day} to {end_of_day}')
    events_result = service.events().list(
        calendarId="primary",
        timeMin=start_of_day,
        timeMax=end_of_day,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])
    print(f'Found {len(events)} events for the date')
    return events

def format_event(event):
    return {
        'id': event.get('id'),
        'summary': event.get('summary'),
        'start': event['start'],
        'end': event['end'],
        'description': event.get('description'),
        'number_of_attendees': len(event.get('attendees', []))
    }

def invite_to_event(service, event_id, email):
    event = service.events().get(calendarId="primary", eventId=event_id).execute()
    if 'attendees' not in event:
        event['attendees'] = []
    event['attendees'].append({'email': email})
    updated_event = service.events().update(calendarId="primary", eventId=event_id, body=event).execute()
    return updated_event

def handle_get_request(event, service):
    date_str = event.get('queryStringParameters', {}).get('date')
    if not date_str:
        print('Error: date query parameter is required')
        return {
            'statusCode': 400,
            'body': 'date query parameter is required'
        }
    
    try:
        date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        print('Error: Invalid date format. Use YYYY-MM-DD.')
        return {
            'statusCode': 400,
            'body': 'Invalid date format. Use YYYY-MM-DD.'
        }
    
    start_of_day, end_of_day = get_time_range_for_date(date)
    events = get_events_for_date(service, start_of_day, end_of_day)
    
    # Return the three nearest upcoming events with specified fields
    nearest_events = [format_event(event) for event in events[:3]]
    return {
        'statusCode': 200,
        'body': json.dumps(nearest_events)
    }

def handle_post_request(event, service):
    body = json.loads(event.get('body', '{}'))
    print(f'POST request body: {body}')
    
    # Extract event_id and email from the body
    additional_description = body.get('order', {}).get('additionalDescription', '')
    email = body.get('order', {}).get('buyer', {}).get('email', '')
    status = body.get('order', {}).get('status', '')
    
    # Extract event_id from additionalDescription
    event_id_prefix = 'event_id: '
    event_id = additional_description.split(event_id_prefix)[-1] if event_id_prefix in additional_description else None

    print(f'event_id: {event_id}, email: {email}, status: {status}')
    
    if not event_id or not email:
        print('Error: event_id and email are required in the request body')
        return {
            'statusCode': 400,
            'body': 'event_id and email are required in the request body'
        }
    
    if status != 'COMPLETED':
        print('Error: Order status must be COMPLETED to invite to event')
        return {
            'statusCode': 400,
            'body': 'Order status must be COMPLETED to invite to event'
        }
    
    try:
        updated_event = invite_to_event(service, event_id, email)
        print(f'Invitation sent: {format_event(updated_event)}')
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Invitation sent', 'event': format_event(updated_event)})
        }
    except Exception as e:
        print(f'Error inviting to event: {str(e)}')
        return {
            'statusCode': 500,
            'body': f'Error inviting to event: {str(e)}'
        }

def lambda_handler(event, context):
    try:
        service = get_calendar_service()
        
        http_method = event['requestContext']['http']['method']
        
        if http_method == 'GET':
            return handle_get_request(event, service)
        elif http_method == 'POST':
            return handle_post_request(event, service)
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