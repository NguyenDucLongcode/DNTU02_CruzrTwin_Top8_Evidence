import pandas as pd
from src.ai.schemas import validate_dataframe, FEATURE_COLUMNS
from src.common.errors import ValidationError

def get_feature_columns() -> list[str]:
    """
    Return the feature columns used for AI training/detection.
    """
    return list(FEATURE_COLUMNS)

def load_sensor_data(path: str) -> pd.DataFrame:
    """
    Load sensor data CSV from path.
    """
    try:
        return pd.read_csv(path)
    except Exception as e:
        raise ValidationError(f"Failed to read CSV at {path}. Error: {e}")

def validate_sensor_data(df: pd.DataFrame) -> dict:
    """
    Validates sensor data DataFrame.
    Returns a summary dictionary of dataset statistics.
    """
    # 1. Run core validation
    val_result = validate_dataframe(df)
    
    # Extra check from loader requirements:
    # "label không nằm trong feature columns"
    # "timestamp không nằm trong feature columns"
    feats = get_feature_columns()
    if "label" in feats:
        raise ValidationError("Label column must not be in the feature columns list.")
    if "timestamp" in feats:
        raise ValidationError("Timestamp column must not be in the feature columns list.")
        
    num_normal = int((df["label"] == 0).sum())
    num_anomaly = int((df["label"] == 1).sum())
    
    return {
        "normal_rows": num_normal,
        "anomaly_rows": num_anomaly,
        "train_rows": num_normal,  # Train uses label=0 only
        "eval_rows": len(df)       # Eval uses all rows
    }

def split_train_eval(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split the dataset into training and evaluation sets.
    - train_df = df[df["label"] == 0] (normal-only boundary learning)
    - eval_df = df (contains both label=0 and label=1 for testing)
    """
    train_df = df[df["label"] == 0].copy()
    eval_df = df.copy()
    return train_df, eval_df
