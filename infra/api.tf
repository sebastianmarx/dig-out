# ------------------------------------------------------------------ HTTP API (/api/*, via CloudFront)
resource "aws_apigatewayv2_api" "http" {
  name          = "${local.prefix}-http"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_authorizer" "jwt" {
  api_id           = aws_apigatewayv2_api.http.id
  name             = "cognito"
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]

  jwt_configuration {
    audience = [aws_cognito_user_pool_client.web.id]
    issuer   = "https://${aws_cognito_user_pool.main.endpoint}"
  }
}

resource "aws_apigatewayv2_integration" "http" {
  api_id                 = aws_apigatewayv2_api.http.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.fn["http"].invoke_arn
  payload_format_version = "2.0"
}

locals {
  http_routes = {
    "POST /api/gate"                  = false # platform password, before any login
    "GET /api/game-data"              = true
    "GET /api/games"                  = true
    "POST /api/games"                 = true
    "POST /api/games/join"            = true
    "POST /api/games/{game_id}/leave" = true
    "POST /api/ws-ticket"             = true
  }
}

resource "aws_apigatewayv2_route" "http" {
  for_each           = local.http_routes
  api_id             = aws_apigatewayv2_api.http.id
  route_key          = each.key
  target             = "integrations/${aws_apigatewayv2_integration.http.id}"
  authorization_type = each.value ? "JWT" : "NONE"
  authorizer_id      = each.value ? aws_apigatewayv2_authorizer.jwt.id : null
}

resource "aws_apigatewayv2_stage" "http" {
  api_id      = aws_apigatewayv2_api.http.id
  name        = "$default"
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit = 40
    throttling_rate_limit  = 20
  }
}

resource "aws_lambda_permission" "http" {
  statement_id  = "AllowHttpApi"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.fn["http"].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}

# ------------------------------------------------------------- WebSocket API (game, ticket auth)
resource "aws_apigatewayv2_api" "ws" {
  name                       = "${local.prefix}-ws"
  protocol_type              = "WEBSOCKET"
  route_selection_expression = "$request.body.action"
}

locals {
  ws_routes = {
    "$connect"    = "ws_connect"
    "$disconnect" = "ws_disconnect"
    "$default"    = "ws_default"
  }
}

resource "aws_apigatewayv2_integration" "ws" {
  for_each           = local.ws_routes
  api_id             = aws_apigatewayv2_api.ws.id
  integration_type   = "AWS_PROXY"
  integration_uri    = aws_lambda_function.fn[each.value].invoke_arn
  integration_method = "POST"
}

resource "aws_apigatewayv2_route" "ws" {
  for_each  = local.ws_routes
  api_id    = aws_apigatewayv2_api.ws.id
  route_key = each.key
  target    = "integrations/${aws_apigatewayv2_integration.ws[each.key].id}"
}

resource "aws_apigatewayv2_stage" "ws" {
  api_id      = aws_apigatewayv2_api.ws.id
  name        = "prod"
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit = 50
    throttling_rate_limit  = 20
  }
}

resource "aws_lambda_permission" "ws" {
  for_each      = toset(values(local.ws_routes))
  statement_id  = "AllowWebSocketApi"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.fn[each.value].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.ws.execution_arn}/*/*"
}
