"""Tests for API protocols."""

import pytest
from typing import Protocol, runtime_checkable
import httpx

from clintrai.api.protocols import HTTPClientProtocol


class MockHTTPClient:
    """Mock HTTP client for testing protocol compliance."""
    
    async def get(
        self,
        url: str,
        *,
        params: dict[str, str | int | float | bool | None] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        """Mock get method."""
        return httpx.Response(200, json={"test": "data"})
    
    async def close(self) -> None:
        """Mock close method."""
        pass


def test_protocol_compliance():
    """Test that MockHTTPClient complies with HTTPClientProtocol."""
    client = MockHTTPClient()
    
    # Test that the client has the required methods
    assert hasattr(client, "get")
    assert hasattr(client, "close")
    assert callable(getattr(client, "get"))
    assert callable(getattr(client, "close"))


def test_protocol_methods_exist():
    """Test that protocol defines required methods."""
    # Check that protocol has the expected methods
    assert hasattr(HTTPClientProtocol, "get")
    assert hasattr(HTTPClientProtocol, "close")