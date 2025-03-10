resource "aws_lambda_layer_version" "calendar_dependencies" {
  filename            = "google_lambda_layer/google-layer.zip"
  source_code_hash    = filebase64sha256("google_lambda_layer/google-layer.zip")
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

  timeout = 15

  environment {
    variables = {
      GOOGLE_CREDENTIALS_PARAM = "calendar-google-credentials-json"
    }
  }
}

resource "aws_lambda_function_url" "calendar" {
  function_name      = aws_lambda_function.calendar.function_name
  authorization_type = "NONE"
  cors {
    allow_origins = ["http://localhost:3000", "http://opsmaster.s3-website-eu-west-1.amazonaws.com"]
    allow_methods = ["GET", "POST"]
    allow_headers = ["*"]
  }
}

output "lambda_function_arn" {
  value = aws_lambda_function.calendar.arn
}

### For Cloudfront

resource "aws_lambda_layer_version" "google_layer" {
  provider = aws.virginia

  filename            = "google_lambda_layer/google-layer.zip"
  source_code_hash    = filebase64sha256("google_lambda_layer/google-layer.zip")
  layer_name          = "google_layer"
  compatible_runtimes = ["python3.13"]
}

resource "aws_lambda_function" "calendar_2" {
  provider = aws.virginia

  function_name = "calendar"
  role          = aws_iam_role.calendar_2.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.13" # Latest Python version supported by AWS Lambda

  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  layers = [aws_lambda_layer_version.google_layer.arn]

  timeout = 15

  environment {
    variables = {
      GOOGLE_CREDENTIALS_PARAM = "calendar-google-credentials-json"
    }
  }
}

resource "aws_lambda_function_url" "calendar_2" {
  provider = aws.virginia

  function_name      = aws_lambda_function.calendar_2.function_name
  authorization_type = "NONE"
  cors {
    allow_origins = ["http://localhost:3000", "http://opsmaster.s3-website-eu-west-1.amazonaws.com"]
    allow_methods = ["GET", "POST"]
    allow_headers = ["*"]
  }
}
