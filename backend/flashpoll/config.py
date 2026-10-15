import os
from dataclasses import dataclass, field


def _csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_url: str = "http://localhost:5173"
    aws_region: str = "us-east-1"
    dynamodb_url: str | None = None
    polls_table: str = "flashpoll-polls"
    votes_table: str = "flashpoll-votes"
    cors_origins: list[str] = field(default_factory=lambda: ["http://localhost:5173"])
    trusted_proxy_count: int = 0

    @classmethod
    def from_env(cls) -> "Settings":
        defaults = cls()
        return cls(
            app_url=os.environ.get("APP_URL", defaults.app_url).rstrip("/"),
            aws_region=os.environ.get("AWS_REGION", defaults.aws_region),
            dynamodb_url=os.environ.get("DYNAMODB_URL") or None,
            polls_table=os.environ.get("POLLS_TABLE", defaults.polls_table),
            votes_table=os.environ.get("VOTES_TABLE", defaults.votes_table),
            cors_origins=_csv(os.environ.get("CORS_ORIGINS", ",".join(defaults.cors_origins))),
            trusted_proxy_count=int(
                os.environ.get("TRUSTED_PROXY_COUNT", defaults.trusted_proxy_count)
            ),
        )
