# ClinicalTrials.gov API - Studies Enums Endpoint

## GET /studies/enums

Returns enumeration types and their values.

Every item of the returning array represents enum type and contains the following properties:

- `type` - enum type name
- `pieces` - array of names of all data pieces having the enum type
- `values` - all available values of the enum; every item contains the following properties:
  - `value` - data value
  - `legacyValue` - data value in legacy API
  - `exceptions` - map from data piece name to legacy value when different from `legacyValue` (some data pieces had special enum values in legacy API)

**API Server:** `https://beta-ut.clinicaltrials.gov/api/v2`  
**Authentication:** Not Required

## Request Parameters

This endpoint does not require any parameters.

## Response Format

### JSON Response Structure

The endpoint returns an array of enumeration type objects, each containing the enum type name, associated data pieces, and all possible values.

```json
[
  {
    "pieces": [
      "string"
    ],
    "type": "string",
    "values": [
      {
        "exceptions": {},
        "legacyValue": "string",
        "value": "string"
      }
    ]
  }
]
```

### Object Structure

#### Enumeration Type Object

| Property | Type | Description |
|----------|------|-------------|
| `pieces` | array of string | Array of data piece names that use this enum type |
| `type` | string | Name of the enumeration type |
| `values` | array of object | Array of all possible values for this enum type |

#### Enumeration Value Object

| Property | Type | Description |
|----------|------|-------------|
| `exceptions` | object | Map from data piece name to legacy value when different from `legacyValue`. Used when some data pieces had special enum values in legacy API |
| `legacyValue` | string | The value as it appeared in the legacy API |
| `value` | string | The current data value |

## Usage Examples

### Get All Enumeration Types
```
GET /studies/enums
```

## Use Cases

This endpoint is useful for:

- **Data Validation**: Understanding valid values for enumerated fields before submitting queries
- **Form Building**: Creating dropdown menus and selection lists with valid options
- **API Migration**: Mapping between legacy API values and current API values
- **Documentation**: Understanding all possible values for specific data fields
- **Query Construction**: Knowing valid filter values for enumerated fields
- **Data Processing**: Converting between legacy and current enum formats
- **Field Validation**: Ensuring data quality by validating against known enum values

## Integration with Other Endpoints

The enum values returned by this endpoint can be used with:

- **GET /studies** - Use enum values in filter parameters (e.g., `filter.overallStatus=RECRUITING`)
- **GET /studies/{nctId}** - Understanding possible values in response fields
- **GET /studies/metadata** - Cross-reference with field metadata to understand which fields are enumerated

## Example Usage Scenarios

### Filtering Studies by Status
```
# First get enum values for status
GET /studies/enums

# Use the enum values in filters
GET /studies?filter.overallStatus=RECRUITING,COMPLETED
```

### Building UI Components
```javascript
// Use enum data to populate dropdown options
const statusOptions = enumData
  .find(enum => enum.type === 'OverallStatus')
  .values
  .map(val => ({ label: val.value, value: val.value }));
```

### Legacy API Migration
```javascript
// Convert legacy values to current values
const legacyToCurrentMap = enumData
  .find(enum => enum.type === 'StudyPhase')
  .values
  .reduce((map, val) => {
    map[val.legacyValue] = val.value;
    return map;
  }, {});
```

## Response Codes

| Code | Description |
|------|-------------|
| 200 | OK - Enumeration types and values returned successfully |

## Notes

- The `exceptions` property handles cases where different data pieces used different enum values in the legacy API
- This endpoint is particularly valuable for maintaining backward compatibility while transitioning from legacy systems
- Enum values are case-sensitive and should be used exactly as returned by this endpoint
