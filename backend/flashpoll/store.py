"""DynamoDB access. All reads and writes to the tables go through PollStore."""

from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from .config import Settings
from .tables import ADMIN_INDEX


def _plain(value):
    """Convert DynamoDB Decimals back to ints so the rest of the app never sees them."""
    if isinstance(value, Decimal):
        return int(value)
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_plain(item) for item in value]
    return value


class PollIdTaken(Exception):
    pass


class VoteRejected(Exception):
    """A vote transaction was cancelled by a condition check."""

    def __init__(self, poll_rejected: bool):
        # True: the poll update failed (missing or closed). False: a voter marker already existed.
        self.poll_rejected = poll_rejected


class PollStore:
    def __init__(self, settings: Settings):
        resource = boto3.resource(
            "dynamodb", region_name=settings.aws_region, endpoint_url=settings.dynamodb_url
        )
        # The resource's client (de)serializes Python values for us, transactions included.
        self.client = resource.meta.client
        self.polls = resource.Table(settings.polls_table)
        self.votes = resource.Table(settings.votes_table)

    def create_poll(self, poll: dict) -> None:
        try:
            self.polls.put_item(Item=poll, ConditionExpression="attribute_not_exists(poll_id)")
        except ClientError as err:
            if err.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise PollIdTaken() from err
            raise

    def get_poll(self, poll_id: str) -> dict | None:
        item = self.polls.get_item(Key={"poll_id": poll_id}, ConsistentRead=True).get("Item")
        return _plain(item) if item else None

    def find_by_admin_hash(self, admin_token_hash: str) -> dict | None:
        items = self.polls.query(
            IndexName=ADMIN_INDEX,
            KeyConditionExpression=Key("admin_token_hash").eq(admin_token_hash),
        )["Items"]
        return _plain(items[0]) if items else None

    def has_voter(self, poll_id: str, voter_key: str) -> bool:
        item = self.votes.get_item(
            Key={"poll_id": poll_id, "voter_key": voter_key}, ConsistentRead=True
        ).get("Item")
        return item is not None

    def record_vote(
        self,
        poll: dict,
        option_index: int,
        now: int,
        markers: list[tuple[str, bool]],
    ) -> None:
        """Count a vote and write voter markers atomically (docs/spec.md, 3.3).

        `markers` is a list of (voter_key, must_be_new). A marker with must_be_new
        rejects the whole vote if it already exists.
        """
        items = [
            {
                "Update": {
                    "TableName": self.polls.name,
                    "Key": {"poll_id": poll["poll_id"]},
                    "UpdateExpression": "SET #counts.#option = #counts.#option + :one, "
                    "total_votes = total_votes + :one",
                    "ConditionExpression": "attribute_exists(poll_id) AND expires_at > :now",
                    "ExpressionAttributeNames": {"#counts": "counts", "#option": str(option_index)},
                    "ExpressionAttributeValues": {":one": 1, ":now": now},
                }
            }
        ]
        for voter_key, must_be_new in markers:
            put = {
                "TableName": self.votes.name,
                "Item": {
                    "poll_id": poll["poll_id"],
                    "voter_key": voter_key,
                    "created_at": now,
                    "ttl": poll["ttl"],
                },
            }
            if must_be_new:
                put["ConditionExpression"] = "attribute_not_exists(voter_key)"
            items.append({"Put": put})

        try:
            self.client.transact_write_items(TransactItems=items)
        except ClientError as err:
            if err.response["Error"]["Code"] != "TransactionCanceledException":
                raise
            reasons = err.response.get("CancellationReasons", [])
            poll_failed = bool(reasons) and reasons[0].get("Code") == "ConditionalCheckFailed"
            markers_failed = any(r.get("Code") == "ConditionalCheckFailed" for r in reasons[1:])
            if not (poll_failed or markers_failed):
                raise
            raise VoteRejected(poll_rejected=poll_failed) from err

    def close_poll(self, poll_id: str, now: int) -> None:
        """Move expires_at to now if the poll is still open. No-op if already closed."""
        try:
            self.polls.update_item(
                Key={"poll_id": poll_id},
                UpdateExpression="SET expires_at = :now",
                ConditionExpression="attribute_exists(poll_id) AND expires_at > :now",
                ExpressionAttributeValues={":now": now},
            )
        except ClientError as err:
            if err.response["Error"]["Code"] != "ConditionalCheckFailedException":
                raise

    def delete_poll(self, poll_id: str) -> None:
        self.polls.delete_item(Key={"poll_id": poll_id})
        query = {
            "KeyConditionExpression": Key("poll_id").eq(poll_id),
            "ProjectionExpression": "poll_id, voter_key",
        }
        with self.votes.batch_writer() as batch:
            while True:
                page = self.votes.query(**query)
                for item in page["Items"]:
                    batch.delete_item(
                        Key={"poll_id": item["poll_id"], "voter_key": item["voter_key"]}
                    )
                if "LastEvaluatedKey" not in page:
                    break
                query["ExclusiveStartKey"] = page["LastEvaluatedKey"]
