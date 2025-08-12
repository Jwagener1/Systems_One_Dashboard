# InfluxDB Integration Guide

This guide explains how InfluxDB works, how data is structured, and how to effectively query and use it with this dashboard application.

## InfluxDB Fundamentals

InfluxDB is a time-series database optimized for handling timestamped data. Understanding its data model is crucial for effective querying.

### Key Concepts

- **Measurement**: Similar to a table name (e.g., `device_data`, `sensor_readings`)
- **Tags**: Indexed metadata for grouping/filtering (e.g., `location=JBH`, `device_id=DEMO1`)
- **Fields**: Actual numeric/string values being measured (e.g., `temperature=23.5`, `status=online`)
- **Timestamp**: When the data point was recorded (automatically added)
- **Bucket**: Container for related measurements (like a database)
- **Organization**: Top-level container for users and buckets

### Data Structure Example

```
Measurement: device_data
Tags: location=JBH, station=DEM0, company=DEMO
Fields: statistics_complete=478.0, storage_C_used_pct=85.2
Time: 2025-01-15T10:30:00Z
```

### Tags vs Fields

**Tags** (indexed, for grouping):
- Location identifiers: `location`, `station`, `company`
- Device metadata: `host`, `device_id`
- Categories: `message_type`, `topic`
- String values used for filtering and grouping

**Fields** (stored values, for analysis):
- Statistics: `statistics_complete`, `statistics_sent`, `statistics_total_items`
- Storage: `storage_C_used_pct`, `storage_D_free_gb`
- Performance metrics, sensor readings, counts
- Numeric or string values that change over time

## Querying with Flux

InfluxDB v2 uses Flux as its query language. Here are common patterns:

### Basic Query

```flux
from(bucket: "telemetry")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "device_data")
  |> filter(fn: (r) => r["location"] == "JBH")
```

### Time Ranges

```flux
// Last hour
|> range(start: -1h)

// Last 24 hours
|> range(start: -24h)

// Last week
|> range(start: -7d)

// Specific time range
|> range(start: 2025-01-01T00:00:00Z, stop: 2025-01-02T00:00:00Z)
```

### Filtering

```flux
// Single field
|> filter(fn: (r) => r["_field"] == "temperature")

// Multiple fields
|> filter(fn: (r) => r["_field"] == "temperature" or r["_field"] == "humidity")

// Tag values
|> filter(fn: (r) => r["location"] == "JBH")

// Multiple conditions
|> filter(fn: (r) => r["location"] == "JBH" and r["station"] == "DEM0")
```

### Aggregation

```flux
// Group by tag and calculate mean
from(bucket: "telemetry")
  |> range(start: -24h)
  |> filter(fn: (r) => r["_measurement"] == "device_data")
  |> group(columns: ["location"])
  |> mean(column: "_value")

// Time-based aggregation (hourly averages)
|> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
```

### Pivoting (for charts)

```flux
// Convert from long to wide format
from(bucket: "telemetry")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "device_data")
  |> filter(fn: (r) => r["_field"] == "temperature" or r["_field"] == "humidity")
  |> pivot(rowKey:["_time"], columnKey:["_field"], valueColumn:"_value")
```

## Data Discovery

Use the included discovery script to explore your InfluxDB schema:

```bash
# List all measurements, tags, and fields
python scripts/discover_influx.py --range=-24h

# Sample data from a specific measurement
python scripts/discover_influx.py --range=-24h --measurement-sample=device_data

# List values for a specific tag
python scripts/discover_influx.py --range=-24h --tag-values=location

# Export sample data for analysis
python scripts/discover_influx.py --range=-24h --measurement-sample=device_data --export-csv=sample.csv
```

### Understanding Your Data

Based on the sample data discovered, here's what we found:

**Measurement:** `device_data`

**Available Tags (for grouping):**
- `location`: Geographic location (e.g., "JBH")
- `station`: Station identifier (e.g., "DEM0")
- `company`: Company identifier (e.g., "DEMO")
- `host`: Device hostname
- `message_type`: Type of message (e.g., "statistics")
- `topic`: MQTT topic path

**Available Fields (for visualization):**
- Statistics fields: `statistics_complete`, `statistics_sent`, `statistics_total_items`, etc.
- Storage fields: `storage_C_used_pct`, `storage_D_free_gb`, etc.
- Device fields: `device_id`, `device_status`, `device_os_version`

## Configuration

### Environment Variables

Set these in your `.env` file or shell environment:

**Required:**
```bash
INFLUXDB_URL=https://influxdb.bantryprop.com
INFLUXDB_TOKEN=your_read_token_here
INFLUXDB_ORG=systems-one
INFLUXDB_BUCKET=telemetry
```

**Optional:**
```bash
INFLUXDB_RANGE_START=-1h    # Time window (e.g., -24h, -7d, -30d)
```

### Application Mapping

The application currently requires these mappings in the code:

```bash
INFLUXDB_MEASUREMENT=device_data
INFLUXDB_CATEGORY_TAG=location
INFLUXDB_VALUE1_FIELD=statistics_complete
INFLUXDB_VALUE2_FIELD=storage_C_used_pct
```

This tells the app:
- Query the `device_data` measurement
- Group charts by `location` tag
- Plot `statistics_complete` as the first metric
- Plot `storage_C_used_pct` as the second metric

## Data Types and Best Practices

### Choosing Good Chart Data

**Numeric Fields** (good for charts):
- Percentages: `storage_C_used_pct` (0-100%)
- Counts: `statistics_complete`, `statistics_total_items`
- Measurements: Temperature, pressure, etc.
- Rates: Items per minute, errors per hour

**Tag Fields** (good for grouping):
- Location: `location`, `station`, `company`
- Device info: `host`, `device_id`
- Categories: `message_type`, `status`

### Time Range Considerations

- **Real-time**: `-5m` to `-1h` for live monitoring
- **Recent**: `-24h` for daily trends
- **Historical**: `-7d` to `-30d` for longer analysis
- **Large datasets**: Use aggregation to reduce data points

## Troubleshooting

### Common Issues

1. **Empty results**
   ```flux
   // Check if any data exists
   from(bucket: "telemetry") |> range(start: -30d) |> limit(n: 1)
   ```

2. **Permission errors**
   - Ensure your token has read access to the bucket
   - Check organization permissions

3. **Field not found**
   - Use discovery script to verify exact field names
   - Check for typos in field/tag names

4. **Too much data**
   ```flux
   // Limit results
   |> limit(n: 1000)
   
   // Or use aggregation
   |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
   ```

5. **Wrong data types**
   - Tags are always strings
   - Fields can be numbers, strings, or booleans
   - Use appropriate filters for each type

### Performance Tips

1. **Use specific time ranges** instead of querying all data
2. **Filter early** in your query to reduce data processing
3. **Use aggregation** for large time ranges
4. **Limit results** when exploring data
5. **Index on tags** for faster filtering

## Security Best Practices

- **Never commit tokens** to version control
- **Use read-only tokens** for applications
- **Rotate tokens** periodically
- **Consider IP restrictions** for production
- **Monitor token usage** in InfluxDB admin panel

## For Developers

### Extending the Application

1. **Use the discovery script** to understand available data
2. **Modify Flux queries** in `DataModel._load_from_influx()` for different data needs
3. **Add caching strategies** for expensive queries
4. **Implement error handling** for network issues
5. **Add query pagination** for large datasets

### Code Examples

**Custom query in DataModel:**
```python
def _load_custom_data(self) -> pd.DataFrame:
    flux = f'''
    from(bucket: "{config.INFLUXDB_BUCKET}")
      |> range(start: -24h)
      |> filter(fn: (r) => r["_measurement"] == "device_data")
      |> filter(fn: (r) => r["location"] == "JBH")
      |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
      |> pivot(rowKey:["_time"], columnKey:["_field"], valueColumn:"_value")
    '''
    # Execute query and return DataFrame
```

**Adding new visualizations:**
1. Create new ViewModel methods for data processing
2. Add new callbacks in the View layer
3. Use appropriate Plotly chart types for your data

### Future Enhancements

- Dynamic field selection in UI
- Real-time data streaming
- Multiple measurement support
- Custom time range picker
- Data export functionality
- Alert thresholds based on metrics
