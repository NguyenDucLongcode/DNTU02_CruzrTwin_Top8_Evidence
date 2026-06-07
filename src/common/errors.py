class DNTUException(Exception):
    """Base exception class for DNTU02 system."""
    pass

class ValidationError(DNTUException):
    """Raised when validation fails for input schemas."""
    pass

class DetectionError(DNTUException):
    """Raised when anomaly detection encounters an error."""
    pass

class AlertServiceError(DNTUException):
    """Raised when there is an issue handling AlertEvents."""
    pass

class RobotActionError(DNTUException):
    """Raised when robot actions cannot be created or dispatched."""
    pass

class OrionClientError(DNTUException):
    """Raised when FIWARE Orion client encounters HTTP issues or is unavailable."""
    pass
