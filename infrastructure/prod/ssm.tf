# OLD
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

resource "aws_ssm_parameter" "payu_second_key" {
  name        = "calendar-payu-second-key"
  description = "PayU second key for validating PayU Signature"
  type        = "SecureString"
  value       = " "
  lifecycle {
    ignore_changes = [value]
  }
}

# NEW
resource "aws_ssm_parameter" "google_credentials_json" {
  name        = "/calendar/prod/google-credentials-json"
  description = "Google service account credentials for accessing the Calendar API"
  type        = "SecureString"
  value       = " "
  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "calendar_token_json" {
  name        = "/calendar/prod/token-json"
  description = "Google service account calendar ID for accessing the Calendar API"
  type        = "SecureString"
  value       = " "
  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "payu_second_key_new" {
  name        = "/calendar/prod/payu-second-key"
  description = "PayU second key for validating PayU Signature"
  type        = "SecureString"
  value       = " "
  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "ical_feed_url" {
  name        = "/calendar/prod/ical-feed-url"
  description = "iCal feed URL for the calendar"
  type        = "SecureString"
  value       = " "
  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "smtp_from_email" {
  name        = "/calendar/prod/smtp-from-email"
  description = "SMTP from email address for sending emails via Brevo"
  type        = "SecureString"
  value       = " "
  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "smtp_username" {
  name        = "/calendar/prod/smtp-username"
  description = "Brevo SMTP username (login email)"
  type        = "SecureString"
  value       = " "
  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "smtp_password" {
  name        = "/calendar/prod/smtp-password"
  description = "Brevo SMTP password (API key)"
  type        = "SecureString"
  value       = " "
  lifecycle {
    ignore_changes = [value]
  }
}
