resource "aws_cloudwatch_log_group" "calendar" {
  provider = aws.virginia

  name              = "/aws/lambda/${aws_lambda_function.calendar.function_name}"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_metric_filter" "token_expired_filter" {
  provider = aws.virginia

  name           = "TokenExpiredFilter"
  log_group_name = aws_cloudwatch_log_group.calendar.name

  pattern = "\"Token has been expired or revoked.\""

  metric_transformation {
    name      = "TokenExpiredCount"
    namespace = "CalendarApp"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "token_expired_alarm" {
  provider = aws.virginia

  alarm_name          = "TokenExpiredAlarm"
  alarm_description   = "Alarm when the token expiration message appears in logs."
  metric_name         = aws_cloudwatch_log_metric_filter.token_expired_filter.metric_transformation[0].name
  namespace           = aws_cloudwatch_log_metric_filter.token_expired_filter.metric_transformation[0].namespace
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  alarm_actions = [
    aws_sns_topic.token_expired_alarm_topic.arn
  ]
}

resource "aws_sns_topic" "token_expired_alarm_topic" {
  provider = aws.virginia

  name = "TokenExpiredAlarmTopic"
}

resource "aws_sns_topic_subscription" "email_subscription" {
  provider = aws.virginia

  topic_arn = aws_sns_topic.token_expired_alarm_topic.arn
  protocol  = "email"
  endpoint  = "bar.wieckowski@gmail.com"
}
