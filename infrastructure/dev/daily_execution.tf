resource "aws_cloudwatch_event_rule" "calendar_daily" {
  provider = aws.virginia

  name                = "calendar_daily_dev"
  schedule_expression = "cron(0 9 * * ? *)"
}

resource "aws_cloudwatch_event_target" "check_at_rate_daily" {
  provider = aws.virginia

  rule = aws_cloudwatch_event_rule.calendar_daily.name
  arn  = aws_lambda_function.calendar.arn

  input = jsonencode({
    requestContext = {
      http = {
        method = "GET"
      }
    }
    queryStringParameters = {
      date = "2025-01-14"
    }
  })
}

resource "aws_lambda_permission" "calendar_daily" {
  provider = aws.virginia

  statement_id  = "AllowExecutionFromCWDaily"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.calendar.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.calendar_daily.arn
}
