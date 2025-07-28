"""Tests for HTTP client implementation."""

import pytest
import httpx
from pytest_httpx import HTTPXMock
import tenacity

from clintrai.api.client import ClinicalTrialsHTTPClient, create_default_client
from clintrai.api.exceptions import (
    RateLimitError,
    NotFoundError,
    ValidationError,
    ServerError,
    TimeoutError,
    NetworkError,
)


@pytest.fixture
async def httpx_client():
    """Create httpx client for testing."""
    async with httpx.AsyncClient() as client:
        yield client


@pytest.fixture
def ct_client(httpx_client):
    """Create ClinicalTrialsHTTPClient for testing."""
    return ClinicalTrialsHTTPClient(httpx_client)


@pytest.mark.asyncio
async def test_client_initialization():
    """Test client initialization with defaults."""
    async with httpx.AsyncClient() as httpx_client:
        client = ClinicalTrialsHTTPClient(httpx_client)
        
        assert client.base_url == "https://clinicaltrials.gov/api/v2"
        assert client.default_timeout == 30.0


@pytest.mark.asyncio
async def test_client_initialization_custom_params():
    """Test client initialization with custom parameters."""
    async with httpx.AsyncClient() as httpx_client:
        client = ClinicalTrialsHTTPClient(
            httpx_client,
            base_url="https://test.example.com/api/",
            default_timeout=60.0
        )
        
        assert client.base_url == "https://test.example.com/api"
        assert client.default_timeout == 60.0


@pytest.mark.asyncio
async def test_successful_get_request(httpx_mock: HTTPXMock):
    """Test successful GET request."""
    httpx_mock.add_response(
        url="https://clinicaltrials.gov/api/v2/test",
        json={"result": "success"},
        status_code=200
    )
    
    async with httpx.AsyncClient() as httpx_client:
        client = ClinicalTrialsHTTPClient(httpx_client)
        response = await client.get("test")
        
        assert response.status_code == 200
        assert response.json() == {"result": "success"}


@pytest.mark.asyncio
async def test_get_request_with_params(httpx_mock: HTTPXMock):
    """Test GET request with query parameters."""
    httpx_mock.add_response(
        url="https://clinicaltrials.gov/api/v2/studies?page=1&size=10",
        json={"studies": []},
        status_code=200
    )
    
    async with httpx.AsyncClient() as httpx_client:
        client = ClinicalTrialsHTTPClient(httpx_client)
        response = await client.get("studies", params={"page": 1, "size": 10})
        
        assert response.status_code == 200
        assert response.json() == {"studies": []}


@pytest.mark.asyncio
async def test_not_found_error(httpx_mock: HTTPXMock):
    """Test 404 error handling."""
    httpx_mock.add_response(
        url="https://clinicaltrials.gov/api/v2/studies/NCT99999999",
        status_code=404,
        text="Study not found"
    )
    
    async with httpx.AsyncClient() as httpx_client:
        client = ClinicalTrialsHTTPClient(httpx_client)
        
        with pytest.raises(NotFoundError) as exc_info:
            await client.get("studies/NCT99999999")
        
        assert exc_info.value.status_code == 404
        assert exc_info.value.response_text == "Study not found"


@pytest.mark.asyncio
async def test_validation_error(httpx_mock: HTTPXMock):
    """Test 400 error handling."""
    httpx_mock.add_response(
        url="https://clinicaltrials.gov/api/v2/studies",
        status_code=400,
        text="Invalid parameters"
    )
    
    async with httpx.AsyncClient() as httpx_client:
        client = ClinicalTrialsHTTPClient(httpx_client)
        
        with pytest.raises(ValidationError) as exc_info:
            await client.get("studies")
        
        assert exc_info.value.status_code == 400
        assert "Invalid request parameters" in str(exc_info.value)


@pytest.mark.asyncio
async def test_rate_limit_error(httpx_mock: HTTPXMock):
    """Test 429 rate limit error handling."""
    # Add 3 responses for initial request + 2 retries
    for _ in range(3):
        httpx_mock.add_response(
            url="https://clinicaltrials.gov/api/v2/studies",
            status_code=429,
            text="Rate limit exceeded"
        )
    
    async with httpx.AsyncClient() as httpx_client:
        client = ClinicalTrialsHTTPClient(httpx_client)
        
        # Should retry 3 times before failing
        with pytest.raises(tenacity.RetryError) as exc_info:
            await client.get("studies")
        
        # Check that the underlying exception is RateLimitError
        assert isinstance(exc_info.value.last_attempt.exception(), RateLimitError)
        assert exc_info.value.last_attempt.exception().status_code == 429
        # Verify it was called 3 times (initial + 2 retries)
        assert len(httpx_mock.get_requests()) == 3


@pytest.mark.asyncio
async def test_server_error(httpx_mock: HTTPXMock):
    """Test 500 server error handling."""
    # Add 3 responses for initial request + 2 retries
    for _ in range(3):
        httpx_mock.add_response(
            url="https://clinicaltrials.gov/api/v2/studies",
            status_code=500
        )
    
    async with httpx.AsyncClient() as httpx_client:
        client = ClinicalTrialsHTTPClient(httpx_client)
        
        # Should retry 3 times before failing
        with pytest.raises(tenacity.RetryError) as exc_info:
            await client.get("studies")
        
        # Check that the underlying exception is ServerError
        assert isinstance(exc_info.value.last_attempt.exception(), ServerError)
        assert exc_info.value.last_attempt.exception().status_code == 500
        # Verify it was called 3 times (initial + 2 retries)
        assert len(httpx_mock.get_requests()) == 3


@pytest.mark.asyncio
async def test_timeout_error(httpx_mock: HTTPXMock):
    """Test timeout error handling."""
    httpx_mock.add_exception(httpx.TimeoutException("Request timed out"))
    
    async with httpx.AsyncClient() as httpx_client:
        client = ClinicalTrialsHTTPClient(httpx_client)
        
        # Timeout errors are not retried due to immediate conversion to TimeoutError
        with pytest.raises(TimeoutError) as exc_info:
            await client.get("studies")
        
        assert "Request timed out" in str(exc_info.value)
        # Verify it was only called once (no retries due to conversion)
        assert len(httpx_mock.get_requests()) == 1


@pytest.mark.asyncio
async def test_network_error(httpx_mock: HTTPXMock):
    """Test network connection error handling."""
    httpx_mock.add_exception(httpx.ConnectError("Connection failed"))
    
    async with httpx.AsyncClient() as httpx_client:
        client = ClinicalTrialsHTTPClient(httpx_client)
        
        # Network errors are not retried due to immediate conversion to NetworkError
        with pytest.raises(NetworkError) as exc_info:
            await client.get("studies")
        
        assert "Network connection failed" in str(exc_info.value)
        # Verify it was only called once (no retries due to conversion)
        assert len(httpx_mock.get_requests()) == 1


@pytest.mark.asyncio
async def test_custom_timeout(httpx_mock: HTTPXMock):
    """Test custom timeout parameter."""
    httpx_mock.add_response(
        url="https://clinicaltrials.gov/api/v2/studies",
        json={"studies": []},
        status_code=200
    )
    
    async with httpx.AsyncClient() as httpx_client:
        client = ClinicalTrialsHTTPClient(httpx_client)
        response = await client.get("studies", timeout=5.0)
        
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_custom_headers(httpx_mock: HTTPXMock):
    """Test custom headers parameter."""
    httpx_mock.add_response(
        url="https://clinicaltrials.gov/api/v2/studies",
        json={"studies": []},
        status_code=200
    )
    
    async with httpx.AsyncClient() as httpx_client:
        client = ClinicalTrialsHTTPClient(httpx_client)
        response = await client.get("studies", headers={"X-Custom": "value"})
        
        assert response.status_code == 200
        # Check that custom header was sent
        request = httpx_mock.get_request()
        assert request.headers.get("X-Custom") == "value"


@pytest.mark.asyncio
async def test_close_client():
    """Test client close method."""
    async with httpx.AsyncClient() as httpx_client:
        client = ClinicalTrialsHTTPClient(httpx_client)
        await client.close()
        
        # Verify httpx client is closed
        with pytest.raises(RuntimeError):
            await httpx_client.get("https://example.com")


def test_create_default_client():
    """Test create_default_client factory function."""
    client = create_default_client()
    
    assert isinstance(client, ClinicalTrialsHTTPClient)
    assert client.base_url == "https://clinicaltrials.gov/api/v2"
    assert client.default_timeout == 30.0