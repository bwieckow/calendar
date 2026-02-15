### Deleted from terraform state as we have only single hosted zone for both prod and dev environments. 
### We will manage the records manually for now, as there are only few of them and they are not expected to change frequently. 
### If we need to manage them with terraform in the future, we can always add them back.

# resource "aws_route53_record" "brevo_spf" {
#   zone_id = data.aws_route53_zone.opsmaster.zone_id
#   name    = "ops-master.com"
#   type    = "TXT"
#   ttl     = 300
#   records = ["brevo-code:d6e4f26f46b51b24848e374b556ecef9"]
# }

# resource "aws_route53_record" "brevo_dkim1" {
#   zone_id = data.aws_route53_zone.opsmaster.zone_id
#   name    = "brevo1._domainkey.ops-master.com"
#   type    = "CNAME"
#   ttl     = 300
#   records = ["b1.ops-master-com.dkim.brevo.com"]
# }

# resource "aws_route53_record" "brevo_dkim2" {
#   zone_id = data.aws_route53_zone.opsmaster.zone_id
#   name    = "brevo2._domainkey.ops-master.com"
#   type    = "CNAME"
#   ttl     = 300
#   records = ["b2.ops-master-com.dkim.brevo.com"]
# }

# resource "aws_route53_record" "brevo_dmarc" {
#   zone_id = data.aws_route53_zone.opsmaster.zone_id
#   name    = "_dmarc.ops-master.com"
#   type    = "TXT"
#   ttl     = 300
#   records = ["v=DMARC1; p=none; rua=mailto:rua@dmarc.brevo.com"]
# }
