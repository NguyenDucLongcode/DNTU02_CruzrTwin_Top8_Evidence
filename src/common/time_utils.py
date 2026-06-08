from datetime import datetime, timezone

def now_iso() -> str:
    """
    Return current UTC timestamp in ISO 8601 format with Z suffix.
    Example: 2026-06-08T08:45:00Z
    """
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
