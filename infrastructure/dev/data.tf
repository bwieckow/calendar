data "aws_caller_identity" "current" {}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "../../src"
  output_path = "lambda_function.zip"
}

data "aws_route53_zone" "opsmaster" {
  name         = "ops-master.com"
  private_zone = false
}

# data "aws_ssm_parameter" "cloudfront_distribution_id" {
#   name = "/ops-master/cloudfront/distribution_id"
# }

# data "aws_cloudfront_distribution" "opsmaster" {
#   id = data.aws_ssm_parameter.cloudfront_distribution_id.value
# }
