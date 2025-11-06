resource "aws_ses_email_identity" "calendar" {
  email = var.ses_from_email
}

resource "aws_ses_email_identity" "sandbox_recipients" {
  for_each = toset(local.ses_sandbox_recipient_emails)
  email    = each.value
}

resource "aws_ses_domain_identity" "calendar" {
  domain = "ops-master.com"
}

resource "aws_route53_record" "opsmaster_amazonses_verification_record" {
  zone_id = data.aws_route53_zone.opsmaster.zone_id
  name    = "_amazonses.ops-master.com"
  type    = "TXT"
  ttl     = "600"
  records = [aws_ses_domain_identity.calendar.verification_token]
}

resource "aws_ses_configuration_set" "calendar" {
  name = "${var.project_name}-${var.environment}-config-set"

  delivery_options {
    tls_policy = "Require"
  }
}

resource "aws_ses_event_destination" "cloudwatch" {
  name                   = "${var.project_name}-${var.environment}-cloudwatch"
  configuration_set_name = aws_ses_configuration_set.calendar.name
  enabled                = true
  matching_types         = ["send", "reject", "bounce", "complaint", "delivery"]

  cloudwatch_destination {
    default_value  = "default"
    dimension_name = "ses:configuration-set"
    value_source   = "messageTag"
  }
}
