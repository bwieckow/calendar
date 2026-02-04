# Add to infrastructure/dev/route53.tf or similar file

resource "aws_route53_record" "brevo_spf" {
  zone_id = data.aws_route53_zone.opsmaster.zone_id
  name    = "ops-master.com"
  type    = "TXT"
  ttl     = 300
  records = ["brevo-code:d6e4f26f46b51b24848e374b556ecef9"]
}

resource "aws_route53_record" "brevo_dkim1" {
  zone_id = data.aws_route53_zone.opsmaster.zone_id
  name    = "brevo1._domainkey.ops-master.com"
  type    = "CNAME"
  ttl     = 300
  records = ["b1.ops-master-com.dkim.brevo.com"]
}

resource "aws_route53_record" "brevo_dkim2" {
  zone_id = data.aws_route53_zone.opsmaster.zone_id
  name    = "brevo2._domainkey.ops-master.com"
  type    = "CNAME"
  ttl     = 300
  records = ["b2.ops-master-com.dkim.brevo.com"]
}

resource "aws_route53_record" "brevo_dmarc" {
  zone_id = data.aws_route53_zone.opsmaster.zone_id
  name    = "_dmarc.ops-master.com"
  type    = "TXT"
  ttl     = 300
  records = ["v=DMARC1; p=none; rua=mailto:rua@dmarc.brevo.com"]
}
