# ClinicalTrials.gov API - Studies Search Areas Endpoint

## GET /studies/search-areas

Search Docs and their Search Areas.

**API Server:** `https://beta-ut.clinicaltrials.gov/api/v2`  
**Authentication:** Not Required

## Request Parameters

This endpoint does not require any parameters.

## Response Format

### JSON Response Structure

The endpoint returns an array of search document objects, each containing available search areas and their configurations.

```json
[
  {
    "areas": [
      {
        "name": "string",
        "param": "string",
        "parts": [
          {
            "isEnum": false,
            "isSynonyms": false,
            "pieces": [
              "string"
            ],
            "type": "string",
            "weight": 0
          }
        ],
        "uiLabel": "string"
      }
    ],
    "name": "string"
  }
]
```

### Object Structure

#### Search Document Object

| Property | Type | Description |
|----------|------|-------------|
| `areas` | array of object | Array of search areas available in this document |
| `name` | string | Name of the search document |

#### Search Area Object

| Property | Type | Description |
|----------|------|-------------|
| `name` | string | Internal name of the search area |
| `param` | string | Parameter name used in API queries |
| `parts` | array of object | Array of parts that make up this search area |
| `uiLabel` | string | User-friendly label for display in interfaces |

#### Search Part Object

| Property | Type | Description |
|----------|------|-------------|
| `isEnum` | boolean | Whether this part has enumerated values |
| `isSynonyms` | boolean | Whether this part supports synonym searching |
| `pieces` | array of string | Array of data pieces/fields included in this part |
| `type` | string | Type of search part |
| `weight` | integer | Weight/priority of this part in search ranking |

## Usage Examples

### Get All Search Areas
```
GET /studies/search-areas
```

## Use Cases

This endpoint is useful for:

- **Search Interface Development**: Understanding available search areas for building search forms
- **Query Construction**: Knowing which parameters and areas are available for search queries
- **API Integration**: Getting the complete list of searchable fields and their configurations
- **Documentation**: Understanding the search capabilities of the studies API
- **Dynamic Search**: Building adaptive search interfaces that respond to available search areas
- **Search Optimization**: Understanding field weights and types for optimizing search queries

## Related Endpoints

This endpoint provides metadata that can be used with:

- `GET /studies` - Use the `param` values as query parameters (e.g., `query.cond`, `query.term`)
- `GET /studies/metadata` - Get detailed field information for the pieces referenced in search areas

## Example Search Area Usage

Based on the search areas returned by this endpoint, you can construct queries like:

```
# If a search area has param "cond"
GET /studies?query.cond=diabetes

# If a search area has param "term"  
GET /studies?query.term=randomized

# If a search area has param "locn"
GET /studies?query.locn=california
```

## Response Codes

| Code | Description |
|------|-------------|
| 200 | OK - Search areas returned successfully |
