resource "aws_lambda_function" "calendar" {
  function_name = "calendar"
  role          = aws_iam_role.calendar.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.13" # Latest Python version supported by AWS Lambda

  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      GOOGLE_CREDENTIALS_PARAM = "calendar-google-credentials-json"
    }
  }
}

resource "aws_lambda_function_url" "calendar" {
  function_name      = aws_lambda_function.calendar.function_name
  authorization_type = "NONE"
}

output "lambda_function_arn" {
  value = aws_lambda_function.calendar.arn
}