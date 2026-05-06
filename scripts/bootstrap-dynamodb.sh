#!/bin/bash

ENDPOINT_URL="http://localhost:8000"
REGION="us-east-1"

create_table() {
  local table_name=$1
  shift

  echo "Creating table '$table_name'..."
  if aws dynamodb describe-table --table-name "$table_name" --endpoint-url "$ENDPOINT_URL" --region "$REGION" > /dev/null 2>&1; then
    echo "Table '$table_name' already exists, skipping."
  else
    aws dynamodb create-table \
      --endpoint-url "$ENDPOINT_URL" \
      --region "$REGION" \
      --table-name "$table_name" \
      "$@"
    echo "Table '$table_name' created."
  fi
}

create_table "polls" \
  --attribute-definitions AttributeName=poll_id,AttributeType=S \
  --key-schema AttributeName=poll_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

create_table "votes" \
  --attribute-definitions AttributeName=poll_id,AttributeType=S AttributeName=vote_id,AttributeType=S \
  --key-schema AttributeName=poll_id,KeyType=HASH AttributeName=vote_id,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST

echo "Done."
