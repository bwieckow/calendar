# Calendar Lambda Function

This project contains a Lambda function to interact with Google Calendar via iCalendar feeds. It supports two types of requests:
- **GET**: Retrieve the nearest upcoming events for a given date by parsing an iCalendar feed.
- **POST**: Send calendar invitation via email (AWS SES) to a specified email address when PayU order status is `COMPLETED`.

> **📚 For Developers**: See [ARCHITECTURE.md](src/ARCHITECTURE.md) for detailed code structure and module documentation.

## Architecture

The solution uses:
- **iCalendar Feed**: Reads events from Google Calendar's public/private iCalendar URL (no OAuth required)
- **AWS SES**: Sends calendar invitations (.ics files) via email
- **AWS Lambda**: Serverless function to handle API requests
- **AWS SSM Parameter Store**: Stores sensitive configuration (API keys, calendar feed URL)
- **AWS DynamoDB**: Tracks events and participant counts

## Prerequisites

- Python 3.13 or higher
- AWS CLI configured with appropriate permissions
- Terraform (for infrastructure deployment)
- Google Calendar with iCalendar feed URL
- Verified email address in AWS SES

## Setup

1. **Clone the repository**:
    ```sh
    git clone <repository-url>
    cd calendar
    ```

2. **Create and Activate a Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Configure AWS SSM Parameters**:
    Store the following parameters in AWS Systems Manager Parameter Store:
    - `calendar-ical-feed-url`: Your Google Calendar iCalendar feed URL (private URL from calendar settings)
    - `calendar-ses-from-email`: Verified sender email address for SES
    - `/ops-master/cloudfront/apikey`: API key for request authentication
    - `calendar-payu-second-key`: PayU second key for signature validation

5. **Get Your Google Calendar iCalendar URL**:
    - Open Google Calendar
    - Go to Settings → Select your calendar → Integrate calendar
    - Copy the "Secret address in iCal format" URL
    - Store this URL in SSM Parameter Store as `calendar-ical-feed-url`

6. **Verify Email in AWS SES**:
    - Go to AWS SES Console
    - Verify the email address you want to use as sender
    - If in sandbox mode, also verify recipient email addresses for testing

## Running the Lambda Function Locally

You can run the Lambda function directly from the command line using the existing JSON files for event data.

### GET Request

Retrieve upcoming events for a specific date. Save the following JSON as `src/event_get.json`:

```json
{
    "requestContext": {
        "http": {
            "method": "GET"
        }
    },
    "headers": {
        "x-api-key": "your-api-key-here"
    },
    "queryStringParameters": {
        "date": "2025-01-14"
    }
}
```

Run the GET request:

```bash
python -c 'import json; from src.lambda_function import lambda_handler; event = json.load(open("src/event_get.json")); context = {}; response = lambda_handler(event, context); print(json.dumps(response, indent=2))'
```

**Response Example**:
```json
{
    "statusCode": 200,
    "body": "[{\"id\": \"event-uid-123\", \"summary\": \"Meeting\", \"start\": {\"dateTime\": \"2025-01-14T10:00:00\"}, \"end\": {\"dateTime\": \"2025-01-14T11:00:00\"}, \"description\": \"Team meeting\", \"location\": \"Office\"}]"
}
```

### POST Request

Send a calendar invitation after successful PayU payment. Save the following JSON as `src/event_post.json`:

```json
{
    "requestContext": {
        "http": {
            "method": "POST"
        }
    },
    "headers": {
        "x-api-key": "your-api-key-here",
        "openpayu-signature": "signature=your-payu-signature;algorithm=MD5"
    },
    "body": "{\"order\": {\"additionalDescription\": \"event_id: event-uid-123\", \"buyer\": {\"email\": \"customer@example.com\"}, \"status\": \"COMPLETED\"}}"
}
```

Run the POST request:

```bash
python -c 'import json; from src.lambda_function import lambda_handler; event = json.load(open("src/event_post.json")); context = {}; response = lambda_handler(event, context); print(json.dumps(response, indent=2))'
```

**Response Example**:
```json
{
    "statusCode": 200,
    "body": "{\"message\": \"Invitation sent successfully\", \"event\": {...}, \"email\": \"customer@example.com\"}"
}
```

## Finding Event IDs

To find the `event_id` (UID) for a calendar event:

1. **Run the GET request** as described above with a date range that includes your event
2. **Check the response** for the `id` field of each event
3. **Use this `id`** in the PayU order's `additionalDescription` field as: `event_id: <event-uid>`

Example flow:
```bash
# 1. Get events
GET /calendar?date=2025-01-14

# 2. Response includes event IDs
[{"id": "abc123xyz", "summary": "Workshop", ...}]

# 3. Use event ID in PayU order
additionalDescription: "event_id: abc123xyz"
```

## Environment Variables

The Lambda function uses the following environment variables:

- `ICAL_URL_PARAM` (default: `calendar-ical-feed-url`): SSM parameter name for iCalendar feed URL
- `SES_FROM_EMAIL_PARAM` (default: `calendar-ses-from-email`): SSM parameter name for SES sender email
- `API_KEY_PARAM` (default: `/ops-master/cloudfront/apikey`): SSM parameter name for API key
- `SECOND_KEY_PARAM` (default: `calendar-payu-second-key`): SSM parameter name for PayU second key

## Deployment

Deploy the infrastructure using Terraform:

```bash
cd infrastructure/dev  # or infrastructure/prod
terraform init
terraform plan
terraform apply
```

## Security

- API requests are authenticated using `x-api-key` header
- POST requests (PayU webhooks) are validated using MD5 signature
- All sensitive data stored in AWS SSM Parameter Store with encryption
- SES enforces TLS for email delivery

## Limitations

- AWS SES sandbox mode limits: can only send to verified email addresses
- Request production access for SES to send to any email address
- iCalendar feed has slight delay (typically a few minutes) for reflecting calendar changes
- GET requests return maximum 3 nearest upcoming events within 90 days

## Troubleshooting

**"Event not found" error**:
- Verify the event ID matches the UID from the iCalendar feed
- Check that the event is within the 90-day range from the query date

**Email not received**:
- Verify sender email in AWS SES
- Check SES sending limits and sandbox restrictions
- Verify recipient email if in SES sandbox mode
- Check CloudWatch logs for delivery errors

**"Invalid API key" error**:
- Ensure `x-api-key` header matches the value in SSM Parameter Store
- Check the parameter name matches `API_KEY_PARAM` environment variable
