# ClinicalTrials.gov API - Studies Metadata Endpoint

## GET /studies/metadata

Returns study data model fields.

**API Server:** `https://beta-ut.clinicaltrials.gov/api/v2`  
**Authentication:** Not Required

## Request Parameters

### Query String Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `includeIndexedOnly` | boolean | `false` | Include indexed-only fields, if `true` |
| `includeHistoricOnly` | boolean | `false` | Include fields available only in historic data, if `true` |

## Response Format

### JSON Response Structure

The endpoint returns an array of field objects, each containing information about available study data model fields.

```json
[
  {
    "altPieceNames": [
      "string"
    ],
    "children": [
      {}
    ],
    "dedLink": {
      "label": "string",
      "url": "string"
    },
    "description": "string",
    "historicOnly": false,
    "indexedOnly": false,
    "isEnum": false,
    "maxChars": 0,
    "name": "string",
    "nested": false,
    "piece": "string",
    "rules": "string",
    "sourceType": "string",
    "synonyms": false,
    "title": "string",
    "type": "string"
  }
]
```

### Field Object Properties

| Property | Type | Description |
|----------|------|-------------|
| `altPieceNames` | array of string | Alternative names for the piece/field |
| `children` | array of object | Child fields (for nested structures) |
| `dedLink` | object | Data element dictionary link information |
| `dedLink.label` | string | Label for the dictionary link |
| `dedLink.url` | string | URL to the data element dictionary |
| `description` | string | Description of the field |
| `historicOnly` | boolean | Whether field is available only in historic data |
| `indexedOnly` | boolean | Whether field is indexed-only |
| `isEnum` | boolean | Whether field has enumerated values |
| `maxChars` | integer | Maximum character length for the field |
| `name` | string | Field name |
| `nested` | boolean | Whether field is nested |
| `piece` | string | Piece name the field belongs to |
| `rules` | string | Validation rules for the field |
| `sourceType` | string | Source type of the field |
| `synonyms` | boolean | Whether field has synonyms |
| `title` | string | Display title of the field |
| `type` | string | Data type of the field |

## Usage Examples

### Get All Fields
```
GET /studies/metadata
```

### Include Indexed-Only Fields
```
GET /studies/metadata?includeIndexedOnly=true
```

### Include Historic Fields
```
GET /studies/metadata?includeHistoricOnly=true
```

### Include Both Indexed-Only and Historic Fields
```
GET /studies/metadata?includeIndexedOnly=true&includeHistoricOnly=true
```

## Use Cases

This endpoint is useful for:

- **API Integration**: Understanding available fields for constructing queries to other endpoints
- **Data Dictionary**: Getting comprehensive information about all study data fields
- **Field Validation**: Understanding field types, character limits, and validation rules
- **Dynamic UI Generation**: Building user interfaces that adapt to available fields
- **Documentation**: Generating documentation about available study data fields

## Response Codes

| Code | Description |
|------|-------------|
| 200 | OK - Metadata returned successfully |
