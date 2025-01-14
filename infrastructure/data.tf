data "aws_caller_identity" "current" {}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "../src"
  output_path = "lambda_function.zip"
}

data "archive_file" "google_lambda_layer" {
  type        = "zip"
  source_dir  = "./google_lambda_layer/python"
  output_path = "google-layer.zip"
}
