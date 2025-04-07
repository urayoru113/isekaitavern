from .basic import TransmittableException


class StatusError(TransmittableException):
    """Exception raised when user uses a command that is not allowed. Such as user uses a guild command in a DM."""


class UrlExtractionError(TransmittableException):
    """Exception raised when URL extraction fails."""


class TypeError(TransmittableException):
    """Exception raised when a type error occurs."""


class ValueError(TransmittableException):
    """Exception raised when a value error occurs."""
