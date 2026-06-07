from datetime import datetime, timezone

def now_iso() -> str:
    """
    Returns the current UTC time in ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ
    """
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
