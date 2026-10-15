# Tables from docs/spec.md, section 3. Keep in sync with backend/flashpoll/tables.py,
# which the local bootstrap script and the test suite use.

resource "aws_dynamodb_table" "polls" {
  name                        = "${var.name_prefix}-polls"
  billing_mode                = "PAY_PER_REQUEST"
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

  global_secondary_index {
    name            = "admin_token_hash-index"
    projection_type = "ALL"

    key_schema {
      attribute_name = "admin_token_hash"
      key_type       = "HASH"
    }
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  server_side_encryption {
    enabled = true # AWS managed KMS key
  }
}

resource "aws_dynamodb_table" "votes" {
  name                        = "${var.name_prefix}-votes"
  billing_mode                = "PAY_PER_REQUEST"
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

  server_side_encryption {
    enabled = true
  }
}
