import os
import joblib
from src.common.config import MODEL_PATH

def load_isolation_forest_model():
    """
    Loads the Isolation Forest model from the configured path.
    Returns:
        model: IsolationForest instance, or None if not found or failed.
    """
    if not os.path.exists(MODEL_PATH):
        return None
    try:
        model = joblib.load(MODEL_PATH)
        return model
    except Exception:
        return None
