# ClinicalTrials.gov API - Version Endpoint

## GET /version

API and data versions.

API version follows **Semantic Versioning 2.0.0** Schema. Data version is UTC timestamp in `yyyy-MM-dd'T'HH:mm:ss` format.

**API Server:** `https://beta-ut.clinicaltrials.gov/api/v2`  
**Authentication:** Not Required

## Request Parameters

This endpoint does not require any parameters.

## Response Format

### JSON Response Structure

The endpoint returns version information for both the API and the underlying data.

```json
{
  "apiVersion": "string",
  "dataTimestamp": "string"
}
```

### Response Object Properties

| Property | Type | Description | Format |
|----------|------|-------------|---------|
| `apiVersion` | string | Current version of the API following Semantic Versioning 2.0.0 | `MAJOR.MINOR.PATCH` (e.g., "2.1.0") |
| `dataTimestamp` | string | UTC timestamp indicating when the data was last updated | `yyyy-MM-dd'T'HH:mm:ss` (e.g., "2025-07-27T14:30:00") |

## Usage Examples

### Get Current Version Information
```
GET /version
```

### Example Response
```json
{
  "apiVersion": "2.1.0",
  "dataTimestamp": "2025-07-27T14:30:00"
}
```

## Use Cases

This endpoint is useful for:

- **API Compatibility Checking**: Ensuring your application is compatible with the current API version
- **Change Management**: Tracking API updates and planning for version migrations
- **Data Freshness Validation**: Understanding how recent the underlying study data is
- **Caching Strategy**: Using data timestamp to implement intelligent cache invalidation
- **System Monitoring**: Monitoring for API updates and data refreshes
- **Documentation**: Displaying current version information in applications
- **Debugging**: Including version information in error reports and support requests
- **Compliance**: Tracking data currency for regulatory or research requirements

## Semantic Versioning (API Version)

The API version follows [Semantic Versioning 2.0.0](https://semver.org/) principles:

- **MAJOR**: Incremented for incompatible API changes
- **MINOR**: Incremented for backwards-compatible functionality additions
- **PATCH**: Incremented for backwards-compatible bug fixes

### Version Interpretation Examples
- `2.0.0` → `2.1.0`: New features added, backwards compatible
- `2.1.0` → `2.1.1`: Bug fixes, backwards compatible  
- `2.1.1` → `3.0.0`: Breaking changes, may require code updates

## Data Timestamp

The `dataTimestamp` indicates when the study data was last updated in the system:

- **Format**: ISO 8601 datetime format in UTC
- **Precision**: Seconds
- **Use**: Determine data freshness for caching and compliance purposes

## Implementation Examples

### Version Checking in Applications
```javascript
// Check API compatibility
async function checkApiCompatibility() {
  const response = await fetch('/version');
  const { apiVersion } = await response.json();
  
  const [major, minor, patch] = apiVersion.split('.').map(Number);
  
  if (major !== 2) {
    console.warn('API version mismatch - may need updates');
  }
}
```

### Cache Invalidation Strategy
```javascript
// Use data timestamp for cache management
async function shouldRefreshCache(lastCacheTime) {
  const response = await fetch('/version');
  const { dataTimestamp } = await response.json();
  
  return new Date(dataTimestamp) > new Date(lastCacheTime);
}
```

### Error Reporting
```javascript
// Include version info in error reports
async function reportError(error) {
  const { apiVersion, dataTimestamp } = await fetch('/version').then(r => r.json());
  
  console.error('Error occurred:', {
    error: error.message,
    apiVersion,
    dataTimestamp,
    timestamp: new Date().toISOString()
  });
}
```

## Integration with Other Endpoints

Use version information to:

- **Monitor Data Currency**: Compare `dataTimestamp` with your last data sync
- **Plan API Updates**: Track `apiVersion` changes for maintenance windows
- **Debug Issues**: Include version info when reporting problems with other endpoints
- **Cache Management**: Use `dataTimestamp` to invalidate study data caches

## Best Practices

### Regular Version Monitoring
```javascript
// Check versions periodically
setInterval(async () => {
  const version = await fetch('/version').then(r => r.json());
  console.log('Current API version:', version.apiVersion);
  console.log('Data last updated:', version.dataTimestamp);
}, 3600000); // Check hourly
```

### Graceful Version Handling
```javascript
// Handle version compatibility gracefully
async function makeApiCall(endpoint) {
  const { apiVersion } = await fetch('/version').then(r => r.json());
  
  if (!isCompatibleVersion(apiVersion)) {
    throw new Error(`Incompatible API version: ${apiVersion}`);
  }
  
  return fetch(endpoint);
}
```

## Response Codes

| Code | Description |
|------|-------------|
| 200 | OK - Version information returned successfully |

## Notes

- This endpoint provides essential metadata about the API and data
- The `dataTimestamp` reflects the most recent data update across all studies
- API version changes are announced through official channels
- Use this endpoint for health checks and system monitoring
- Version information should be included in bug reports and support requests
- Consider implementing automatic version checking in production applications