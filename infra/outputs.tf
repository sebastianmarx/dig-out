output "site_url" {
  value = "https://${local.use_custom_domain ? var.domain_name : aws_cloudfront_distribution.site.domain_name}"
}

output "distribution_id" {
  value = aws_cloudfront_distribution.site.id
}

output "site_bucket" {
  value = aws_s3_bucket.site.bucket
}

output "region" {
  value = var.region
}

output "user_pool_id" {
  value = aws_cognito_user_pool.main.id
}

output "user_pool_client_id" {
  value = aws_cognito_user_pool_client.web.id
}

output "ws_url" {
  value = aws_apigatewayv2_stage.ws.invoke_url
}

output "gate_hash_param" {
  value = local.gate_hash_param
}

output "table_name" {
  value = aws_dynamodb_table.main.name
}
