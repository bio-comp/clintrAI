"""Hybrid HTTP client that uses curl_cffi for specific domains and httpx for others."""

from typing import Any
import httpx
from curl_cffi.requests import AsyncSession
from curl_cffi import CurlError
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


class HybridHTTPClient:
    """Hybrid HTTP client that automatically chooses the best client for each domain."""
    
    def __init__(
        self,
        *,
        base_url: str = "https://beta-ut.clinicaltrials.gov/api/v2",
        default_timeout: float = 30.0,
        default_headers: dict[str, str] | None = None,
        impersonate_domains: list[str] | None = None,
        impersonate: str = "chrome110",
    ):
        """Initialize the hybrid client.
        
        Args:
            base_url: Base URL for the API
            default_timeout: Default timeout for requests
            default_headers: Default headers to include with requests
            impersonate_domains: List of domains that require browser impersonation
            impersonate: Browser/client to impersonate for curl_cffi
        """
        self.base_url = base_url.rstrip("/")
        self.default_timeout = default_timeout
        self.impersonate_domains = impersonate_domains or ["clinicaltrials.gov"]
        self.impersonate = impersonate
        
        headers = {
            "User-Agent": "clinTrAI/0.1.0 (research application; contact via GitHub)",
            "Accept": "application/json",
        }
        if default_headers:
            headers.update(default_headers)
        
        # Initialize both clients
        self._httpx_client = httpx.AsyncClient(
            headers=headers,
            timeout=default_timeout,
        )
        
        self._cffi_client = AsyncSession()
        self._cffi_headers = headers
    
    def _get_client_for_url(self, url: str) -> tuple[httpx.AsyncClient | AsyncSession, dict[str, str]]:
        """Get the appropriate client for the given URL.
        
        Args:
            url: The URL to check
            
        Returns:
            Tuple of (client, headers) to use for this URL
        """
        # Use curl_cffi for domains that require browser impersonation
        if any(domain in url for domain in self.impersonate_domains):
            return self._cffi_client, self._cffi_headers
        
        # Use httpx for all other domains
        return self._httpx_client, {}
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((TimeoutError, NetworkError, RateLimitError, ServerError))
    )
    async def get(
        self,
        url: str,
        *,
        params: dict[str, str | int | float | bool | None] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        """Make GET request with automatic client selection.
        
        Args:
            url: URL path (will be joined with base_url if relative)
            params: Query parameters
            headers: Additional headers
            timeout: Request timeout (overrides default)
            
        Returns:
            httpx.Response-compatible object
            
        Raises:
            ClinicalTrialsAPIError: For API-related errors
            TimeoutError: For timeout errors
            NetworkError: For network-related errors
        """
        # Build full URL if needed
        if not url.startswith(('http://', 'https://')):
            full_url = f"{self.base_url}/{url.lstrip('/')}"
        else:
            full_url = url
        
        request_timeout = timeout or self.default_timeout
        
        # Get appropriate client
        client, default_headers = self._get_client_for_url(full_url)
        
        # Prepare headers
        request_headers = dict(default_headers)
        if headers:
            request_headers.update(headers)
        
        try:
            # Use curl_cffi client
            if isinstance(client, AsyncSession):
                response = await client.get(
                    full_url,
                    params=params,
                    headers=request_headers,
                    timeout=request_timeout,
                    impersonate=self.impersonate
                )
            else:
                # Use httpx client
                response = await client.get(
                    full_url,
                    params=params,
                    headers=request_headers,
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
                
        # Handle httpx-specific exceptions
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out after {request_timeout}s") from e
        except httpx.ConnectError as e:
            raise NetworkError(f"Network connection failed: {e}") from e
        except httpx.RequestError as e:
            raise NetworkError(f"Request failed: {e}") from e
        
        # Handle curl_cffi-specific exceptions
        except CurlError as e:
            # curl_cffi uses CurlError as base exception
            error_msg = str(e).lower()
            if "timeout" in error_msg:
                raise TimeoutError(f"Request timed out after {request_timeout}s") from e
            elif "connect" in error_msg or "resolve" in error_msg:
                raise NetworkError(f"Network connection failed: {e}") from e
            else:
                raise NetworkError(f"Request failed: {e}") from e
        
        # Handle any remaining exceptions
        except Exception as e:
            # Re-raise our custom exceptions
            if isinstance(e, (ClinicalTrialsAPIError, RateLimitError, NotFoundError, 
                            ValidationError, ServerError, TimeoutError, NetworkError)):
                raise
            # Convert unknown exceptions
            raise NetworkError(f"Unexpected error: {e}") from e
    
    async def close(self) -> None:
        """Close both HTTP clients."""
        await self._httpx_client.aclose()
        await self._cffi_client.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


def create_hybrid_client(
    *,
    impersonate_domains: list[str] | None = None,
    impersonate: str = "chrome110"
) -> HybridHTTPClient:
    """Create a hybrid HTTP client with sensible defaults.
    
    Args:
        impersonate_domains: List of domains that require browser impersonation
        impersonate: Browser/client to impersonate for problematic domains
    
    Returns:
        Configured HybridHTTPClient instance
    """
    return HybridHTTPClient(
        impersonate_domains=impersonate_domains,
        impersonate=impersonate
    )