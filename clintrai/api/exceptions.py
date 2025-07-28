"""Custom exceptions for ClinicalTrials.gov API."""


class ClinicalTrialsAPIError(Exception):
    """Base exception for ClinicalTrials.gov API errors."""
    
    def __init__(self, message: str, status_code: int | None = None, response_text: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


class RateLimitError(ClinicalTrialsAPIError):
    """Raised when API rate limit is exceeded."""


class NotFoundError(ClinicalTrialsAPIError):
    """Raised when requested resource is not found."""


class ValidationError(ClinicalTrialsAPIError):
    """Raised when request parameters are invalid."""


class ServerError(ClinicalTrialsAPIError):
    """Raised when server returns 5xx error."""


class TimeoutError(ClinicalTrialsAPIError):
    """Raised when request times out."""


class NetworkError(ClinicalTrialsAPIError):
    """Raised when network connection fails."""