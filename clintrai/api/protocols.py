"""Protocol definitions for dependency injection."""

from typing import Protocol
import httpx


class HTTPClientProtocol(Protocol):
    """Protocol for HTTP client implementations."""
    
    async def get(
        self, 
        url: str, 
        *, 
        params: dict[str, str | int | float | bool | None] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        """Make GET request."""
        ...
    
    async def close(self) -> None:
        """Close the client and clean up resources."""
        ...