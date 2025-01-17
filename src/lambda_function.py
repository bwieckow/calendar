import os
import datetime
import boto3
import google.auth
from googleapiclient.discovery import build
from google.oauth2 import service_account
import json

def get_ssm_parameter(name):
    ssm_client = boto3.client('ssm')
    parameter = ssm_client.get_parameter(
        Name=name,
        WithDecryption=True
    )
    return parameter['Parameter']['Value']

def get_google_credentials():
    if os.getenv('LOCAL'):
        with open(os.getenv('LOCAL_CREDENTIALS_PATH'), 'r') as f:
            google_credentials_json = f.read()
    else:
        google_credentials_json = get_ssm_parameter(os.environ['GOOGLE_CREDENTIALS_PARAM'])
    return google_credentials_json

def write_credentials_to_file(credentials_json):
    with open('/tmp/google-credentials.json', 'w') as f:
        f.write(credentials_json)

def get_calendar_service():
    creds = service_account.Credentials.from_service_account_file('/tmp/google-credentials.json')
    service = build('calendar', 'v3', credentials=creds)
    return service

def get_time_range_for_date(date):
    start_of_day = datetime.datetime.combine(date, datetime.time.min).isoformat() + 'Z'
    end_date = date + datetime.timedelta(days=90)  # 3 months later
    end_of_day = datetime.datetime.combine(end_date, datetime.time.max).isoformat() + 'Z'
    return start_of_day, end_of_day

def get_events_for_date(service, start_of_day, end_of_day, calendar_id):
    print(f'Getting events for date from {start_of_day} to {end_of_day}')
    events_result = service.events().list(
        calendarId=calendar_id,
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

def lambda_handler(event, context):
    google_credentials_json = get_google_credentials()
    write_credentials_to_file(google_credentials_json)
    service = get_calendar_service()
    
    calendar_id = get_ssm_parameter('calendar-id')
    
    date_str = event.get('queryStringParameters', {}).get('date')
    if not date_str:
        return {
            'statusCode': 400,
            'body': 'date query parameter is required'
        }
    
    try:
        date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return {
            'statusCode': 400,
            'body': 'Invalid date format. Use YYYY-MM-DD.'
        }
    
    start_of_day, end_of_day = get_time_range_for_date(date)
    events = get_events_for_date(service, start_of_day, end_of_day, calendar_id)
    
    # Return the three nearest upcoming events with specified fields
    nearest_events = [format_event(event) for event in events[:3]]
    return {
        'statusCode': 200,
        'body': json.dumps(nearest_events)
    }