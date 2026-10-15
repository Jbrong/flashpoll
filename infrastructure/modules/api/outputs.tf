output "api_endpoint" {
  value = aws_apigatewayv2_api.http.api_endpoint
}

output "api_domain" {
  description = "API Gateway hostname, for the CloudFront origin."
  value       = replace(aws_apigatewayv2_api.http.api_endpoint, "https://", "")
}

output "function_name" {
  value = aws_lambda_function.api.function_name
}
