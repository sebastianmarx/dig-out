variable "project" {
  type    = string
  default = "digout"
}

variable "env" {
  description = "Environment name (prod, dev, ...)."
  type        = string
  default     = "prod"
}

variable "region" {
  type    = string
  default = "eu-central-1"
}

variable "lambda_zip" {
  description = "Path to the backend deployment package built by scripts/deploy.py."
  type        = string
}

variable "domain_name" {
  description = "Custom domain for production; an empty value uses the CloudFront domain."
  type        = string
  default     = "dig-out.marxai.de"
}

variable "dns_zone_name" {
  description = "Existing public Route 53 zone containing the custom domain."
  type        = string
  default     = "marxai.de"
}

variable "alert_email" {
  description = "E-mail for error alarms and budget warnings (empty = no notifications)."
  type        = string
  default     = ""
}

variable "monthly_budget_usd" {
  type    = number
  default = 5
}

variable "log_retention_days" {
  type    = number
  default = 14
}
