resource "aws_ssm_parameter" "google_credentials" {
  name        = "calendar-google-credentials-json"
  description = "Google service account credentials for accessing the Calendar API"
  type        = "SecureString"
  value       = " "
  lifecycle {
    ignore_changes = [value]
  }
}
