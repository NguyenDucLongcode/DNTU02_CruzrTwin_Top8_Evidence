import pandas as pd
from src.common.errors import ValidationError

FEATURE_COLUMNS = ["temperature", "humidity", "smoke", "co2", "power"]
REQUIRED_COLUMNS = ["timestamp"] + FEATURE_COLUMNS + ["label"]
PII_COLUMNS = ["name", "email", "phone", "face_id", "person_id"]

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
    # 1. Check required columns
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            raise ValidationError(f"Required column '{col}' is missing.")

    # 2. Check PII columns
    for pii in PII_COLUMNS:
        if pii in df.columns:
            raise ValidationError(f"PII leak detected! Column '{pii}' is in the dataset.")

    # 3. Check labels
    unique_labels = df["label"].unique()
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
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise ValidationError(f"Column '{col}' must be numeric.")

    # 6. Check that timestamp is not empty
    if df["timestamp"].isnull().any() or (df["timestamp"] == "").any():
        raise ValidationError("Timestamp column cannot contain null or empty values.")

    return {
        "status": "VALID",
        "total_rows": len(df),
        "normal_rows": int((df["label"] == 0).sum()),
        "anomaly_rows": int((df["label"] == 1).sum())
    }
