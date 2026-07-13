import pandas as pd
from src.ai.schemas import FEATURE_COLUMNS, normalize_sensor_dict

def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract feature columns from a pandas DataFrame.
    Ensures that timestamp and label are excluded.
    Returns a DataFrame with the exact feature columns in order.
    """
    # Keep only target feature columns in order
    return df[FEATURE_COLUMNS].copy()

def extract_one(sensor: dict) -> pd.DataFrame:
    """
    Extract features from a single sensor dictionary.
    Returns a single-row DataFrame with correct column names and order.
    """
    # Normalize keys for backward compatibility
    normalized = normalize_sensor_dict(sensor)
    # Create dictionary containing only feature columns
    row_data = {col: [float(normalized.get(col, 0.0))] for col in FEATURE_COLUMNS}
    return pd.DataFrame(row_data)
