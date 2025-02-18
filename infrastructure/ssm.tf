resource "aws_ssm_parameter" "google_credentials" {
  name        = "calendar-google-credentials-json"
  description = "Google service account credentials for accessing the Calendar API"
  type        = "SecureString"
  value       = " "
  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "calendar_token" {
  name        = "calendar-token-json"
  description = "Google service account calendar ID for accessing the Calendar API"
  type        = "SecureString"
  value       = " "
  lifecycle {
    ignore_changes = [value]
  }
}
