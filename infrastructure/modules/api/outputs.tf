output "api_endpoint" {
  value = aws_lambda_function_url.api.function_url
}

output "api_domain" {
  description = "Function URL hostname, for the CloudFront origin."
  value       = trimsuffix(trimprefix(aws_lambda_function_url.api.function_url, "https://"), "/")
}

output "function_name" {
  value = aws_lambda_function.api.function_name
}
