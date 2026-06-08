class BaseAppError(Exception):
    """Base exception for all custom application errors."""
    pass

class ConfigError(BaseAppError):
    """Raised when configuration values are missing or invalid."""
    pass

class ValidationError(BaseAppError):
    """Raised when data validation fails."""
    pass

class InferenceError(BaseAppError):
    """Raised when model inference fails."""
    pass

class TrainingError(BaseAppError):
    """Raised when training model fails."""
    pass
