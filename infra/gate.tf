# Platform gate: HMAC key for the gate cookie, shared by the gate Lambda (SSM) and CloudFront (KeyValueStore).
# The platform password hash itself is written by scripts/deploy.py, so it never enters the Terraform state.
resource "random_password" "gate_key" {
  length  = 48
  special = false
}

resource "random_password" "origin_verify" {
  length  = 40
  special = false
}

resource "aws_ssm_parameter" "gate_key" {
  name  = "/${var.project}/${var.env}/gate-key"
  type  = "SecureString"
  value = random_password.gate_key.result
}

resource "aws_cloudfront_key_value_store" "gate" {
  name    = "${local.prefix}-gate"
  comment = "Dig Out gate cookie key"
}

resource "aws_cloudfrontkeyvaluestore_key" "gate_key" {
  key_value_store_arn = aws_cloudfront_key_value_store.gate.arn
  key                 = "gate_key"
  value               = random_password.gate_key.result
}

resource "aws_cloudfront_function" "gate" {
  name    = "${local.prefix}-gate"
  runtime = "cloudfront-js-2.0"
  publish = true
  code = templatefile("${path.module}/cf_gate.js.tftpl", {
    kvs_id = element(split("/", aws_cloudfront_key_value_store.gate.arn), 1)
  })
  key_value_store_associations = [aws_cloudfront_key_value_store.gate.arn]
}
