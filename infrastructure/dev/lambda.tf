resource "aws_lambda_layer_version" "ical_layer" {
  provider = aws.virginia

  filename            = "../ical_lambda_layer/ical-layer.zip"
  source_code_hash    = filebase64sha256("../ical_lambda_layer/ical-layer.zip")
  layer_name          = "ical_layer"
  compatible_runtimes = ["python3.13"]
}

resource "aws_lambda_function" "calendar" {
  provider = aws.virginia

  function_name = "calendar-dev"
  role          = aws_iam_role.calendar.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.13" # Latest Python version supported by AWS Lambda

  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  layers = [aws_lambda_layer_version.ical_layer.arn]

  timeout = 15

  environment {
    variables = {
      ENVIRONMENT              = "dev"
      GOOGLE_CREDENTIALS_PARAM = "/calendar/dev/google-credentials-json"

      API_KEY_PARAM    = "/ops-master/cloudfront/dev/apikey"
      SECOND_KEY_PARAM = "/calendar/dev/payu-second-key"

      ICAL_URL_PARAM      = "/calendar/dev/ical-feed-url"
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.calendar_events.name
    }
  }
}

resource "aws_lambda_function_url" "calendar" {
  provider = aws.virginia

  function_name      = aws_lambda_function.calendar.function_name
  authorization_type = "AWS_IAM"
  cors {
    allow_origins = ["http://localhost:3000", "http://opsmaster-dev.s3-website-eu-west-1.amazonaws.com", "https://dev.ops-master.com"]
    allow_methods = ["GET", "POST"]
    allow_headers = ["*"]
  }
}

resource "aws_lambda_permission" "cloudfront_origin_access_control_invoke_function" {
  provider = aws.virginia

  statement_id  = "AllowCloudFrontServicePrincipalInvokeFunction"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.calendar.function_name
  principal     = "cloudfront.amazonaws.com"
  source_arn    = data.aws_cloudfront_distribution.opsmaster.arn
}

resource "aws_lambda_permission" "cloudfront_origin_access_control_invoke_function_url" {
  provider = aws.virginia

  statement_id  = "AllowCloudFrontServicePrincipal"
  action        = "lambda:InvokeFunctionUrl"
  function_name = aws_lambda_function.calendar.function_name
  principal     = "cloudfront.amazonaws.com"
  source_arn    = data.aws_cloudfront_distribution.opsmaster.arn
}
