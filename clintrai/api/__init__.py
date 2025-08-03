"""API client module for interacting with clinicaltrials.gov"""

from clintrai.api.hybrid_client import HybridHTTPClient, create_hybrid_client
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
    "HybridHTTPClient",
    "create_hybrid_client",
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