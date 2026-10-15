import time
from datetime import UTC, datetime


def now() -> int:
    """Current Unix time in seconds. Tests monkeypatch this to move time."""
    return int(time.time())


def iso(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
