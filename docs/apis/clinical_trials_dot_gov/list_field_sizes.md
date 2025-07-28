# ClinicalTrials.gov API - Field Sizes Stats Endpoint

## GET /stats/field/sizes

Sizes of list/array fields.

To search studies by a list field size, use `AREA[FieldName:size]` search operator. For example, `AREA[Phase:size] 2` query finds studies with 2 phases.

**API Server:** `https://beta-ut.clinicaltrials.gov/api/v2`  
**Authentication:** Not Required

## Request Parameters

### Query String Parameters

| Parameter | Type | Description | Examples |
|-----------|------|-------------|----------|
| `fields` | array of string | Filter by piece names or field paths of leaf fields. Must be non-empty comma- or pipe-separated list if specified. If unspecified, all available stats will be returned. | `["Phase"]`, `["Condition", "Intervention"]`, `["protocolSection.armsInterventionsModule.armGroups.interventionNames"]` |

**Note:** See Data Structure documentation for the complete list of available field values.

## Response Format

### JSON Response Structure

The endpoint returns an array of field size statistics objects, each containing size distribution data for list/array fields.

```json
[
  {
    "field": "string",
    "maxSize": 0,
    "minSize": 0,
    "piece": "string",
    "topSizes": [
      {
        "size": 0,
        "studiesCount": 0
      }
    ],
    "uniqueSizesCount": 0
  }
]
```

### Field Size Statistics Object Properties

| Property | Type | Description |
|----------|------|-------------|
| `field` | string | Name or path of the list/array field |
| `maxSize` | integer | Maximum number of items found in this field across all studies |
| `minSize` | integer | Minimum number of items found in this field across all studies |
| `piece` | string | Name of the data piece this field belongs to |
| `topSizes` | array of object | Most common list sizes and their occurrence counts |
| `uniqueSizesCount` | integer | Total number of different list sizes observed for this field |

#### Top Size Object Properties

| Property | Type | Description |
|----------|------|-------------|
| `size` | integer | Number of items in the list/array |
| `studiesCount` | integer | Number of studies that have this specific list size |

## Usage Examples

### Get All Field Size Statistics
```
GET /stats/field/sizes
```

### Get Statistics for Specific Fields
```
GET /stats/field/sizes?fields=Phase,Condition
```

### Get Statistics for Nested Array Fields
```
GET /stats/field/sizes?fields=protocolSection.armsInterventionsModule.interventions
```

### Multiple Field Analysis
```
GET /stats/field/sizes?fields=Phase,Condition,Intervention,PrimaryOutcome
```

## Search Integration

Use the size statistics to construct targeted searches:

### Find Studies with Specific List Sizes
```
# Find studies with exactly 2 phases
GET /studies?query.term=AREA[Phase:size] 2

# Find studies with 3 or more conditions  
GET /studies?query.term=AREA[Condition:size]RANGE[3,MAX]

# Find studies with single intervention
GET /studies?query.term=AREA[Intervention:size] 1
```

### Range-Based Size Searches
```
# Find studies with 1-3 primary outcomes
GET /studies?query.term=AREA[PrimaryOutcome:size]RANGE[1,3]

# Find studies with many conditions (5+)
GET /studies?query.term=AREA[Condition:size]RANGE[5,MAX]
```

## Use Cases

This endpoint is useful for:

- **Study Complexity Analysis**: Understanding how complex studies are based on number of conditions, interventions, etc.
- **Search Query Optimization**: Building size-based filters for finding studies with specific characteristics
- **Data Quality Assessment**: Identifying fields that may have data quality issues (unusually large or small lists)
- **Research Design Analysis**: Understanding typical patterns in study design (e.g., how many arms, outcomes, etc.)
- **Database Performance**: Planning for fields that may have large arrays that could impact performance
- **UI Design**: Understanding typical list sizes to design appropriate user interfaces
- **Data Validation**: Setting reasonable bounds for list field validation
- **Comparative Research**: Finding studies with similar complexity profiles

## Example Response Analysis

### Understanding Study Complexity
```javascript
// Example: Analyze Condition field sizes
{
  "field": "Condition",
  "maxSize": 15,                    // Some study has 15 conditions
  "minSize": 1,                     // Minimum is 1 condition
  "piece": "ConditionsModule",
  "topSizes": [
    {
      "size": 1,
      "studiesCount": 25000         // Most studies have 1 condition
    },
    {
      "size": 2, 
      "studiesCount": 8000          // 8000 studies have 2 conditions
    },
    {
      "size": 3,
      "studiesCount": 3000          // Fewer studies have 3+ conditions
    }
  ],
  "uniqueSizesCount": 12            // 12 different list sizes observed
}
```

### Data Insights
- **Small `minSize` and large `maxSize`**: Wide variation in study complexity
- **Concentrated `topSizes`**: Most studies follow common patterns
- **High `uniqueSizesCount`**: Field shows diverse usage patterns

## Integration with Other Endpoints

Use size statistics to enhance:

- **GET /studies** - Apply size-based filters using `AREA[FieldName:size]` syntax
- **GET /stats/field/values** - Compare value distributions with size distributions
- **Research queries** - Target studies with specific complexity profiles
- **Data analysis** - Understand relationships between study size and other characteristics

## Advanced Analysis Examples

### Study Design Complexity
```
# Analyze intervention complexity
GET /stats/field/sizes?fields=protocolSection.armsInterventionsModule.interventions

# Analyze outcome complexity  
GET /stats/field/sizes?fields=protocolSection.outcomesModule.primaryOutcomes,protocolSection.outcomesModule.secondaryOutcomes
```

### Geographic Distribution
```
# Analyze location list sizes
GET /stats/field/sizes?fields=protocolSection.contactsLocationsModule.locations
```

### Reference and Documentation
```
# Analyze reference list sizes
GET /stats/field/sizes?fields=protocolSection.referencesModule.references
```

## Response Codes

| Code | Description |
|------|-------------|
| 200 | OK - Field size statistics returned successfully |
| 400 | Bad Request - Invalid field names specified |

## Notes

- Only list/array fields are included in the response
- Field paths support nested notation for complex data structures
- Size statistics help identify both typical patterns and outliers
- Use the `AREA[FieldName:size]` operator in search queries to filter by list sizes
- Statistics reflect the current state of the database
- Zero-sized lists (empty arrays) are included in the `minSize` calculation if present
