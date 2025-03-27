resource "aws_cloudwatch_log_group" "calendar" {
  provider = aws.virginia

  name              = "/aws/lambda/${aws_lambda_function.calendar.function_name}"
  retention_in_days = 30
}
