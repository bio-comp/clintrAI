"""HTTP client implementation with retry logic and error handling."""

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from clintrai.api.protocols import HTTPClientProtocol
from clintrai.api.exceptions import (
    ClinicalTrialsAPIError,
    RateLimitError,
    NotFoundError,
    ValidationError,
    ServerError,
    TimeoutError,
    NetworkError,
)


class ClinicalTrialsHTTPClient:
    """HTTP client for ClinicalTrials.gov API with retry logic and error handling."""
    
    def __init__(
        self,
        httpx_client: httpx.AsyncClient,
        *,
        base_url: str = "https://clinicaltrials.gov/api/v2",
        default_timeout: float = 30.0,
    ):
        """Initialize the HTTP client.
        
        Args:
            httpx_client: httpx AsyncClient instance to use
            base_url: Base URL for the API
            default_timeout: Default timeout for requests
        """
        self._client = httpx_client
        self.base_url = base_url.rstrip("/")
        self.default_timeout = default_timeout
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError, RateLimitError, ServerError))
    )
    async def get(
        self,
        url: str,
        *,
        params: dict[str, str | int | float | bool | None] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        """Make GET request with retry logic and error handling.
        
        Args:
            url: URL path (will be joined with base_url)
            params: Query parameters
            headers: Additional headers
            timeout: Request timeout (overrides default)
            
        Returns:
            httpx.Response object
            
        Raises:
            ClinicalTrialsAPIError: For API-related errors
            TimeoutError: For timeout errors
            NetworkError: For network-related errors
        """
        full_url = f"{self.base_url}/{url.lstrip('/')}"
        request_timeout = timeout or self.default_timeout
        
        try:
            response = await self._client.get(
                full_url,
                params=params,
                headers=headers,
                timeout=request_timeout,
            )
            
            # Handle different HTTP status codes
            if response.status_code == 200:
                return response
            elif response.status_code == 404:
                raise NotFoundError(
                    f"Resource not found: {full_url}",
                    status_code=response.status_code,
                    response_text=response.text,
                )
            elif response.status_code == 400:
                raise ValidationError(
                    f"Invalid request parameters: {response.text}",
                    status_code=response.status_code,
                    response_text=response.text,
                )
            elif response.status_code == 403:
                raise ClinicalTrialsAPIError(
                    f"Forbidden: {response.text}",
                    status_code=response.status_code,
                    response_text=response.text,
                )
            elif response.status_code == 429:
                raise RateLimitError(
                    "Rate limit exceeded",
                    status_code=response.status_code,
                    response_text=response.text,
                )
            elif 500 <= response.status_code < 600:
                raise ServerError(
                    f"Server error: {response.status_code}",
                    status_code=response.status_code,
                    response_text=response.text,
                )
            else:
                raise ClinicalTrialsAPIError(
                    f"Unexpected status code: {response.status_code}",
                    status_code=response.status_code,
                    response_text=response.text,
                )
                
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out after {request_timeout}s") from e
        except httpx.ConnectError as e:
            raise NetworkError(f"Network connection failed: {e}") from e
        except httpx.RequestError as e:
            raise NetworkError(f"Request failed: {e}") from e
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


def create_default_client() -> ClinicalTrialsHTTPClient:
    """Create a default HTTP client with sensible defaults.
    
    Returns:
        Configured ClinicalTrialsHTTPClient instance
    """
    httpx_client = httpx.AsyncClient(
        headers={
            "User-Agent": "clinTrAI/0.1.0",
            "Accept": "application/json",
        },
        timeout=30.0,
    )
    
    return ClinicalTrialsHTTPClient(httpx_client)