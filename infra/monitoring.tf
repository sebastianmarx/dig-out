# Error alarms and a cost budget – only when an alert e-mail is configured.
locals {
  alerts = var.alert_email != ""
}

resource "aws_sns_topic" "alerts" {
  count = local.alerts ? 1 : 0
  name  = "${local.prefix}-alerts"
}

resource "aws_sns_topic_subscription" "email" {
  count     = local.alerts ? 1 : 0
  topic_arn = aws_sns_topic.alerts[0].arn
  protocol  = "email"
  endpoint  = var.alert_email
}

resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  for_each            = local.alerts ? local.functions : {}
  alarm_name          = "${local.function_names[each.key]}-errors"
  namespace           = "AWS/Lambda"
  metric_name         = "Errors"
  dimensions          = { FunctionName = local.function_names[each.key] }
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts[0].arn]
}

resource "aws_budgets_budget" "monthly" {
  count        = local.alerts ? 1 : 0
  name         = "${local.prefix}-monthly"
  budget_type  = "COST"
  limit_amount = tostring(var.monthly_budget_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.alert_email]
  }
}
