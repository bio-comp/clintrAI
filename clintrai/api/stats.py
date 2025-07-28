"""Functions for statistics-related API endpoints."""

from clintrai.api.protocols import HTTPClientProtocol


async def get_size_stats(client: HTTPClientProtocol) -> dict[str, int]:
    """Get size statistics.
    
    Args:
        client: HTTP client implementing HTTPClientProtocol
        
    Returns:
        Dictionary containing size statistics
    """
    response = await client.get("stats/size")
    return response.json()


async def get_field_values_stats(
    client: HTTPClientProtocol,
    fields: list[str] | None = None,
    types: list[str] | None = None,
) -> list[dict]:
    """Get field value statistics.
    
    Args:
        client: HTTP client implementing HTTPClientProtocol
        fields: List of field names to get statistics for
        types: List of field types to filter by (ENUM, STRING, DATE, INTEGER, NUMBER, BOOLEAN)
        
    Returns:
        List of field value statistics objects
    """
    params = {}
    if fields:
        params["fields"] = ",".join(fields)
    if types:
        params["types"] = ",".join(types)
    
    response = await client.get("stats/field/values", params=params if params else None)
    return response.json()


async def get_field_sizes_stats(
    client: HTTPClientProtocol,
    fields: list[str] | None = None,
) -> list[dict]:
    """Get field size statistics.
    
    Args:
        client: HTTP client implementing HTTPClientProtocol
        fields: List of field names to get statistics for
        
    Returns:
        List of field size statistics objects
    """
    params = {}
    if fields:
        params["fields"] = ",".join(fields)
    
    response = await client.get("stats/field/sizes", params=params if params else None)
    return response.json()


async def get_version(client: HTTPClientProtocol) -> dict[str, str]:
    """Get API version information.
    
    Args:
        client: HTTP client implementing HTTPClientProtocol
        
    Returns:
        Dictionary containing version information
    """
    response = await client.get("version")
    return response.json()