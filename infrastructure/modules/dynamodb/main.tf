# Tables from docs/spec.md, section 3. Keep in sync with backend/flashpoll/tables.py,
# which the local bootstrap script and the test suite use.
#
# Provisioned capacity, because DynamoDB's always-free tier (25 RCU + 25 WCU per region,
# shared by every provisioned table in the account) does not cover on-demand tables.

locals {
  provisioned = var.billing_mode == "PROVISIONED"
}

resource "aws_dynamodb_table" "polls" {
  name                        = "${var.name_prefix}-polls"
  billing_mode                = var.billing_mode
  read_capacity               = local.provisioned ? var.capacity.polls_read : null
  write_capacity              = local.provisioned ? var.capacity.polls_write : null
  hash_key                    = "poll_id"
  deletion_protection_enabled = var.deletion_protection

  attribute {
    name = "poll_id"
    type = "S"
  }

  attribute {
    name = "admin_token_hash"
    type = "S"
  }

  # Keys only: vote count updates never write to the index; the app re-reads the base table.
  global_secondary_index {
    name            = "admin_token_hash-index"
    projection_type = "KEYS_ONLY"
    read_capacity   = local.provisioned ? var.capacity.admin_index_read : null
    write_capacity  = local.provisioned ? var.capacity.admin_index_write : null

    key_schema {
      attribute_name = "admin_token_hash"
      key_type       = "HASH"
    }
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }
}

resource "aws_dynamodb_table" "votes" {
  name                        = "${var.name_prefix}-votes"
  billing_mode                = var.billing_mode
  read_capacity               = local.provisioned ? var.capacity.votes_read : null
  write_capacity              = local.provisioned ? var.capacity.votes_write : null
  hash_key                    = "poll_id"
  range_key                   = "voter_key"
  deletion_protection_enabled = var.deletion_protection

  attribute {
    name = "poll_id"
    type = "S"
  }

  attribute {
    name = "voter_key"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }
}
