"""Calendar service for iCalendar operations."""
import os
import datetime
from urllib.request import urlopen
from icalendar import Calendar
import recurring_ical_events

from utils.aws_services import get_ssm_parameter


def get_calendar_feed():
    """
    Fetch and parse iCalendar feed from Google Calendar.
    
    Returns:
        Calendar: Parsed iCalendar object
    """
    ICAL_URL_PARAM = os.getenv('ICAL_URL_PARAM', '/calendar/dev/ical-feed-url')
    ical_url = get_ssm_parameter(ICAL_URL_PARAM)
    
    print(f'Fetching calendar feed from URL')
    response = urlopen(ical_url)
    ical_data = response.read()
    
    calendar = Calendar.from_ical(ical_data)
    return calendar


def get_time_range_for_date(date):
    """
    Calculate time range from given date to 90 days later.
    
    Args:
        date: Starting date
        
    Returns:
        tuple: (start_of_day, end_of_day) datetime objects
    """
    start_of_day = datetime.datetime.combine(date, datetime.time.min)
    end_date = date + datetime.timedelta(days=90)  # 3 months later
    end_of_day = datetime.datetime.combine(end_date, datetime.time.max)
    return start_of_day, end_of_day


def get_events_for_date(calendar, start_of_day, end_of_day):
    """
    Extract events from calendar feed within date range.
    Includes recurring event instances.
    
    Args:
        calendar: iCalendar object
        start_of_day: Start datetime for filtering
        end_of_day: End datetime for filtering
        
    Returns:
        list: Sorted list of event components (including recurring instances)
    """
    print(f'Getting events for date from {start_of_day} to {end_of_day}')
    
    # Use recurring_ical_events to expand recurring events
    events = recurring_ical_events.of(calendar).between(start_of_day, end_of_day)
    
    # Sort events by start time
    events_list = list(events)
    events_list.sort(key=lambda e: e.get('dtstart').dt)
    
    print(f'Found {len(events_list)} events for the date range (including recurring instances)')
    return events_list


def find_event_by_id(calendar, event_id):
    """
    Find a specific event in the calendar by its UID.
    Supports recurring events with format: uid_YYYYMMDD
    
    Args:
        calendar: iCalendar object
        event_id: Event UID to search for (may include _YYYYMMDD suffix for recurring events)
        
    Returns:
        tuple: (Event component or None, recurrence_date or None)
    """
    # Check if this is a recurring event ID (contains _YYYYMMDD suffix)
    recurrence_date = None
    base_uid = event_id
    
    if '_' in event_id:
        parts = event_id.rsplit('_', 1)
        if len(parts) == 2 and len(parts[1]) == 8 and parts[1].isdigit():
            base_uid = parts[0]
            # Parse the date from YYYYMMDD format
            try:
                recurrence_date = datetime.datetime.strptime(parts[1], '%Y%m%d').date()
                print(f'Searching for recurring event with base UID: {base_uid}, recurrence date: {recurrence_date}')
            except ValueError:
                print(f'Invalid date format in event_id: {parts[1]}')
                pass
    
    # First, try to find the base event
    base_event = None
    for component in calendar.walk():
        if component.name == "VEVENT" and str(component.get('uid')) == base_uid:
            base_event = component
            break
    
    if not base_event:
        print(f'Base event with UID {base_uid} not found')
        return None, None
    
    # If this is a specific occurrence, we need to expand recurring events
    if recurrence_date:
        # Calculate a time range around the recurrence date
        start_of_day = datetime.datetime.combine(recurrence_date, datetime.time.min)
        end_of_day = datetime.datetime.combine(recurrence_date, datetime.time.max)
        
        # Expand recurring events for this specific date
        events = recurring_ical_events.of(calendar).between(start_of_day, end_of_day)
        
        # Find the specific occurrence matching both UID and date
        for event in events:
            if str(event.get('uid')) == base_uid:
                event_start = event.get('dtstart').dt
                # Convert to date if it's a datetime
                if isinstance(event_start, datetime.datetime):
                    event_date = event_start.date()
                else:
                    event_date = event_start
                
                if event_date == recurrence_date:
                    print(f'Found specific recurring event occurrence on {recurrence_date}')
                    return event, recurrence_date
        
        print(f'Specific occurrence on {recurrence_date} not found for event {base_uid}')
        return None, None
    
    # If no recurrence date, return the base event
    return base_event, None


def format_event(event, include_attendee_count=False, attendee_count=0):
    """
    Format iCalendar event for JSON response.
    
    Args:
        event: iCalendar event component
        include_attendee_count: Whether to include attendee count
        attendee_count: Number of attendees (if include_attendee_count is True)
        
    Returns:
        dict: Formatted event data
    """
    start = event.get('dtstart').dt
    end = event.get('dtend').dt
    
    # Convert to ISO format strings
    start_str = start.isoformat() if isinstance(start, datetime.datetime) else start.isoformat()
    end_str = end.isoformat() if isinstance(end, datetime.datetime) else end.isoformat()

    # Get base UID
    event_id = str(event.get('uid'))
    
    # Check for RECURRENCE-ID and append to ID if present
    recurrence_id = event.get('RECURRENCE-ID')
    if recurrence_id:
        recurrence_dt = recurrence_id.dt
        # Extract date in YYYYMMDD format
        if isinstance(recurrence_dt, datetime.datetime):
            recurrence_date = recurrence_dt.strftime('%Y%m%d')
        elif isinstance(recurrence_dt, datetime.date):
            recurrence_date = recurrence_dt.strftime('%Y%m%d')
        else:
            # Fallback: convert to string and extract date part
            recurrence_date = str(recurrence_dt).split()[0].replace('-', '')
        
        event_id = f"{event_id}_{recurrence_date}"
        print(f'Event ID with recurrence: {event_id}')
    
    event_data = {
        'id': event_id,
        'summary': str(event.get('summary', '')),
        'start': {'dateTime': start_str},
        'end': {'dateTime': end_str},
        'description': str(event.get('description', '')),
        'location': str(event.get('location', ''))
    }
    
    # Add attendee count if requested
    if include_attendee_count:
        event_data['number_of_attendees'] = attendee_count
    
    return event_data
