variable "aws_region" {
  description = "Region for the API, Lambda and DynamoDB."
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name, used in resource names and tags."
  type        = string
  default     = "prod"
}

variable "domain_name" {
  description = "Apex domain served by CloudFront. Must have a public Route 53 hosted zone in this account."
  type        = string
  default     = "flashpoll.dev"
}

variable "include_www" {
  description = "Also serve www.<domain>, redirecting it to the apex."
  type        = bool
  default     = true
}

variable "lambda_zip_path" {
  description = "Path to the API deployment package built by scripts/build_lambda.sh."
  type        = string
  default     = "../backend/dist/lambda.zip"
}

variable "api_throttle_rate" {
  description = "Steady-state requests/second allowed through API Gateway (account-wide guard until WAF lands in Phase 3)."
  type        = number
  default     = 50
}

variable "api_throttle_burst" {
  description = "Burst request allowance for API Gateway."
  type        = number
  default     = 100
}

variable "log_retention_days" {
  description = "CloudWatch log retention for the API and Lambda."
  type        = number
  default     = 14
}

variable "table_deletion_protection" {
  description = "Protect the DynamoDB tables from accidental deletion. Set false before a deliberate destroy."
  type        = bool
  default     = true
}

variable "budget_alert_email" {
  description = "If set, creates a monthly AWS budget that emails this address at 80% and 100%."
  type        = string
  default     = ""
}

variable "monthly_budget_usd" {
  description = "Monthly budget amount for the alert above."
  type        = number
  default     = 10
}
