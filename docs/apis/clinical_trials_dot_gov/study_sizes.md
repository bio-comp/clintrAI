# ClinicalTrials.gov API - Study Sizes Stats Endpoint

## GET /stats/size

Statistics of study JSON sizes.

**API Server:** `https://beta-ut.clinicaltrials.gov/api/v2`  
**Authentication:** Not Required

## Request Parameters

This endpoint does not require any parameters.

## Response Format

### JSON Response Structure

The endpoint returns statistics about the JSON size distribution of studies in the database.

```json
{
  "averageSizeBytes": 0,
  "largestStudies": [
    {
      "id": "string",
      "sizeBytes": 0
    }
  ],
  "percentiles": {},
  "ranges": [
    {
      "sizeRange": "string",
      "studiesCount": 0
    }
  ],
  "totalStudies": 0
}
```

### Response Object Properties

| Property | Type | Description |
|----------|------|-------------|
| `averageSizeBytes` | integer | Average size of study JSON data in bytes |
| `largestStudies` | array of object | List of studies with the largest JSON sizes |
| `percentiles` | object | Size percentile data (e.g., 50th, 75th, 90th percentiles) |
| `ranges` | array of object | Distribution of studies across different size ranges |
| `totalStudies` | integer | Total number of studies included in the statistics |

#### Largest Studies Object

| Property | Type | Description |
|----------|------|-------------|
| `id` | string | NCT ID of the study |
| `sizeBytes` | integer | Size of the study JSON data in bytes |

#### Size Range Object

| Property | Type | Description |
|----------|------|-------------|
| `sizeRange` | string | Description of the size range (e.g., "0-10KB", "10-50KB") |
| `studiesCount` | integer | Number of studies that fall within this size range |

## Usage Examples

### Get Study Size Statistics
```
GET /stats/size
```

## Use Cases

This endpoint is useful for:

- **Performance Planning**: Understanding typical JSON payload sizes for performance optimization
- **Bandwidth Estimation**: Estimating network requirements for bulk data operations
- **Caching Strategy**: Planning cache sizes and storage requirements
- **API Rate Limiting**: Understanding the distribution of data sizes for rate limiting decisions
- **Infrastructure Sizing**: Determining appropriate server and storage capacity
- **Data Analysis**: Understanding the complexity distribution of clinical trial studies
- **Quality Monitoring**: Identifying unusually large studies that might need optimization
- **Client Application Design**: Planning for appropriate timeouts and memory allocation

## Example Response Analysis

### Understanding the Data
```javascript
// Example response analysis
{
  "averageSizeBytes": 15420,
  "largestStudies": [
    {
      "id": "NCT00000001",
      "sizeBytes": 125000
    }
  ],
  "percentiles": {
    "50": 12000,    // 50% of studies are smaller than 12KB
    "75": 20000,    // 75% of studies are smaller than 20KB
    "90": 35000,    // 90% of studies are smaller than 35KB
    "95": 50000     // 95% of studies are smaller than 50KB
  },
  "ranges": [
    {
      "sizeRange": "0-10KB",
      "studiesCount": 15000
    },
    {
      "sizeRange": "10-25KB", 
      "studiesCount": 8000
    }
  ],
  "totalStudies": 25000
}
```

### Performance Considerations

Based on the statistics, you can:

- **Set appropriate timeouts** for API calls based on percentile data
- **Plan pagination** strategies for bulk operations
- **Optimize field selection** using the `fields` parameter for large studies
- **Implement progressive loading** for studies in higher percentiles

## Integration with Other Endpoints

Use this data to optimize calls to:

- **GET /studies** - Plan appropriate `pageSize` parameters
- **GET /studies/{nctId}** - Set expectations for individual study retrieval times
- **Bulk operations** - Estimate total transfer times and storage requirements

## Response Codes

| Code | Description |
|------|-------------|
| 200 | OK - Study size statistics returned successfully |

## Notes

- Statistics are calculated across all studies in the database
- Sizes represent the full JSON response including all fields
- Use the `fields` parameter in other endpoints to reduce payload sizes when needed
- Percentile data helps understand the distribution beyond simple averages
- Regular monitoring of these statistics can help identify data growth trends
