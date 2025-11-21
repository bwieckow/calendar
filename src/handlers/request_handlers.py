"""Request handlers for GET and POST operations."""
import json
import datetime

from services.calendar_service import (
    get_time_range_for_date,
    get_events_for_date,
    find_event_by_id,
    format_event
)
from services.dynamodb_service import get_attendee_count, update_event_participants
from services.email_service import send_calendar_invitation


def handle_get_request(event, calendar):
    """
    Handle GET requests to retrieve upcoming events.
    
    Args:
        event (dict): Lambda event object
        calendar: iCalendar object
        
    Returns:
        dict: API Gateway response with status code and body
    """
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
    
    # Return the three nearest upcoming events with attendee count
    nearest_events = []
    for evt in events[:3]:
        # Get the formatted event first to get the correct event_id (with recurrence suffix if applicable)
        formatted_event = format_event(evt, include_attendee_count=False, attendee_count=0)
        event_id = formatted_event['id']
        attendee_count = get_attendee_count(event_id)
        formatted_event['number_of_attendees'] = attendee_count
        nearest_events.append(formatted_event)
    
    return {
        'statusCode': 200,
        'headers': {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        },
        'body': json.dumps(nearest_events)
    }


def handle_post_request(event, calendar):
    """
    Handle POST requests to send calendar invitations.
    
    Args:
        event (dict): Lambda event object
        calendar: iCalendar object
        
    Returns:
        dict: API Gateway response with status code and body
    """
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
    
    # Find the event in the calendar (may be a specific recurring occurrence)
    target_event, recurrence_date = find_event_by_id(calendar, event_id)
    
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
        
        # Send invitation email with event UID and recurrence date (if applicable)
        event_uid = str(target_event.get('uid'))
        send_calendar_invitation(
            email, event_summary, event_description, 
            event_start, event_end, event_location,
            event_uid, recurrence_date
        )
        
        # Update DynamoDB with event and participant tracking
        participant_count = update_event_participants(
            event_id, event_summary, event_start, event_end, email
        )
        
        print(f'Invitation sent to {email} for event: {event_summary}')
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Invitation sent successfully',
                'event': format_event(target_event),
                'email': email,
                'participant_count': participant_count
            })
        }
    except Exception as e:
        print(f'Error sending invitation: {str(e)}')
        return {
            'statusCode': 500,
            'body': f'Error sending invitation: {str(e)}'
        }
