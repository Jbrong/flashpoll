locals {
  name = "flashpoll-${var.environment}"
}

module "data" {
  source = "./modules/dynamodb"

  name_prefix         = local.name
  deletion_protection = var.table_deletion_protection
}

# Shared secret CloudFront adds to every API request; the API rejects requests without it,
# so it can't be called around CloudFront (docs/spec.md, 4.2).
resource "random_password" "origin_verify" {
  length  = 48
  special = false
}

module "api" {
  source = "./modules/api"

  name_prefix          = local.name
  lambda_zip_path      = var.lambda_zip_path
  app_url              = "https://${var.domain_name}"
  polls_table          = module.data.polls_table
  votes_table          = module.data.votes_table
  origin_verify_secret = random_password.origin_verify.result
  throttle_rate        = var.api_throttle_rate
  throttle_burst       = var.api_throttle_burst
  log_retention_days   = var.log_retention_days
}

module "site" {
  source = "./modules/site"
  providers = {
    aws           = aws
    aws.us_east_1 = aws.us_east_1
  }

  name_prefix          = local.name
  domain_name          = var.domain_name
  include_www          = var.include_www
  api_domain           = module.api.api_domain
  origin_verify_secret = random_password.origin_verify.result
}

resource "aws_budgets_budget" "monthly" {
  count = var.budget_alert_email == "" ? 0 : 1

  name         = "${local.name}-monthly"
  budget_type  = "COST"
  limit_amount = tostring(var.monthly_budget_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  dynamic "notification" {
    for_each = [80, 100]
    content {
      comparison_operator        = "GREATER_THAN"
      threshold                  = notification.value
      threshold_type             = "PERCENTAGE"
      notification_type          = "ACTUAL"
      subscriber_email_addresses = [var.budget_alert_email]
    }
  }
}
