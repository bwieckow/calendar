"""Email service for sending calendar invitations via AWS SES."""
import os
import datetime
import boto3
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from icalendar import Calendar, Event as ICalEvent

from utils.aws_services import get_ssm_parameter


def create_ics_invitation(event_summary, event_description, event_start, event_end, 
                         event_location, organizer_email, attendee_email):
    """
    Create an .ics calendar invitation file.
    
    Args:
        event_summary (str): Event title
        event_description (str): Event description
        event_start: Event start datetime
        event_end: Event end datetime
        event_location (str): Event location
        organizer_email (str): Organizer email address
        attendee_email (str): Attendee email address
        
    Returns:
        bytes: iCalendar data in bytes
    """
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


def send_calendar_invitation(to_email, event_summary, event_description, 
                            event_start, event_end, event_location):
    """
    Send calendar invitation via AWS SES with .ics attachment.
    
    Args:
        to_email (str): Recipient email address
        event_summary (str): Event title
        event_description (str): Event description
        event_start: Event start datetime
        event_end: Event end datetime
        event_location (str): Event location
        
    Returns:
        dict: SES response
        
    Raises:
        Exception: If email sending fails
    """
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
