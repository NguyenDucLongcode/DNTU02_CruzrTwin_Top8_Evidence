from src.common.errors import ValidationError

VALID_ROBOT_STATUSES = {"PENDING", "SENT_TO_BRIDGE", "IN_PROGRESS", "GUIDANCE_DELIVERED", "ACK_WAITING", "ACKED", "ERROR"}

VALID_TRANSITIONS = {
    "PENDING": {"SENT_TO_BRIDGE", "ERROR"},
    "SENT_TO_BRIDGE": {"IN_PROGRESS", "ERROR"},
    "IN_PROGRESS": {"GUIDANCE_DELIVERED", "ERROR"},
    "GUIDANCE_DELIVERED": {"ACK_WAITING", "ERROR"},
    "ACK_WAITING": {"ACKED", "ERROR"},
    "ACKED": set(),
    "ERROR": set()
}

def validate_robot_transition(current: str, new_status: str):
    """
    Validates if transitioning from current status to new_status is allowed.
    Raises ValidationError if invalid.
    """
    if current not in VALID_ROBOT_STATUSES:
        raise ValidationError(f"Invalid current robot status: '{current}'")
    if new_status not in VALID_ROBOT_STATUSES:
        raise ValidationError(f"Invalid target robot status: '{new_status}'")
        
    allowed = VALID_TRANSITIONS[current]
    if new_status not in allowed:
        raise ValidationError(
            f"RobotAction status transition not allowed: '{current}' -> '{new_status}'. Allowed targets: {allowed}"
        )
    return True
