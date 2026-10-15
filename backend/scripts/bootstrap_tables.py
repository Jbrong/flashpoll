"""Create the DynamoDB tables in DynamoDB Local (or whatever DYNAMODB_URL points at).

Usage, from backend/:  pipenv run bootstrap
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
load_dotenv()

import boto3  # noqa: E402

from flashpoll.config import Settings  # noqa: E402
from flashpoll.tables import create_tables  # noqa: E402


def main() -> None:
    settings = Settings.from_env()
    if not settings.dynamodb_url:
        sys.exit(
            "DYNAMODB_URL is not set; refusing to create tables in real AWS. Use Terraform there."
        )
    client = boto3.client(
        "dynamodb", region_name=settings.aws_region, endpoint_url=settings.dynamodb_url
    )
    created = create_tables(client, settings.polls_table, settings.votes_table)
    for name in (settings.polls_table, settings.votes_table):
        print(f"{name}: {'created' if name in created else 'already exists'}")


if __name__ == "__main__":
    main()
