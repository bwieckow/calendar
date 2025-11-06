resource "aws_dynamodb_table" "calendar_events" {
  name         = "calendar-events-dev"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "event_id"

  attribute {
    name = "event_id"
    type = "S"
  }
}
