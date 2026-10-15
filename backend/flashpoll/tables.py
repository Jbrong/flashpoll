"""DynamoDB table definitions (docs/spec.md, section 3).

Used by the local bootstrap script and the test suite, so both match what
Terraform provisions in AWS. Keep the three in sync.
"""

ADMIN_INDEX = "admin_token_hash-index"


def polls_table(name: str) -> dict:
    return {
        "TableName": name,
        "BillingMode": "PAY_PER_REQUEST",
        "AttributeDefinitions": [
            {"AttributeName": "poll_id", "AttributeType": "S"},
            {"AttributeName": "admin_token_hash", "AttributeType": "S"},
        ],
        "KeySchema": [{"AttributeName": "poll_id", "KeyType": "HASH"}],
        "GlobalSecondaryIndexes": [
            {
                "IndexName": ADMIN_INDEX,
                "KeySchema": [{"AttributeName": "admin_token_hash", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
    }


def votes_table(name: str) -> dict:
    return {
        "TableName": name,
        "BillingMode": "PAY_PER_REQUEST",
        "AttributeDefinitions": [
            {"AttributeName": "poll_id", "AttributeType": "S"},
            {"AttributeName": "voter_key", "AttributeType": "S"},
        ],
        "KeySchema": [
            {"AttributeName": "poll_id", "KeyType": "HASH"},
            {"AttributeName": "voter_key", "KeyType": "RANGE"},
        ],
    }


def create_tables(client, polls_name: str, votes_name: str) -> list[str]:
    """Create any missing tables and enable TTL. Returns the names it created."""
    existing = set(client.list_tables()["TableNames"])
    created = []
    for definition in (polls_table(polls_name), votes_table(votes_name)):
        name = definition["TableName"]
        if name in existing:
            continue
        client.create_table(**definition)
        client.get_waiter("table_exists").wait(TableName=name)
        client.update_time_to_live(
            TableName=name,
            TimeToLiveSpecification={"Enabled": True, "AttributeName": "ttl"},
        )
        created.append(name)
    return created
