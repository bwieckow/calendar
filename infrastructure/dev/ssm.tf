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

resource "aws_ssm_parameter" "smtp_from_email" {
  name        = "/calendar/dev/smtp-from-email"
  description = "SMTP from email address for sending emails via Brevo"
  type        = "SecureString"
  value       = " "
  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "smtp_username" {
  name        = "/calendar/dev/smtp-username"
  description = "Brevo SMTP username (login email)"
  type        = "SecureString"
  value       = " "
  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "smtp_password" {
  name        = "/calendar/dev/smtp-password"
  description = "Brevo SMTP password (API key)"
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
