"""Integration tests for studies API - these hit the live API."""

import pytest
from clintrai.api.hybrid_client import create_hybrid_client
from clintrai.api import studies
from clintrai.models.api_models import PagedStudies, Study
from clintrai.api.exceptions import NotFoundError


@pytest.mark.asyncio
async def test_list_studies_live():
    """Test listing studies from live API."""
    async with create_hybrid_client() as client:
        # Get a small page of studies
        result = await studies.list_studies(
            client,
            page_size=5,
            count_total=True
        )
        
        assert isinstance(result, PagedStudies)
        assert len(result.studies) <= 5
        assert result.total_count > 0
        
        # Check that studies have expected fields
        if result.studies:
            study = result.studies[0]
            assert study.protocolSection is not None
            assert study.protocolSection.identificationModule is not None
            assert study.protocolSection.identificationModule.nctId.startswith('NCT')


@pytest.mark.asyncio
async def test_list_studies_with_query_live():
    """Test searching studies with a query."""
    async with create_hybrid_client() as client:
        # Search for cancer studies
        result = await studies.list_studies(
            client,
            query="cancer",
            page_size=10,
            filter_overall_status=["RECRUITING"]
        )
        
        assert isinstance(result, PagedStudies)
        # Should find some cancer studies
        assert len(result.studies) > 0
        
        # Verify they are recruiting
        for study in result.studies:
            if hasattr(study, 'overall_status'):
                assert study.overall_status == "RECRUITING"


@pytest.mark.asyncio
async def test_fetch_specific_study_live():
    """Test fetching a known study."""
    async with create_hybrid_client() as client:
        # First get a study ID from the list
        studies_list = await studies.list_studies(client, page_size=1)
        
        if studies_list.studies:
            nct_id = studies_list.studies[0].protocolSection.identificationModule.nctId
            
            # Now fetch that specific study
            study = await studies.fetch_study(client, nct_id)
            
            assert isinstance(study, Study)
            assert study.protocolSection.identificationModule.nctId == nct_id
            
            # Check for common fields
            assert study.protocolSection is not None


@pytest.mark.asyncio
async def test_pagination_live():
    """Test pagination functionality."""
    async with create_hybrid_client() as client:
        # Get first page
        page1 = await studies.list_studies(
            client,
            page_size=10,
            count_total=True
        )
        
        assert len(page1.studies) == 10
        assert page1.next_page_token is not None
        
        # Get second page
        page2 = await studies.list_studies(
            client,
            page_size=10,
            page_token=page1.next_page_token
        )
        
        assert len(page2.studies) <= 10
        
        # Ensure different studies
        page1_ids = {s.protocolSection.identificationModule.nctId for s in page1.studies}
        page2_ids = {s.protocolSection.identificationModule.nctId for s in page2.studies}
        assert len(page1_ids & page2_ids) == 0  # No overlap


@pytest.mark.asyncio
async def test_get_metadata_live():
    """Test getting metadata from live API."""
    async with create_hybrid_client() as client:
        metadata = await studies.get_study_metadata(client)
        
        # Metadata is a list of dictionaries describing the data structure
        assert isinstance(metadata, list)
        assert len(metadata) > 0
        assert "name" in metadata[0]


@pytest.mark.asyncio
async def test_search_areas_live():
    """Test searching areas (conditions, interventions)."""
    async with create_hybrid_client() as client:
        # Get all search areas
        result = await studies.search_areas(client)
        
        # Should return a list of search area documents
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Each document should have areas
        for doc in result:
            assert hasattr(doc, 'areas')
            assert hasattr(doc, 'name')


@pytest.mark.asyncio
async def test_get_enums_live():
    """Test getting enumeration values."""
    async with create_hybrid_client() as client:
        enums = await studies.get_enums(client)
        
        # Should return a list of enum definitions
        assert isinstance(enums, list)
        assert len(enums) > 0
        
        # Each enum should have the expected structure
        for enum_def in enums:
            assert hasattr(enum_def, 'type')
            assert hasattr(enum_def, 'values')
            assert hasattr(enum_def, 'pieces')


@pytest.mark.asyncio
async def test_error_handling_live():
    """Test error handling with invalid study ID."""
    async with create_hybrid_client() as client:
        with pytest.raises(NotFoundError):
            # This NCT ID should not exist
            await studies.fetch_study(client, "NCT99999999")


@pytest.mark.asyncio
@pytest.mark.slow
async def test_large_page_size_live():
    """Test handling larger page sizes."""
    async with create_hybrid_client() as client:
        # Request 100 studies
        result = await studies.list_studies(
            client,
            page_size=100,
            fields=["NCTId", "BriefTitle"]  # Limit fields to reduce response size
        )
        
        assert isinstance(result, PagedStudies)
        assert len(result.studies) <= 100
        
        # All studies should have the basic structure
        for study in result.studies:
            assert study.protocolSection is not None
            assert study.protocolSection.identificationModule is not None