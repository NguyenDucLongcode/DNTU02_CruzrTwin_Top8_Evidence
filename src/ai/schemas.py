import pandas as pd
from src.common.errors import ValidationError

FEATURE_COLUMNS = ["temperature", "humidity", "co2", "smoke_status", "energy_consumption"]
REQUIRED_COLUMNS = ["timestamp"] + FEATURE_COLUMNS + ["label"]
PII_COLUMNS = ["name", "email", "phone", "face_id", "person_id"]

def normalize_sensor_dict(sensor: dict) -> dict:
    """
    Normalize sensor keys for backward compatibility.
    Maps legacy 'power' -> 'energy_consumption', and 'smoke' -> 'smoke_status'.
    """
    normalized = dict(sensor)
    if "power" in normalized and "energy_consumption" not in normalized:
        normalized["energy_consumption"] = normalized["power"]
    
    # Handle smoke / smoke_status mapping carefully
    if "smoke" in normalized and "smoke_status" not in normalized:
        try:
            val = float(normalized["smoke"])
            if val > 1.0:
                # Analog smoke value
                normalized["smoke_status"] = 1 if val >= 300.0 else 0
                normalized["raw_smoke_value"] = val
            else:
                # Binary smoke status
                normalized["smoke_status"] = int(val)
                normalized["raw_smoke_value"] = 300.0 if val >= 1.0 else 0.0
        except (ValueError, TypeError):
            normalized["smoke_status"] = normalized["smoke"]
            
    if "smoke_status" in normalized and "raw_smoke_value" not in normalized:
        try:
            val = float(normalized["smoke_status"])
            if val > 1.0:
                normalized["smoke_status"] = 1 if val >= 300.0 else 0
                normalized["raw_smoke_value"] = val
            else:
                normalized["smoke_status"] = int(val)
                normalized["raw_smoke_value"] = 300.0 if val >= 1.0 else 0.0
        except (ValueError, TypeError):
            normalized["raw_smoke_value"] = 0.0
            
    return normalized

def validate_sensor_dict(sensor: dict) -> None:
    """
    Validate a single sensor reading dictionary.
    """
    # Check for PII leaks
    for pii in PII_COLUMNS:
        if pii in sensor:
            raise ValidationError(f"PII leak detected! Column '{pii}' should not exist in sensor data.")

    # Check for missing feature columns
    for col in FEATURE_COLUMNS:
        if col not in sensor:
            raise ValidationError(f"Missing required feature '{col}' in sensor input.")
        # Check if they are numeric
        try:
            float(sensor[col])
        except (ValueError, TypeError):
            raise ValidationError(f"Feature '{col}' must be numeric, got {sensor[col]}.")

def validate_dataframe(df: pd.DataFrame) -> dict:
    """
    Validate a pandas DataFrame containing sensor data.
    Returns a status summary dict or raises ValidationError.
    """
    # Normalize dataframe columns for validation
    df_norm = df.copy()
    if "power" in df_norm.columns and "energy_consumption" not in df_norm.columns:
        df_norm = df_norm.rename(columns={"power": "energy_consumption"})
    if "smoke" in df_norm.columns and "smoke_status" not in df_norm.columns:
        # For dataframes, map analog to binary
        df_norm["smoke_status"] = df_norm["smoke"].apply(lambda x: 1 if float(x) >= 1.0 else 0)
    if "expected_label" in df_norm.columns and "label" not in df_norm.columns:
        df_norm["label"] = df_norm["expected_label"].apply(lambda x: 0 if x == "normal" else 1)

    # 1. Check required columns
    for col in REQUIRED_COLUMNS:
        if col not in df_norm.columns:
            raise ValidationError(f"Required column '{col}' is missing.")

    # 2. Check PII columns
    for pii in PII_COLUMNS:
        if pii in df_norm.columns:
            raise ValidationError(f"PII leak detected! Column '{pii}' is in the dataset.")

    # 3. Check labels
    unique_labels = df_norm["label"].unique()
    for lbl in unique_labels:
        if lbl not in [0, 1]:
            raise ValidationError(f"Invalid label '{lbl}' found. Labels must be 0 (normal) or 1 (anomaly).")

    # 4. Check that we have at least one label 0 and one label 1
    has_normal = 0 in unique_labels
    has_anomaly = 1 in unique_labels
    if not has_normal:
        raise ValidationError("Dataset must contain at least one normal row (label=0).")
    if not has_anomaly:
        raise ValidationError("Dataset must contain at least one anomaly row (label=1).")

    # 5. Check numeric types
    for col in FEATURE_COLUMNS:
        if not pd.api.types.is_numeric_dtype(df_norm[col]):
            raise ValidationError(f"Column '{col}' must be numeric.")

    # 6. Check that timestamp is not empty
    if df_norm["timestamp"].isnull().any() or (df_norm["timestamp"] == "").any():
        raise ValidationError("Timestamp column cannot contain null or empty values.")

    return {
        "status": "VALID",
        "total_rows": len(df_norm),
        "normal_rows": int((df_norm["label"] == 0).sum()),
        "anomaly_rows": int((df_norm["label"] == 1).sum())
    }
