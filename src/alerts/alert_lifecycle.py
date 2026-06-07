from src.common.errors import ValidationError

VALID_ALERT_STATUSES = {"OPEN", "DISPATCHED", "ACKED", "RESOLVED", "ERROR"}

VALID_TRANSITIONS = {
    "OPEN": {"DISPATCHED", "ERROR"},
    "DISPATCHED": {"ACKED", "ERROR"},
    "ACKED": {"RESOLVED"},
    "RESOLVED": set(),
    "ERROR": set()
}

def validate_alert_transition(current: str, new_status: str, note: str | None = None) -> bool:
    """
    Validates if transition from current to new_status is allowed.
    Raises ValidationError if transition is invalid.
    """
    if current not in VALID_ALERT_STATUSES:
        raise ValidationError(f"Invalid current alert status: '{current}'")
    if new_status not in VALID_ALERT_STATUSES:
        raise ValidationError(f"Invalid target alert status: '{new_status}'")
        
    # Recovery note exception: allow transition if recovery note is provided
    if note and "recovery" in note.lower():
        return True
        
    allowed = VALID_TRANSITIONS[current]
    if new_status not in allowed:
        raise ValidationError(
            f"Alert status transition not allowed: '{current}' -> '{new_status}'. Allowed targets: {allowed}"
        )
    return True
