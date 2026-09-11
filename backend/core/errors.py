class OneWaySentinelException(Exception):
    """Base exception class for OneWay Sentinel."""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class IngestionError(OneWaySentinelException):
    def __init__(self, message: str):
        super().__init__(message, code="INGESTION_ERROR")


class MLInferenceError(OneWaySentinelException):
    def __init__(self, message: str):
        super().__init__(message, code="ML_INFERENCE_ERROR")


class ZeroOutboundViolationError(OneWaySentinelException):
    def __init__(self, message: str = "Attempted write operation on read-only passive capture interface."):
        super().__init__(message, code="ZERO_OUTBOUND_VIOLATION")


class AuthenticationError(OneWaySentinelException):
    def __init__(self, message: str = "Invalid credentials or authentication token."):
        super().__init__(message, code="AUTHENTICATION_FAILED")


class PermissionDeniedError(OneWaySentinelException):
    def __init__(self, message: str = "Insufficient permissions to perform this action."):
        super().__init__(message, code="PERMISSION_DENIED")
