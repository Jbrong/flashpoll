variable "name_prefix" {
  type = string
}

variable "deletion_protection" {
  type = bool
}

variable "billing_mode" {
  type = string
  validation {
    condition     = contains(["PROVISIONED", "PAY_PER_REQUEST"], var.billing_mode)
    error_message = "billing_mode must be PROVISIONED or PAY_PER_REQUEST."
  }
}

variable "capacity" {
  description = "Provisioned read/write capacity units (ignored for PAY_PER_REQUEST)."
  type = object({
    polls_read        = number
    polls_write       = number
    admin_index_read  = number
    admin_index_write = number
    votes_read        = number
    votes_write       = number
  })
}
