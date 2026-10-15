variable "name_prefix" {
  type = string
}

variable "lambda_zip_path" {
  type = string
}

variable "app_url" {
  description = "Public site URL, used to build share/admin links."
  type        = string
}

variable "polls_table" {
  type = object({ name = string, arn = string })
}

variable "votes_table" {
  type = object({ name = string, arn = string })
}

variable "origin_verify_secret" {
  type      = string
  sensitive = true
}

variable "throttle_rate" {
  type = number
}

variable "throttle_burst" {
  type = number
}

variable "log_retention_days" {
  type = number
}
