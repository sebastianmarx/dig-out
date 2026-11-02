# One deployment package, six functions. Each function gets its own role with only what it needs.
locals {
  functions = {
    http          = { handler = "digout.aws.handlers.http", table = true, ws = true, scheduler = true, ssm = true }
    ws_connect    = { handler = "digout.aws.handlers.ws_connect", table = true, ws = false, scheduler = false, ssm = false }
    ws_disconnect = { handler = "digout.aws.handlers.ws_disconnect", table = true, ws = false, scheduler = false, ssm = false }
    ws_default    = { handler = "digout.aws.handlers.ws_default", table = true, ws = true, scheduler = true, ssm = false }
    timeout       = { handler = "digout.aws.handlers.timeout", table = true, ws = true, scheduler = true, ssm = false }
    pre_signup    = { handler = "digout.aws.handlers.pre_signup", table = false, ws = false, scheduler = false, ssm = true }
  }
  function_names       = { for k, _ in local.functions : k => "${local.prefix}-${replace(k, "_", "-")}" }
  timeout_function_arn = "arn:aws:lambda:${var.region}:${local.account_id}:function:${local.function_names["timeout"]}"
  gate_hash_param      = "/${var.project}/${var.env}/gate-hash" # written by scripts/deploy.py, never by Terraform
}

data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "fn" {
  for_each           = local.functions
  name               = local.function_names[each.key]
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

data "aws_iam_policy_document" "fn" {
  for_each = local.functions

  statement {
    sid       = "Logs"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.fn[each.key].arn}:*"]
  }

  dynamic "statement" {
    for_each = each.value.table ? [1] : []
    content {
      sid       = "Table"
      actions   = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:DeleteItem", "dynamodb:Query"]
      resources = [aws_dynamodb_table.main.arn, "${aws_dynamodb_table.main.arn}/index/*"]
    }
  }

  dynamic "statement" {
    for_each = each.value.ws ? [1] : []
    content {
      sid       = "PushToWebSockets"
      actions   = ["execute-api:ManageConnections"]
      resources = ["${aws_apigatewayv2_api.ws.execution_arn}/*"]
    }
  }

  dynamic "statement" {
    for_each = each.value.scheduler ? [1] : []
    content {
      sid       = "ScheduleTimeouts"
      actions   = ["scheduler:CreateSchedule"]
      resources = ["arn:aws:scheduler:${var.region}:${local.account_id}:schedule/${aws_scheduler_schedule_group.main.name}/*"]
    }
  }

  dynamic "statement" {
    for_each = each.value.scheduler ? [1] : []
    content {
      sid       = "PassSchedulerRole"
      actions   = ["iam:PassRole"]
      resources = [aws_iam_role.scheduler.arn]
    }
  }

  dynamic "statement" {
    for_each = each.value.ssm ? [1] : []
    content {
      sid     = "Secrets"
      actions = ["ssm:GetParameter"]
      resources = [
        "arn:aws:ssm:${var.region}:${local.account_id}:parameter${local.gate_hash_param}",
        aws_ssm_parameter.gate_key.arn,
      ]
    }
  }

  dynamic "statement" {
    for_each = each.value.ssm ? [1] : []
    content {
      sid       = "DecryptSecrets"
      actions   = ["kms:Decrypt"]
      resources = ["*"]
      condition {
        test     = "StringEquals"
        variable = "kms:ViaService"
        values   = ["ssm.${var.region}.amazonaws.com"]
      }
    }
  }
}

resource "aws_iam_role_policy" "fn" {
  for_each = local.functions
  name     = "least-privilege"
  role     = aws_iam_role.fn[each.key].id
  policy   = data.aws_iam_policy_document.fn[each.key].json
}

resource "aws_cloudwatch_log_group" "fn" {
  for_each          = local.functions
  name              = "/aws/lambda/${local.function_names[each.key]}"
  retention_in_days = var.log_retention_days
}

resource "aws_lambda_function" "fn" {
  for_each         = local.functions
  function_name    = local.function_names[each.key]
  role             = aws_iam_role.fn[each.key].arn
  handler          = each.value.handler
  runtime          = "python3.13"
  architectures    = ["arm64"]
  filename         = var.lambda_zip
  source_code_hash = filebase64sha256(var.lambda_zip)
  memory_size      = 512
  timeout          = 10

  environment {
    variables = {
      TABLE_NAME             = aws_dynamodb_table.main.name
      DIGOUT_GAME_DATA       = "/var/task/game-data"
      ORIGIN_VERIFY          = random_password.origin_verify.result
      GATE_HASH_PARAM        = local.gate_hash_param
      GATE_KEY_PARAM         = aws_ssm_parameter.gate_key.name
      WS_MANAGEMENT_ENDPOINT = "https://${aws_apigatewayv2_api.ws.id}.execute-api.${var.region}.amazonaws.com/${aws_apigatewayv2_stage.ws.name}"
      SCHEDULE_GROUP         = aws_scheduler_schedule_group.main.name
      TIMEOUT_FUNCTION_ARN   = local.timeout_function_arn
      SCHEDULER_ROLE_ARN     = aws_iam_role.scheduler.arn
    }
  }

  depends_on = [aws_iam_role_policy.fn, aws_cloudwatch_log_group.fn]
}
