"""API client module for interacting with clinicaltrials.gov"""

from clintrai.api.client import ClinicalTrialsHTTPClient, create_default_client
from clintrai.api.protocols import HTTPClientProtocol
from clintrai.api import studies, stats
from clintrai.api.exceptions import (
    ClinicalTrialsAPIError,
    RateLimitError,
    NotFoundError,
    ValidationError,
    ServerError,
    TimeoutError,
    NetworkError,
)

__all__ = [
    # Client
    "ClinicalTrialsHTTPClient",
    "create_default_client",
    "HTTPClientProtocol",
    # Modules
    "studies",
    "stats",
    # Exceptions
    "ClinicalTrialsAPIError",
    "RateLimitError",
    "NotFoundError",
    "ValidationError",
    "ServerError",
    "TimeoutError",
    "NetworkError",
]