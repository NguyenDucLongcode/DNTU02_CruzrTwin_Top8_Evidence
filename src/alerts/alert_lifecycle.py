ALLOWED_STATUSES = {"OPEN", "ACKED", "RESOLVED", "ERROR", "ACTIVE"}

def is_valid_alert_status(status: str) -> bool:
    """
    Check if the given status string is a valid AlertEvent status.
    """
    return status in ALLOWED_STATUSES
