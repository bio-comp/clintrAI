"""Integration tests for stats API - these hit the live API."""

import pytest
from clintrai.api.hybrid_client import create_hybrid_client
from clintrai.api import stats


@pytest.mark.asyncio
async def test_get_size_stats_live():
    """Test getting size statistics from live API."""
    async with create_hybrid_client() as client:
        size_stats = await stats.get_size_stats(client)
        
        assert isinstance(size_stats, dict)
        # Should have total studies count
        assert any(key in size_stats for key in ['total', 'totalStudies', 'total_studies'])
        
        # The value should be a reasonable number
        total_key = next(k for k in ['total', 'totalStudies', 'total_studies'] if k in size_stats)
        assert size_stats[total_key] > 100000  # ClinicalTrials.gov has hundreds of thousands of studies


@pytest.mark.asyncio
async def test_get_version_live():
    """Test getting version information from live API."""
    async with create_hybrid_client() as client:
        version_info = await stats.get_version(client)
        
        assert isinstance(version_info, dict)
        # Should have version data
        assert len(version_info) > 0
        
        # Common version fields
        assert any(key in version_info for key in ['version', 'apiVersion', 'api_version', 'dataVersion', 'data_version'])


@pytest.mark.asyncio
async def test_get_field_values_stats_live():
    """Test getting field value statistics from live API."""
    async with create_hybrid_client() as client:
        # Get stats for overall status field
        field_stats = await stats.get_field_values_stats(client, fields=["OverallStatus"])
        
        assert isinstance(field_stats, list)
        assert len(field_stats) > 0
        
        # Check the structure of the response
        first_stat = field_stats[0]
        assert "field" in first_stat
        assert "topValues" in first_stat or "values" in first_stat


@pytest.mark.asyncio
async def test_get_field_sizes_stats_live():
    """Test getting field size statistics from live API."""
    async with create_hybrid_client() as client:
        # Get stats for specific fields
        field_sizes = await stats.get_field_sizes_stats(client, fields=["Phase"])
        
        assert isinstance(field_sizes, list)
        assert len(field_sizes) > 0
        
        # Check the structure of the response
        first_stat = field_sizes[0]
        assert "field" in first_stat
        assert "uniqueSizesCount" in first_stat