locals {
  # Development workspaces keep their own CloudFront URL.
  use_custom_domain = var.env == "prod" && var.domain_name != ""
}

data "aws_route53_zone" "site" {
  count        = local.use_custom_domain ? 1 : 0
  name         = var.dns_zone_name
  private_zone = false
}

resource "aws_acm_certificate" "site" {
  count             = local.use_custom_domain ? 1 : 0
  provider          = aws.us_east_1
  domain_name       = var.domain_name
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_route53_record" "certificate_validation" {
  for_each = local.use_custom_domain ? {
    for option in aws_acm_certificate.site[0].domain_validation_options : option.domain_name => {
      name   = option.resource_record_name
      type   = option.resource_record_type
      record = option.resource_record_value
    }
  } : {}

  zone_id = data.aws_route53_zone.site[0].zone_id
  name    = each.value.name
  type    = each.value.type
  ttl     = 300
  records = [each.value.record]
}

resource "aws_acm_certificate_validation" "site" {
  count                   = local.use_custom_domain ? 1 : 0
  provider                = aws.us_east_1
  certificate_arn         = aws_acm_certificate.site[0].arn
  validation_record_fqdns = [for record in aws_route53_record.certificate_validation : record.fqdn]
}

resource "aws_route53_record" "site" {
  for_each = local.use_custom_domain ? toset(["A", "AAAA"]) : toset([])

  zone_id = data.aws_route53_zone.site[0].zone_id
  name    = var.domain_name
  type    = each.value

  alias {
    name                   = aws_cloudfront_distribution.site.domain_name
    zone_id                = aws_cloudfront_distribution.site.hosted_zone_id
    evaluate_target_health = false
  }
}
