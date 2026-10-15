variable "name_prefix" {
  type = string
}

variable "domain_name" {
  type = string
}

variable "include_www" {
  type = bool
}

variable "api_domain" {
  description = "Lambda function URL hostname to route /api/* to."
  type        = string
}

variable "origin_verify_secret" {
  type      = string
  sensitive = true
}
