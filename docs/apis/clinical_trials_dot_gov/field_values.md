# ClinicalTrials.gov API - Field Values Stats Endpoint

## GET /stats/field/values

Value statistics of the study leaf fields.

**API Server:** `https://beta-ut.clinicaltrials.gov/api/v2`  
**Authentication:** Not Required

## Request Parameters

### Query String Parameters

| Parameter | Type | Description | Examples |
|-----------|------|-------------|----------|
| `types` | array of string | Filter by field types | `["ENUM", "BOOLEAN"]`, `["INTEGER", "NUMBER"]` |
| `fields` | array of string | Filter by piece names or field paths of leaf fields. Must be non-empty comma- or pipe-separated list if specified. | `["Phase"]`, `["Condition", "InterventionName"]`, `["protocolSection.armsInterventionsModule.armGroups.interventionNames"]` |

#### Valid Field Types

- `ENUM` - Enumerated values
- `STRING` - Text strings  
- `DATE` - Date values
- `INTEGER` - Whole numbers
- `NUMBER` - Numeric values (including decimals)
- `BOOLEAN` - True/false values

## Response Format

### JSON Response Structure

The endpoint returns an array of field statistics objects, each containing value distribution data for a specific field.

```json
[
  {
    "field": "string",
    "missingStudiesCount": 0,
    "piece": "string",
    "topValues": [
      {
        "studiesCount": 0,
        "value": "string"
      }
    ],
    "type": "ENUM",
    "uniqueValuesCount": 0
  }
]
```

### Field Statistics Object Properties

| Property | Type | Description |
|----------|------|-------------|
| `field` | string | Name or path of the field |
| `missingStudiesCount` | integer | Number of studies that don't have a value for this field |
| `piece` | string | Name of the data piece this field belongs to |
| `topValues` | array of object | Most common values and their occurrence counts |
| `type` | string | Data type of the field (ENUM, STRING, DATE, etc.) |
| `uniqueValuesCount` | integer | Total number of unique values found for this field |

#### Top Value Object Properties

| Property | Type | Description |
|----------|------|-------------|
| `studiesCount` | integer | Number of studies that have this specific value |
| `value` | string | The actual field value |

## Usage Examples

### Get All Field Statistics
```
GET /stats/field/values
```

### Filter by Field Types
```
GET /stats/field/values?types=ENUM,BOOLEAN
```

### Get Statistics for Specific Fields
```
GET /stats/field/values?fields=Phase,OverallStatus
```

### Combine Type and Field Filters
```
GET /stats/field/values?types=ENUM&fields=Phase,OverallStatus,Sex
```

### Get Statistics for Nested Fields
```
GET /stats/field/values?fields=protocolSection.designModule.phases
```

## Use Cases

This endpoint is useful for:

- **Data Quality Analysis**: Understanding completeness and distribution of field values
- **Search Optimization**: Identifying most common values for search filters and suggestions
- **UI/UX Design**: Building informed dropdown menus and filter options based on actual data distribution
- **Data Validation**: Understanding expected value ranges and patterns for validation rules
- **Research Planning**: Identifying fields with good data coverage for research queries
- **API Integration**: Planning field usage based on data availability and distribution
- **Data Governance**: Monitoring data quality and identifying fields with missing or inconsistent data
- **Performance Optimization**: Understanding which field values are most commonly queried

## Example Response Analysis

### Understanding Field Coverage
```javascript
// Example: Analyze Phase field statistics
{
  "field": "Phase",
  "missingStudiesCount": 5000,      // 5000 studies don't specify phase
  "piece": "DesignModule", 
  "topValues": [
    {
      "studiesCount": 15000,
      "value": "Phase 3"             // Most common phase
    },
    {
      "studiesCount": 12000, 
      "value": "Phase 2"
    },
    {
      "studiesCount": 8000,
      "value": "Phase 1"
    }
  ],
  "type": "ENUM",
  "uniqueValuesCount": 8            // 8 different phase values total
}
```

### Data Quality Insights
- **High `missingStudiesCount`**: Field may not be required or consistently filled
- **Large `uniqueValuesCount`**: Field may need standardization or validation
- **Concentrated `topValues`**: Good candidates for filter options and search suggestions

## Integration with Other Endpoints

Use this data to optimize:

- **GET /studies** - Build effective filters using common values from `topValues`
- **GET /studies/enums** - Cross-reference enum statistics with available enum values
- **Search interfaces** - Populate filter dropdowns with most common values
- **Data validation** - Set up validation rules based on observed value patterns

## Advanced Filtering Examples

### Analyze String Fields for Data Quality
```
GET /stats/field/values?types=STRING
```

### Focus on Core Study Information
```
GET /stats/field/values?fields=BriefTitle,OfficialTitle,BriefSummary
```

### Examine Enrollment and Demographics
```
GET /stats/field/values?fields=EnrollmentCount,Sex,MinimumAge,MaximumAge
```

## Response Codes

| Code | Description |
|------|-------------|
| 200 | OK - Field value statistics returned successfully |
| 400 | Bad Request - Invalid field names or types specified |

## Notes

- Field paths support nested notation (e.g., `protocolSection.designModule.phases`)
- See Data Structure documentation for complete list of available field paths
- Statistics reflect the current state of the database
- `topValues` typically shows the most frequent values (exact number may vary)
- Use this data to inform query strategies and user interface design decisions
