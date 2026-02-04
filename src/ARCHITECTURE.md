# Lambda Function Architecture

This document describes the refactored, modular architecture of the Calendar Lambda function.

## Directory Structure

```
src/
├── lambda_function.py          # Main entry point (orchestration layer)
├── handlers/
│   ├── __init__.py
│   └── request_handlers.py     # GET and POST request handlers
├── services/
│   ├── __init__.py
│   ├── calendar_service.py     # iCalendar operations
│   ├── dynamodb_service.py     # DynamoDB operations
│   └── email_service.py        # SES email operations
└── utils/
    ├── __init__.py
    ├── aws_services.py         # AWS SSM parameter store utilities
    └── validators.py           # API key and PayU signature validation
```

## Module Responsibilities

### `lambda_function.py`
**Purpose:** Main entry point and orchestration
- Routes requests to appropriate handlers
- Validates API keys
- Validates PayU signatures for POST requests
- Handles top-level error catching

### `handlers/request_handlers.py`
**Purpose:** HTTP request handling logic
- `handle_get_request()`: Process GET requests for calendar events
- `handle_post_request()`: Process POST requests to send invitations

### `services/calendar_service.py`
**Purpose:** iCalendar operations
- `get_calendar_feed()`: Fetch and parse iCalendar feed
- `get_time_range_for_date()`: Calculate date ranges
- `get_events_for_date()`: Filter events by date range
- `find_event_by_id()`: Find specific event by UID
- `format_event()`: Format event data for JSON response

### `services/dynamodb_service.py`
**Purpose:** DynamoDB operations
- `get_dynamodb_table()`: Get table resource
- `get_attendee_count()`: Get participant count for an event
- `update_event_participants()`: Create/update event with participants

### `services/email_service.py`
**Purpose:** Email operations via Brevo SMTP
- `create_ics_invitation()`: Generate .ics calendar file
- `send_calendar_invitation()`: Send email with calendar attachment via SMTP

### `utils/aws_services.py`
**Purpose:** AWS service utilities
- `get_ssm_parameter()`: Retrieve parameters from SSM Parameter Store

### `utils/validators.py`
**Purpose:** Request validation
- `validate_api_key()`: Validate x-api-key header
- `validate_payu_signature()`: Validate PayU webhook signatures

## Benefits of This Architecture

### 1. **Separation of Concerns**
Each module has a single, well-defined responsibility.

### 2. **Testability**
Functions can be unit tested in isolation without mocking the entire Lambda context.

### 3. **Maintainability**
Changes to one area (e.g., email formatting) don't affect other areas (e.g., DynamoDB logic).

### 4. **Reusability**
Services can be reused across different handlers or Lambda functions.

### 5. **Readability**
Main lambda_function.py is now ~70 lines instead of 450+, making the flow clear.

### 6. **Scalability**
Easy to add new handlers, services, or validators without cluttering existing code.

## Migration from Old Code

To switch to the new modular structure:

1. **Backup the old file:**
   ```bash
   mv src/lambda_function.py src/lambda_function_old.py
   ```

2. **Rename the new file:**
   ```bash
   mv src/lambda_function_new.py src/lambda_function.py
   ```

3. **Test locally:**
   ```bash
   python -c 'import json; from src.lambda_function import lambda_handler; event = json.load(open("src/ical_event_get.json")); context = {}; response = lambda_handler(event, context); print(json.dumps(response, indent=2))'
   ```

4. **Deploy to Lambda:**
   The entire `src/` directory should be packaged together, maintaining the folder structure.

## Packaging for Lambda

When creating the deployment package, ensure all modules are included:

```bash
cd src/
zip -r ../lambda_function.zip . -x "*.pyc" -x "__pycache__/*" -x "*.json"
```

Or use your existing deployment method (Terraform, SAM, etc.) ensuring the directory structure is preserved.

## Environment Variables

The function uses the following environment variables:
- `ICAL_URL_PARAM` (default: `/calendar/dev/ical-feed-url`)
- `SMTP_FROM_EMAIL_PARAM` (default: `/calendar/dev/smtp-from-email`)
- `SMTP_USERNAME_PARAM` (default: `/calendar/dev/smtp-username`)
- `SMTP_PASSWORD_PARAM` (default: `/calendar/dev/smtp-password`)
- `API_KEY_PARAM` (default: `/ops-master/cloudfront/apikey`)
- `SECOND_KEY_PARAM` (default: `/calendar/dev/payu-second-key`)
- `DYNAMODB_TABLE_NAME` (default: `calendar-events-dev`)

## Testing Individual Modules

You can now test individual components:

```python
# Test calendar service
from services.calendar_service import get_calendar_feed
calendar = get_calendar_feed()

# Test DynamoDB service
from services.dynamodb_service import get_attendee_count
count = get_attendee_count('event-id-123')

# Test validators
from utils.validators import validate_api_key
is_valid = validate_api_key({'x-api-key': 'test-key'})
```
