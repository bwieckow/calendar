import os
import datetime
import boto3
import json
import hashlib
from urllib.request import urlopen
from icalendar import Calendar, Event as ICalEvent
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def get_ssm_parameter(name):
    ssm_client = boto3.client('ssm', region_name='eu-west-1')
    parameter = ssm_client.get_parameter(
        Name=name,
        WithDecryption=True
    )
    return parameter['Parameter']['Value']

def get_calendar_feed():
    """Fetch and parse iCalendar feed from Google Calendar"""
    ICAL_URL_PARAM = os.getenv('ICAL_URL_PARAM', '/calendar/dev/ical-feed-url')
    ical_url = get_ssm_parameter(ICAL_URL_PARAM)
    
    print(f'Fetching calendar feed from URL')
    response = urlopen(ical_url)
    ical_data = response.read()
    
    calendar = Calendar.from_ical(ical_data)
    return calendar

def get_time_range_for_date(date):
    start_of_day = datetime.datetime.combine(date, datetime.time.min)
    end_date = date + datetime.timedelta(days=90)  # 3 months later
    end_of_day = datetime.datetime.combine(end_date, datetime.time.max)
    return start_of_day, end_of_day

def get_events_for_date(calendar, start_of_day, end_of_day):
    """Extract events from calendar feed within date range"""
    print(f'Getting events for date from {start_of_day} to {end_of_day}')
    events = []
    
    for component in calendar.walk():
        if component.name == "VEVENT":
            event_start = component.get('dtstart').dt
            
            # Handle both date and datetime objects
            if isinstance(event_start, datetime.date) and not isinstance(event_start, datetime.datetime):
                event_start = datetime.datetime.combine(event_start, datetime.time.min)
            
            # Make timezone-naive for comparison
            if event_start.tzinfo:
                event_start = event_start.replace(tzinfo=None)
            
            if start_of_day <= event_start <= end_of_day:
                events.append(component)
    
    # Sort events by start time
    events.sort(key=lambda e: e.get('dtstart').dt)
    print(f'Found {len(events)} events for the date range')
    return events

def format_event(event):
    """Format iCalendar event for JSON response"""
    start = event.get('dtstart').dt
    end = event.get('dtend').dt
    
    # Convert to ISO format strings
    start_str = start.isoformat() if isinstance(start, datetime.datetime) else start.isoformat()
    end_str = end.isoformat() if isinstance(end, datetime.datetime) else end.isoformat()
    
    return {
        'id': str(event.get('uid')),
        'summary': str(event.get('summary', '')),
        'start': {'dateTime': start_str},
        'end': {'dateTime': end_str},
        'description': str(event.get('description', '')),
        'location': str(event.get('location', ''))
    }

def create_ics_invitation(event_summary, event_description, event_start, event_end, event_location, organizer_email, attendee_email):
    """Create an .ics calendar invitation file"""
    cal = Calendar()
    cal.add('prodid', '-//Calendar Booking System//EN')
    cal.add('version', '2.0')
    cal.add('method', 'REQUEST')
    
    event = ICalEvent()
    event.add('summary', event_summary)
    event.add('description', event_description)
    event.add('dtstart', event_start)
    event.add('dtend', event_end)
    event.add('location', event_location)
    event.add('uid', f'{hash(attendee_email + str(event_start))}@calendar-booking')
    event.add('dtstamp', datetime.datetime.now())
    event.add('status', 'CONFIRMED')
    
    # Add organizer
    event.add('organizer', f'mailto:{organizer_email}')
    
    # Add attendee
    event.add('attendee', f'mailto:{attendee_email}', parameters={
        'CUTYPE': 'INDIVIDUAL',
        'ROLE': 'REQ-PARTICIPANT',
        'PARTSTAT': 'NEEDS-ACTION',
        'RSVP': 'TRUE'
    })
    
    cal.add_component(event)
    return cal.to_ical()

def send_calendar_invitation_email(to_email, event_summary, event_description, event_start, event_end, event_location):
    """Send calendar invitation via AWS SES with .ics attachment"""
    SES_FROM_EMAIL_PARAM = os.getenv('SES_FROM_EMAIL_PARAM', '/calendar/dev/ses-from-email')
    from_email = get_ssm_parameter(SES_FROM_EMAIL_PARAM)
    
    ses_client = boto3.client('ses', region_name='eu-west-1')
    
    # Create the email message
    msg = MIMEMultipart('mixed')
    msg['Subject'] = f'Calendar Invitation: {event_summary}'
    msg['From'] = from_email
    msg['To'] = to_email
    
    # Email body
    body_text = f"""
You have been invited to the following event:

Event: {event_summary}
Date: {event_start.strftime('%Y-%m-%d %H:%M')} - {event_end.strftime('%Y-%m-%d %H:%M')}
Location: {event_location}

Description:
{event_description}

This invitation has been added as a calendar attachment. Please accept or decline using your calendar application.
    """
    
    msg_body = MIMEText(body_text, 'plain', 'utf-8')
    msg.attach(msg_body)
    
    # Create .ics attachment
    ics_content = create_ics_invitation(
        event_summary, event_description, event_start, event_end, 
        event_location, from_email, to_email
    )
    
    ics_attachment = MIMEBase('text', 'calendar', method='REQUEST', name='invite.ics')
    ics_attachment.set_payload(ics_content)
    encoders.encode_base64(ics_attachment)
    ics_attachment.add_header('Content-Disposition', 'attachment', filename='invite.ics')
    msg.attach(ics_attachment)
    
    # Send email
    try:
        response = ses_client.send_raw_email(
            Source=from_email,
            Destinations=[to_email],
            RawMessage={'Data': msg.as_string()}
        )
        print(f'Email sent successfully. Message ID: {response["MessageId"]}')
        return response
    except Exception as e:
        print(f'Error sending email: {str(e)}')
        raise

def handle_get_request(event, calendar):
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
    events = get_events_for_date(calendar, start_of_day, end_of_day)
    
    # Return the three nearest upcoming events with specified fields
    nearest_events = [format_event(evt) for evt in events[:3]]
    return {
        'statusCode': 200,
        'body': json.dumps(nearest_events)
    }

def handle_post_request(event, calendar):
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
    
    # Find the event in the calendar
    target_event = None
    for component in calendar.walk():
        if component.name == "VEVENT" and str(component.get('uid')) == event_id:
            target_event = component
            break
    
    if not target_event:
        print(f'Error: Event with ID {event_id} not found')
        return {
            'statusCode': 404,
            'body': f'Event with ID {event_id} not found'
        }
    
    try:
        # Extract event details
        event_summary = str(target_event.get('summary', 'Event'))
        event_description = str(target_event.get('description', ''))
        event_start = target_event.get('dtstart').dt
        event_end = target_event.get('dtend').dt
        event_location = str(target_event.get('location', ''))
        
        # Convert date to datetime if needed
        if isinstance(event_start, datetime.date) and not isinstance(event_start, datetime.datetime):
            event_start = datetime.datetime.combine(event_start, datetime.time(9, 0))
        if isinstance(event_end, datetime.date) and not isinstance(event_end, datetime.datetime):
            event_end = datetime.datetime.combine(event_end, datetime.time(17, 0))
        
        # Send invitation email
        send_calendar_invitation_email(
            email, event_summary, event_description, 
            event_start, event_end, event_location
        )
        
        print(f'Invitation sent to {email} for event: {event_summary}')
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Invitation sent successfully',
                'event': format_event(target_event),
                'email': email
            })
        }
    except Exception as e:
        print(f'Error sending invitation: {str(e)}')
        return {
            'statusCode': 500,
            'body': f'Error sending invitation: {str(e)}'
        }

def validate_api_key(headers):
    api_key = headers.get('x-api-key')
    API_KEY_PARAM = os.getenv('API_KEY_PARAM', '/ops-master/cloudfront/apikey')
    expected_api_key = get_ssm_parameter(API_KEY_PARAM)
    if api_key != expected_api_key:
        print('Error: Invalid API key')
        return False
    return True

def validate_payu_signature(headers, body):
    """
    Validates the PayU signature of an incoming POST notification.
    Follows the process described in the PayU documentation.
    """
    signature_header = headers.get('openpayu-signature')
    if not signature_header:
        print('Error: Missing openpayu-signature header')
        return False

    # Extract the signature part from the header
    try:
        signature = next(part.split('=')[1] for part in signature_header.split(';') if part.startswith('signature='))
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

def lambda_handler(event, context):
    try:
        headers = event.get('headers', {})
        if not validate_api_key(headers):
            return {
                'statusCode': 403,
                'body': 'Forbidden: Invalid API key'
            }

        calendar = get_calendar_feed()
        http_method = event['requestContext']['http']['method']

        if http_method == 'GET':
            return handle_get_request(event, calendar)
        elif http_method == 'POST':
            body = event.get('body', '')
            if not validate_payu_signature(headers, body):
                return {
                    'statusCode': 403,
                    'body': 'Forbidden: Invalid PayU signature'
                }
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