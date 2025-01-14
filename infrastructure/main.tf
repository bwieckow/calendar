resource "aws_lambda_layer_version" "calendar_dependencies" {
  filename            = data.archive_file.google_lambda_layer.output_path
  source_code_hash    = data.archive_file.google_lambda_layer.output_base64sha256
  layer_name          = "calendar_dependencies"
  compatible_runtimes = ["python3.13"]
}

resource "aws_lambda_function" "calendar" {
  function_name = "calendar"
  role          = aws_iam_role.calendar.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.13" # Latest Python version supported by AWS Lambda

  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  layers = [aws_lambda_layer_version.calendar_dependencies.arn]

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