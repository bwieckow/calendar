resource "aws_lambda_layer_version" "ical_layer" {
  provider = aws.virginia

  filename            = "../ical_lambda_layer/ical-layer.zip"
  source_code_hash    = filebase64sha256("../ical_lambda_layer/ical-layer.zip")
  layer_name          = "ical_layer"
  compatible_runtimes = ["python3.13"]
}

resource "aws_lambda_function" "calendar" {
  provider = aws.virginia

  function_name = "calendar"
  role          = aws_iam_role.calendar.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.13" # Latest Python version supported by AWS Lambda

  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  layers = [aws_lambda_layer_version.ical_layer.arn]

  timeout = 15

  environment {
    variables = {
      ENVIRONMENT              = "prod"
      GOOGLE_CREDENTIALS_PARAM = "/calendar/dev/google-credentials-json"
      TOKEN_JSON_PARAM         = "/calendar/dev/token-json"
      API_KEY_PARAM            = "/ops-master/cloudfront/apikey"
      SECOND_KEY_PARAM         = "/calendar/dev/payu-second-key"
    }
  }
}

resource "aws_lambda_function_url" "calendar" {
  provider = aws.virginia

  function_name      = aws_lambda_function.calendar.function_name
  authorization_type = "NONE"
  cors {
    allow_origins = ["http://localhost:3000", "http://opsmaster.s3-website-eu-west-1.amazonaws.com", "https://ops-master.com", "https://www.ops-master.com"]
    allow_methods = ["GET", "POST"]
    allow_headers = ["*"]
  }
}

resource "aws_lambda_permission" "cloudfront_origin_access_control" {
  provider = aws.virginia

  statement_id  = "AllowCloudFrontServicePrincipal"
  action        = "lambda:InvokeFunctionUrl"
  function_name = aws_lambda_function.calendar.function_name
  principal     = "cloudfront.amazonaws.com"
  source_arn    = data.aws_cloudfront_distribution.opsmaster.arn
}
