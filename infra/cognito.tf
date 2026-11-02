# Player accounts. Sign-up is open but the pre sign-up Lambda requires the platform password,
# so the public Cognito API cannot be used to bypass the gate.
resource "aws_cognito_user_pool" "main" {
  name           = local.prefix
  user_pool_tier = "LITE"

  username_configuration {
    case_sensitive = false
  }

  password_policy {
    minimum_length                   = 10
    require_lowercase                = true
    require_uppercase                = true
    require_numbers                  = true
    require_symbols                  = false
    temporary_password_validity_days = 7
  }

  # No e-mail is collected: accounts are recovered by an admin.
  account_recovery_setting {
    recovery_mechanism {
      name     = "admin_only"
      priority = 1
    }
  }

  lambda_config {
    pre_sign_up = aws_lambda_function.fn["pre_signup"].arn
  }
}

resource "aws_cognito_user_pool_client" "web" {
  name                          = "${local.prefix}-web"
  user_pool_id                  = aws_cognito_user_pool.main.id
  generate_secret               = false
  explicit_auth_flows           = ["ALLOW_USER_PASSWORD_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"]
  prevent_user_existence_errors = "ENABLED"
  enable_token_revocation       = true
  access_token_validity         = 60
  id_token_validity             = 60
  refresh_token_validity        = 30

  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "days"
  }
}

resource "aws_lambda_permission" "cognito" {
  statement_id  = "AllowCognito"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.fn["pre_signup"].function_name
  principal     = "cognito-idp.amazonaws.com"
  source_arn    = aws_cognito_user_pool.main.arn
}
