"""Tests for studies API functions."""

import pytest
from pytest_httpx import HTTPXMock
import httpx

from clintrai.api.client import ClinicalTrialsHTTPClient
from clintrai.api import studies
from clintrai.models.api_models import PagedStudies, Study


@pytest.fixture
async def client(httpx_mock: HTTPXMock):
    """Create test client."""
    async with httpx.AsyncClient() as httpx_client:
        yield ClinicalTrialsHTTPClient(httpx_client)


@pytest.mark.asyncio
async def test_list_studies_basic(client, httpx_mock: HTTPXMock):
    """Test basic list_studies call."""
    mock_response = {
        "studies": [
            {
                "protocolSection": {
                    "identificationModule": {
                        "nctId": "NCT12345678",
                        "briefTitle": "Test Study"
                    }
                },
                "hasResults": False
            }
        ],
        "nextPageToken": "token123",
        "totalCount": 100
    }
    
    httpx_mock.add_response(
        url="https://clinicaltrials.gov/api/v2/studies?format=json&pageSize=10&countTotal=false&sort=LastUpdatePostDate%3Adesc",
        json=mock_response,
        status_code=200
    )
    
    result = await studies.list_studies(client)
    
    assert isinstance(result, PagedStudies)
    assert len(result.studies) == 1
    assert result.studies[0].protocolSection.identificationModule.nctId == "NCT12345678"
    assert result.next_page_token == "token123"
    assert result.total_count == 100


@pytest.mark.asyncio
async def test_list_studies_with_query(client, httpx_mock: HTTPXMock):
    """Test list_studies with search query."""
    mock_response = {"studies": [], "totalCount": 0}
    
    httpx_mock.add_response(
        url="https://clinicaltrials.gov/api/v2/studies?format=json&pageSize=20&countTotal=true&sort=LastUpdatePostDate%3Adesc&query.term=cancer",
        json=mock_response,
        status_code=200
    )
    
    result = await studies.list_studies(
        client,
        query="cancer",
        page_size=20,
        count_total=True
    )
    
    assert isinstance(result, PagedStudies)
    assert len(result.studies) == 0
    assert result.total_count == 0


@pytest.mark.asyncio
async def test_list_studies_with_filters(client, httpx_mock: HTTPXMock):
    """Test list_studies with various filters."""
    mock_response = {"studies": []}
    
    httpx_mock.add_response(
        method="GET",
        json=mock_response,
        status_code=200
    )
    
    result = await studies.list_studies(
        client,
        filter_overall_status=["RECRUITING", "ACTIVE_NOT_RECRUITING"],
        filter_geo="dist(39.0,-77.0):50mi",
        filter_ids=["NCT12345678", "NCT87654321"],
        page_token="next123"
    )
    
    # Check the request was made with correct parameters
    request = httpx_mock.get_request()
    assert "filter.overallStatus=RECRUITING%2CACTIVE_NOT_RECRUITING" in str(request.url)
    assert "filter.geo=dist%2839.0%2C-77.0%29%3A50mi" in str(request.url)
    assert "filter.ids=NCT12345678%2CNCT87654321" in str(request.url)
    assert "pageToken=next123" in str(request.url)


@pytest.mark.asyncio
async def test_list_studies_with_fields(client, httpx_mock: HTTPXMock):
    """Test list_studies with specific fields."""
    mock_response = {"studies": []}
    
    httpx_mock.add_response(
        method="GET",
        json=mock_response,
        status_code=200
    )
    
    await studies.list_studies(
        client,
        fields=["NCTId", "BriefTitle", "OverallStatus"]
    )
    
    request = httpx_mock.get_request()
    assert "fields=NCTId%2CBriefTitle%2COverallStatus" in str(request.url)


@pytest.mark.asyncio
async def test_list_studies_max_page_size(client, httpx_mock: HTTPXMock):
    """Test that page_size is capped at 1000."""
    mock_response = {"studies": []}
    
    httpx_mock.add_response(
        method="GET",
        json=mock_response,
        status_code=200
    )
    
    await studies.list_studies(client, page_size=5000)
    
    request = httpx_mock.get_request()
    assert "pageSize=1000" in str(request.url)


@pytest.mark.asyncio
async def test_fetch_study(client, httpx_mock: HTTPXMock):
    """Test fetch_study function."""
    mock_study = {
        "protocolSection": {
            "identificationModule": {
                "nctId": "NCT12345678",
                "briefTitle": "Test Study"
            },
            "statusModule": {
                "overallStatus": "RECRUITING"
            }
        },
        "hasResults": False
    }
    
    httpx_mock.add_response(
        url="https://clinicaltrials.gov/api/v2/studies/NCT12345678?format=json",
        json=mock_study,
        status_code=200
    )
    
    result = await studies.fetch_study(client, "NCT12345678")
    
    assert isinstance(result, Study)
    assert result.protocolSection.identificationModule.nctId == "NCT12345678"
    assert result.protocolSection.identificationModule.briefTitle == "Test Study"
    assert result.protocolSection.statusModule.overallStatus.value == "RECRUITING"


@pytest.mark.asyncio
async def test_fetch_study_with_fields(client, httpx_mock: HTTPXMock):
    """Test fetch_study with specific fields."""
    mock_study = {
        "protocolSection": {
            "identificationModule": {
                "nctId": "NCT12345678"
            }
        },
        "hasResults": False
    }
    
    httpx_mock.add_response(
        url="https://clinicaltrials.gov/api/v2/studies/NCT12345678?format=json&fields=NCTId%2CBriefTitle",
        json=mock_study,
        status_code=200
    )
    
    result = await studies.fetch_study(
        client,
        "NCT12345678",
        fields=["NCTId", "BriefTitle"]
    )
    
    assert isinstance(result, Study)
    assert result.protocolSection.identificationModule.nctId == "NCT12345678"


@pytest.mark.asyncio
async def test_get_study_metadata(client, httpx_mock: HTTPXMock):
    """Test get_study_metadata function."""
    mock_metadata = {
        "dataVersion": "2023-10-01",
        "apiVersion": "2.0.0"
    }
    
    httpx_mock.add_response(
        url="https://clinicaltrials.gov/api/v2/studies/metadata",
        json=mock_metadata,
        status_code=200
    )
    
    result = await studies.get_study_metadata(client)
    
    assert isinstance(result, dict)
    assert result["dataVersion"] == "2023-10-01"
    assert result["apiVersion"] == "2.0.0"


@pytest.mark.asyncio
async def test_search_areas(client, httpx_mock: HTTPXMock):
    """Test search_areas function."""
    mock_areas = [
        {
            "name": "Study",
            "areas": [
                {"name": "BasicSearch", "uiLabel": "Other terms", "param": "term", "parts": []}
            ]
        }
    ]
    
    httpx_mock.add_response(
        url="https://clinicaltrials.gov/api/v2/studies/search-areas",
        json=mock_areas,
        status_code=200
    )
    
    result = await studies.search_areas(client)
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert hasattr(result[0], 'areas')
    assert hasattr(result[0], 'name')




@pytest.mark.asyncio
async def test_get_enums(client, httpx_mock: HTTPXMock):
    """Test get_enums function."""
    mock_enums = [
        {
            "type": "OverallStatus",
            "pieces": ["OverallStatus"],
            "values": [
                {"value": "RECRUITING", "legacy_value": "Recruiting"},
                {"value": "COMPLETED", "legacy_value": "Completed"}
            ]
        }
    ]
    
    httpx_mock.add_response(
        url="https://clinicaltrials.gov/api/v2/studies/enums",
        json=mock_enums,
        status_code=200
    )
    
    result = await studies.get_enums(client)
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert hasattr(result[0], 'type')
    assert hasattr(result[0], 'values')