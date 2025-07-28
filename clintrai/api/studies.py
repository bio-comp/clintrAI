"""Functions for study-related API endpoints."""

from pydantic import BaseModel
from clintrai.api.protocols import HTTPClientProtocol
from clintrai.models.api_models import PagedStudies, Study


class SearchArea(BaseModel):
    """Individual search area definition."""
    name: str
    ui_label: str | None = None
    param: str | None = None
    parts: list[dict] | None = None


class SearchAreaDocument(BaseModel):
    """Document containing search areas."""
    name: str
    areas: list[SearchArea]


class EnumValue(BaseModel):
    """Individual enum value."""
    value: str
    legacy_value: str | None = None


class EnumDefinition(BaseModel):
    """Definition of an enum type."""
    type: str
    values: list[EnumValue]
    pieces: list[str]


# Type aliases for cleaner return types
StudyMetadata = list[dict]  # Metadata returns a list of dictionaries
SearchAreasResponse = list[SearchAreaDocument]  # Search areas returns list of documents  
EnumsResponse = list[EnumDefinition]  # Enums returns list of enum definitions


async def list_studies(
    client: HTTPClientProtocol,
    *,
    query: str | None = None,
    page_token: str | None = None,
    page_size: int = 10,
    count_total: bool = False,
    sort: str = "LastUpdatePostDate:desc",
    fields: list[str] | None = None,
    # Filter parameters
    filter_overall_status: list[str] | None = None,
    filter_geo: str | None = None,
    filter_ids: list[str] | None = None,
    filter_advanced: str | None = None,
    filter_synonyms: list[str] | None = None,
) -> PagedStudies:
    """List studies matching query and filter parameters.
    
    Args:
        client: HTTP client implementing HTTPClientProtocol
        query: Search query in Essie expression syntax
        page_token: Token for pagination
        page_size: Number of studies per page (max 1000)
        count_total: Whether to include total count
        sort: Sort order (e.g., "LastUpdatePostDate:desc")
        fields: Fields to include in response
        filter_overall_status: Filter by overall status
        filter_geo: Geographic filter
        filter_ids: Filter by study IDs
        filter_advanced: Advanced filter expression
        filter_synonyms: Filter by synonyms
        
    Returns:
        PagedStudies containing studies and pagination info
    """
    # Build all potential parameters, filtering out None values
    raw_params = {
        "query.term": query,
        "pageToken": page_token,
        "fields": ",".join(fields) if fields else None,
        "filter.overallStatus": ",".join(filter_overall_status) if filter_overall_status else None,
        "filter.geo": filter_geo,
        "filter.ids": ",".join(filter_ids) if filter_ids else None,
        "filter.advanced": filter_advanced,
        "filter.synonyms": ",".join(filter_synonyms) if filter_synonyms else None,
    }
    
    # Filter out None values and add fixed parameters
    params = {k: v for k, v in raw_params.items() if v is not None}
    params.update({
        "format": "json",
        "pageSize": min(page_size, 1000),
        "countTotal": count_total,
        "sort": sort,
    })
    
    response = await client.get("studies", params=params)
    return PagedStudies.model_validate(response.json())


async def fetch_study(
    client: HTTPClientProtocol,
    nct_id: str,
    *,
    fields: list[str] | None = None,
    format: str = "json",
) -> Study:
    """Fetch a single study by NCT ID.
    
    Args:
        client: HTTP client implementing HTTPClientProtocol
        nct_id: NCT identifier (e.g., "NCT12345678")
        fields: Fields to include in response
        format: Response format (json, xml)
        
    Returns:
        Study containing study details
    """
    params: dict[str, str] = {"format": format}
    if fields:
        params["fields"] = ",".join(fields)
        
    response = await client.get(f"studies/{nct_id}", params=params)
    return Study.model_validate(response.json())


async def get_study_metadata(client: HTTPClientProtocol) -> StudyMetadata:
    """Get metadata about studies.
    
    Args:
        client: HTTP client implementing HTTPClientProtocol
        
    Returns:
        StudyMetadata containing metadata information
    """
    response = await client.get("studies/metadata")
    return response.json()  # Returns list[dict] directly


async def search_areas(
    client: HTTPClientProtocol,
) -> SearchAreasResponse:
    """Get available search areas.
    
    Args:
        client: HTTP client implementing HTTPClientProtocol
        
    Returns:
        SearchAreasResponse containing search areas
    """
    response = await client.get("studies/search-areas")
    json_response = response.json()
    return [SearchAreaDocument.model_validate(doc) for doc in json_response]


async def get_enums(client: HTTPClientProtocol) -> EnumsResponse:
    """Get enumeration values for various fields.
    
    Args:
        client: HTTP client implementing HTTPClientProtocol
        
    Returns:
        EnumsResponse containing enumeration data
    """
    response = await client.get("studies/enums")
    json_response = response.json()
    return [EnumDefinition.model_validate(enum_def) for enum_def in json_response]