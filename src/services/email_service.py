"""Email service for sending calendar invitations via Brevo SMTP."""
import os
import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from icalendar import Calendar, Event as ICalEvent

from utils.aws_services import get_ssm_parameter


def create_ics_invitation(event_summary, event_description, event_start, event_end, 
                         event_location, organizer_email, attendee_email, event_uid, recurrence_date=None):
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
        event_uid (str): Original event UID from calendar
        recurrence_date: Date of specific occurrence (for recurring events)
        
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
    # Use the original event UID to maintain reference to the calendar event
    event.add('uid', event_uid)
    event.add('dtstamp', datetime.datetime.now())
    
    # Add RECURRENCE-ID for specific occurrences of recurring events
    if recurrence_date:
        # Use the event start time with the recurrence date
        if isinstance(event_start, datetime.datetime):
            recurrence_dt = datetime.datetime.combine(recurrence_date, event_start.time())
        else:
            recurrence_dt = recurrence_date
        event.add('recurrence-id', recurrence_dt)
        print(f'Added RECURRENCE-ID: {recurrence_dt} for specific event occurrence')
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
                            event_start, event_end, event_location, event_uid, recurrence_date=None):
    """
    Send calendar invitation via Brevo SMTP with .ics attachment.
    
    Args:
        to_email (str): Recipient email address
        event_summary (str): Event title
        event_description (str): Event description
        event_start: Event start datetime
        event_end: Event end datetime
        event_location (str): Event location
        event_uid (str): Original event UID from calendar
        recurrence_date: Date of specific occurrence (for recurring events)
        
    Returns:
        dict: Response with success status
        
    Raises:
        Exception: If email sending fails
    """
    # Get SMTP credentials from SSM
    SMTP_FROM_EMAIL_PARAM = os.getenv('SMTP_FROM_EMAIL_PARAM', '/calendar/dev/smtp-from-email')
    SMTP_SENDER_NAME_PARAM = os.getenv('SMTP_SENDER_NAME_PARAM', '/calendar/dev/smtp-sender-name')
    SMTP_USERNAME_PARAM = os.getenv('SMTP_USERNAME_PARAM', '/calendar/dev/smtp-username')
    SMTP_PASSWORD_PARAM = os.getenv('SMTP_PASSWORD_PARAM', '/calendar/dev/smtp-password')
    
    from_email = get_ssm_parameter(SMTP_FROM_EMAIL_PARAM)
    sender_name = "OpsMaster Trainings"
    smtp_username = get_ssm_parameter(SMTP_USERNAME_PARAM)
    smtp_password = get_ssm_parameter(SMTP_PASSWORD_PARAM)
    
    # Brevo SMTP settings
    smtp_server = 'smtp-relay.brevo.com'
    smtp_port = 587
    
    # Create the email message
    msg = MIMEMultipart('mixed')
    msg['Subject'] = f'Calendar Invitation: {event_summary}'
    msg['From'] = f'{sender_name} <{from_email}>'
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

Please do not reply to this email. If you have any questions, contact the event organizer.
    """
    
    msg_body = MIMEText(body_text, 'plain', 'utf-8')
    msg.attach(msg_body)
    
    # Create .ics attachment
    ics_content = create_ics_invitation(
        event_summary, event_description, event_start, event_end, 
        event_location, from_email, to_email, event_uid, recurrence_date
    )
    
    ics_attachment = MIMEBase('text', 'calendar', method='REQUEST', name='invite.ics')
    ics_attachment.set_payload(ics_content)
    encoders.encode_base64(ics_attachment)
    ics_attachment.add_header('Content-Disposition', 'attachment', filename='invite.ics')
    msg.attach(ics_attachment)
    
    # Send email via SMTP
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        print(f'Email sent successfully to {to_email} via Brevo SMTP')
        return {'success': True, 'message': 'Email sent via Brevo'}
    except Exception as e:
        print(f'Error sending email via Brevo: {str(e)}')
        raise
