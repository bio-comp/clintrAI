"""Tests for API exceptions."""

import pytest
from clintrai.api.exceptions import (
    ClinicalTrialsAPIError,
    RateLimitError,
    NotFoundError,
    ValidationError,
    ServerError,
    TimeoutError,
    NetworkError,
)


def test_base_exception_initialization():
    """Test ClinicalTrialsAPIError initialization."""
    error = ClinicalTrialsAPIError("Test error", status_code=400, response_text="Bad request")
    
    assert str(error) == "Test error"
    assert error.status_code == 400
    assert error.response_text == "Bad request"


def test_base_exception_without_optional_params():
    """Test ClinicalTrialsAPIError without optional parameters."""
    error = ClinicalTrialsAPIError("Test error")
    
    assert str(error) == "Test error"
    assert error.status_code is None
    assert error.response_text is None


def test_rate_limit_error():
    """Test RateLimitError is properly subclassed."""
    error = RateLimitError("Rate limit exceeded", status_code=429)
    
    assert isinstance(error, ClinicalTrialsAPIError)
    assert str(error) == "Rate limit exceeded"
    assert error.status_code == 429


def test_not_found_error():
    """Test NotFoundError is properly subclassed."""
    error = NotFoundError("Resource not found", status_code=404)
    
    assert isinstance(error, ClinicalTrialsAPIError)
    assert str(error) == "Resource not found"
    assert error.status_code == 404


def test_validation_error():
    """Test ValidationError is properly subclassed."""
    error = ValidationError("Invalid parameters", status_code=400)
    
    assert isinstance(error, ClinicalTrialsAPIError)
    assert str(error) == "Invalid parameters"
    assert error.status_code == 400


def test_server_error():
    """Test ServerError is properly subclassed."""
    error = ServerError("Internal server error", status_code=500)
    
    assert isinstance(error, ClinicalTrialsAPIError)
    assert str(error) == "Internal server error"
    assert error.status_code == 500


def test_timeout_error():
    """Test TimeoutError is properly subclassed."""
    error = TimeoutError("Request timed out")
    
    assert isinstance(error, ClinicalTrialsAPIError)
    assert str(error) == "Request timed out"


def test_network_error():
    """Test NetworkError is properly subclassed."""
    error = NetworkError("Connection failed")
    
    assert isinstance(error, ClinicalTrialsAPIError)
    assert str(error) == "Connection failed"