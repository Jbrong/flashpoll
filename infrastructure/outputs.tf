output "site_url" {
  value = "https://${var.domain_name}"
}

output "site_bucket" {
  description = "S3 bucket the frontend build is uploaded to."
  value       = module.site.bucket
}

output "cloudfront_distribution_id" {
  description = "Used to invalidate the CDN cache after a frontend deploy."
  value       = module.site.distribution_id
}

output "cloudfront_domain" {
  value = module.site.distribution_domain
}

output "api_endpoint" {
  description = "Direct Lambda function URL. Requests here are rejected without the CloudFront origin secret."
  value       = module.api.api_endpoint
}

output "lambda_function_name" {
  value = module.api.function_name
}

output "polls_table" {
  value = module.data.polls_table.name
}

output "votes_table" {
  value = module.data.votes_table.name
}
