import os
import datetime
import boto3
import google.auth
from googleapiclient.discovery import build
from google.oauth2 import service_account
import json

def get_google_credentials():
    ssm_client = boto3.client('ssm')
    parameter = ssm_client.get_parameter(
        Name=os.environ['GOOGLE_CREDENTIALS_PARAM'],
        WithDecryption=True
    )
    google_credentials_json = parameter['Parameter']['Value']
    return google_credentials_json

def write_credentials_to_file(credentials_json):
    with open('/tmp/google-credentials.json', 'w') as f:
        f.write(credentials_json)

def get_calendar_service():
    creds = service_account.Credentials.from_service_account_file('/tmp/google-credentials.json')
    service = build('calendar', 'v3', credentials=creds)
    return service

def get_upcoming_thursday():
    today = datetime.date.today()
    days_ahead = 3 - today.weekday()  # 3 is Thursday
    if days_ahead <= 0:
        days_ahead += 7
    next_thursday = today + datetime.timedelta(days_ahead)
    return next_thursday

def get_time_range_for_thursday(thursday):
    start_of_day = datetime.datetime.combine(thursday, datetime.time.min).isoformat() + 'Z'
    end_of_day = datetime.datetime.combine(thursday, datetime.time.max).isoformat() + 'Z'
    return start_of_day, end_of_day

def get_events_for_thursday(service, start_of_day, end_of_day):
    events_result = service.events().list(
        calendarId='primary',
        timeMin=start_of_day,
        timeMax=end_of_day,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])
    return events

def find_event_at_time(events, event_time):
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        if start == event_time:
            return event
    return None

def lambda_handler(event, context):
    google_credentials_json = get_google_credentials()
    write_credentials_to_file(google_credentials_json)
    service = get_calendar_service()
    next_thursday = get_upcoming_thursday()
    start_of_day, end_of_day = get_time_range_for_thursday(next_thursday)
    events = get_events_for_thursday(service, start_of_day, end_of_day)
    
    event_time = event.get('queryStringParameters', {}).get('event_time')
    if event_time:
        event_details = find_event_at_time(events, event_time)
        if event_details:
            return {
                'statusCode': 200,
                'body': json.dumps(event_details)
            }
        else:
            return {
                'statusCode': 404,
                'body': 'Event not found'
            }
    else:
        return {
            'statusCode': 400,
            'body': 'event_time query parameter is required'
        }