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

variable "log_retention_days" {
  description = "CloudWatch log retention for the Lambda."
  type        = number
  default     = 7
}

variable "dynamodb_billing_mode" {
  description = "PROVISIONED stays inside DynamoDB's always-free tier. PAY_PER_REQUEST scales freely but bills every request."
  type        = string
  default     = "PROVISIONED"
}

variable "dynamodb_capacity" {
  description = <<-EOT
    Provisioned capacity units. The always-free tier is 25 RCU + 25 WCU per region, shared by
    ALL provisioned tables in the account, so the defaults total 21/21 to leave headroom.
  EOT
  type = object({
    polls_read        = number
    polls_write       = number
    admin_index_read  = number
    admin_index_write = number
    votes_read        = number
    votes_write       = number
  })
  default = {
    polls_read        = 10
    polls_write       = 10
    admin_index_read  = 1
    admin_index_write = 1
    votes_read        = 10
    votes_write       = 10
  }
}

variable "table_deletion_protection" {
  description = "Protect the DynamoDB tables from accidental deletion. Set false before a deliberate destroy."
  type        = bool
  default     = true
}

variable "budget_alert_email" {
  description = "Strongly recommended. Emails this address as soon as the account spends anything (> $0.01 in a month) and when the forecast exceeds monthly_budget_usd."
  type        = string
  default     = ""
}

variable "monthly_budget_usd" {
  description = "Monthly budget amount for the forecast alert."
  type        = number
  default     = 1
}
