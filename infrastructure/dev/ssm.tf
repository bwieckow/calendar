resource "aws_ssm_parameter" "google_credentials" {
  name        = "/calendar/dev/google-credentials-json"
  description = "Google service account credentials for accessing the Calendar API"
  type        = "SecureString"
  value       = " "
  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "ical_feed_url" {
  name        = "/calendar/dev/ical-feed-url"
  description = "iCal feed URL for the calendar"
  type        = "SecureString"
  value       = " "
  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "ses_from_email" {
  name        = "/calendar/dev/ses-from-email"
  description = "SES from email address for sending emails"
  type        = "SecureString"
  value       = "noreply@${aws_ses_domain_identity.calendar.domain}"
}

resource "aws_ssm_parameter" "calendar_token" {
  name        = "/calendar/dev/token-json"
  description = "Google service account calendar ID for accessing the Calendar API"
  type        = "SecureString"
  value       = " "
  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "payu_second_key" {
  name        = "/calendar/dev/payu-second-key"
  description = "PayU second key for validating PayU Signature"
  type        = "SecureString"
  value       = " "
  lifecycle {
    ignore_changes = [value]
  }
}
