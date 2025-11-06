"""Calendar service for iCalendar operations."""
import os
import datetime
from urllib.request import urlopen
from icalendar import Calendar

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
    
    Args:
        calendar: iCalendar object
        start_of_day: Start datetime for filtering
        end_of_day: End datetime for filtering
        
    Returns:
        list: Sorted list of event components
    """
    print(f'Getting events for date from {start_of_day} to {end_of_day}')
    events = []
    
    for component in calendar.walk():
        if component.name == "VEVENT":
            event_start = component.get('dtstart').dt
            
            # Handle both date and datetime objects
            if isinstance(event_start, datetime.date) and not isinstance(event_start, datetime.datetime):
                event_start = datetime.datetime.combine(event_start, datetime.time.min)
            
            # Make timezone-naive for comparison
            if hasattr(event_start, 'tzinfo') and event_start.tzinfo:
                event_start = event_start.replace(tzinfo=None)
            
            if start_of_day <= event_start <= end_of_day:
                events.append(component)
    
    # Sort events by start time
    events.sort(key=lambda e: e.get('dtstart').dt)
    print(f'Found {len(events)} events for the date range')
    return events


def find_event_by_id(calendar, event_id):
    """
    Find a specific event in the calendar by its UID.
    
    Args:
        calendar: iCalendar object
        event_id: Event UID to search for
        
    Returns:
        Event component or None if not found
    """
    for component in calendar.walk():
        if component.name == "VEVENT" and str(component.get('uid')) == event_id:
            return component
    return None


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
    
    event_data = {
        'id': str(event.get('uid')),
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
