"""DynamoDB service for event and participant tracking."""
import os
import datetime
import boto3

from utils.aws_services import get_ssm_parameter


def get_dynamodb_table():
    """
    Get DynamoDB table resource.
    
    Returns:
        boto3.Table: DynamoDB table resource
    """
    DYNAMODB_TABLE_NAME = os.getenv('DYNAMODB_TABLE_NAME', 'calendar-events-dev')
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
    return dynamodb.Table(DYNAMODB_TABLE_NAME)


def get_attendee_count(event_id):
    """
    Get the number of attendees for an event from DynamoDB.
    
    Args:
        event_id (str): Event UID
        
    Returns:
        int: Number of attendees (0 if event not found or on error)
    """
    try:
        table = get_dynamodb_table()
        response = table.get_item(Key={'event_id': event_id})
        
        if 'Item' in response:
            count = response['Item'].get('participant_count', 0)
            # Convert Decimal to int for JSON serialization
            return int(count) if count else 0
        else:
            return 0
    except Exception as e:
        print(f'Error getting attendee count from DynamoDB for event {event_id}: {str(e)}')
        return 0


def update_event_participants(event_id, event_summary, event_start, event_end, participant_email):
    """
    Check if event exists in DynamoDB and update participant count.
    Creates new entry if event doesn't exist.
    
    Args:
        event_id (str): Event UID
        event_summary (str): Event title
        event_start: Event start datetime
        event_end: Event end datetime
        participant_email (str): Email of participant to add
        
    Returns:
        int: Updated participant count
        
    Raises:
        Exception: If DynamoDB operation fails
    """
    table = get_dynamodb_table()
    
    try:
        # Try to get the existing event
        response = table.get_item(Key={'event_id': event_id})
        
        if 'Item' in response:
            # Event exists, increment participant count
            current_count = response['Item'].get('participant_count', 0)
            participants = response['Item'].get('participants', [])
            
            # Convert Decimal to int for proper arithmetic
            current_count = int(current_count) if current_count else 0
            
            # Add new participant if not already in the list
            if participant_email not in participants:
                participants.append(participant_email)
                new_count = current_count + 1
            else:
                new_count = current_count
                print(f'Participant {participant_email} already registered for event {event_id}')
            
            # Update the event
            table.update_item(
                Key={'event_id': event_id},
                UpdateExpression='SET participant_count = :count, participants = :participants, last_updated = :timestamp',
                ExpressionAttributeValues={
                    ':count': new_count,
                    ':participants': participants,
                    ':timestamp': datetime.datetime.now().isoformat()
                }
            )
            print(f'Updated event {event_id}. Participant count: {new_count}')
            return new_count
        else:
            # Event doesn't exist, create new entry
            event_start_str = event_start.isoformat() if isinstance(event_start, datetime.datetime) else str(event_start)
            event_end_str = event_end.isoformat() if isinstance(event_end, datetime.datetime) else str(event_end)
            
            table.put_item(
                Item={
                    'event_id': event_id,
                    'event_summary': event_summary,
                    'event_start': event_start_str,
                    'event_end': event_end_str,
                    'participant_count': 1,
                    'participants': [participant_email],
                    'created_at': datetime.datetime.now().isoformat(),
                    'last_updated': datetime.datetime.now().isoformat()
                }
            )
            print(f'Created new event {event_id} in DynamoDB with first participant')
            return 1
            
    except Exception as e:
        print(f'Error updating DynamoDB: {str(e)}')
        raise
