from src.common.errors import ValidationError

VALID_SCENARIO_SOURCES = {"payload", "orion_entity", "active_state_fallback", "manual_demo"}
VALID_LABELS = {"normal", "warning", "critical"}

def validate_ai_input(reading: dict):
    """
    Validates the structure of the input dictionary.
    Raises ValidationError if validation fails.
    """
    if not isinstance(reading, dict):
        raise ValidationError("Input reading must be a dictionary.")
    
    required_keys = [
        "demo_run_id",
        "scenario_id",
        "scenario_source",
        "zone_id",
        "timestamp",
        "source_entity_id",
        "temperature",
        "humidity",
        "air_quality_or_co2",
        "smoke_status",
        "energy_consumption"
    ]
    
    for key in required_keys:
        if key not in reading:
            raise ValidationError(f"Missing required field: '{key}'.")
            
    # Check scenario source
    if reading["scenario_source"] not in VALID_SCENARIO_SOURCES:
        raise ValidationError(
            f"Invalid scenario_source: '{reading['scenario_source']}'. Must be one of {VALID_SCENARIO_SOURCES}"
        )
        
    # Check data types
    try:
        float(reading["temperature"])
        float(reading["humidity"])
        int(reading["air_quality_or_co2"])
        smoke = int(reading["smoke_status"])
        if smoke not in [0, 1]:
            raise ValidationError("smoke_status must be 0 or 1.")
        float(reading["energy_consumption"])
    except (ValueError, TypeError) as e:
        raise ValidationError(f"Data type validation failed: {e}")
        
    # Check expected_label if present
    expected = reading.get("expected_label")
    if expected is not None and expected not in VALID_LABELS:
        raise ValidationError(f"Invalid expected_label: '{expected}'. Must be one of {VALID_LABELS}")
