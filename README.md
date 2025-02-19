# Calendar Lambda Function

This project contains a Lambda function to interact with Google Calendar. It supports two types of requests:
- **GET**: Retrieve the nearest upcoming events for a given date.
- **POST**: Invite an email address to a specified event if the order status is `COMPLETED`.

## Prerequisites

- Python 3.7 or higher
- AWS CLI configured with appropriate permissions
- Virtualenv

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

## Running the Lambda Function Locally

You can run the Lambda function directly from the command line using the existing JSON files for event data.

### GET Request

Save the following JSON as `src/event_get.json`:

```json
{
    "requestContext": {
        "http": {
            "method": "GET"
        }
    },
    "queryStringParameters": {
        "date": "2025-01-14"
    }
}
```

Run the GET request:

```bash
python -c 'import json; from src.lambda_function import lambda_handler; event = json.load(open("src/event_get.json")); context = {}; response = lambda_handler(event, context); print(response)'
```

### POST Request

Save the following JSON as `src/event_post.json`:

```json
{
    "requestContext": {
        "http": {
            "method": "POST"
        }
    },
    "body": "{\"order\": {\"additionalDescription\": \"event_id: event_id_value\", \"buyer\": {\"email\": \"example@gmail.com\"}, \"status\": \"COMPLETED\"}}"
}
```

Run the POST request:

```bash
python -c 'import json; from src.lambda_function import lambda_handler; event = json.load(open("src/event_post.json")); context = {}; response = lambda_handler(event, context); print(response)'
```

## Grabbing `event_id_value`

To grab the `event_id_value` for a calendar event, you can use the GET request to list the events in your calendar. The response will include the `event_id` for each event.

1. **Run the GET request** as described above.
2. **Check the response** for the `event_id` of the event you want to invite attendees to.
3. **Use the `event_id`** in the `event_post.json` file for the POST request.
