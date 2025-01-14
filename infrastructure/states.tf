terraform {
  backend "s3" {
    bucket         = "codebazar-states"
    region         = "eu-west-1"
    key            = "states/opsmasters/calendar/terraform.tfstate"
    # dynamodb_table = "terraform-state-management"
  }
}
