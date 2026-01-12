# LoadProfile Reference Guide

This guide explains the `LoadProfile` class and how to use it correctly.

## Overview

`LoadProfile` defines the load characteristics for testing Oracle database operations. It controls:
- Number of concurrent connections
- Operations per second
- Data size for each operation
- Think time between operations
- Total test duration

## Constructor Parameters

### Required Parameters (All Required)

```python
LoadProfile(
    name: str,                    # Profile name (for identification)
    concurrent_connections: int,  # Number of concurrent connections
    operations_per_second: int,   # Target operations per second
    data_size_kb: int,           # Data size in KB for each operation
    think_time_ms: int,          # Wait time between operations in milliseconds
    duration_seconds: int         # Total test duration in seconds
)
```

### Parameter Details

| Parameter | Type | Description | Example Values |
|-----------|------|-------------|----------------|
| `name` | str | Descriptive name for the profile | `"Low Load"`, `"High Load"`, `"Custom Test"` |
| `concurrent_connections` | int | Number of simultaneous database connections | `1`, `10`, `50`, `100` |
| `operations_per_second` | int | Target rate of operations (reads or writes) | `10`, `100`, `500`, `1000` |
| `data_size_kb` | int | Size of data in KB for each write operation | `1`, `10`, `500`, `1024` |
| `think_time_ms` | int | Milliseconds to wait between operations (0 = no wait) | `0`, `25`, `100`, `1000` |
| `duration_seconds` | int | Total duration of the test in seconds | `60`, `180`, `300`, `600` |

## Usage Examples

### 1. Manual Construction (All Parameters Required)

```python
from oracle_test_lib import LoadProfile

# Correct - all parameters provided
profile = LoadProfile(
    name="Medium Load",
    concurrent_connections=10,
    operations_per_second=100,
    data_size_kb=500,
    think_time_ms=25,
    duration_seconds=180
)
```

**❌ Common Error:**
```python
# WRONG - missing think_time_ms parameter
profile = LoadProfile(
    name="test",
    concurrent_connections=1,
    operations_per_second=10,
    duration_seconds=60,
    data_size_kb=1
)
# TypeError: LoadProfile.__init__() missing 1 required positional argument: 'think_time_ms'
```

**✅ Correct:**
```python
profile = LoadProfile(
    name="test",
    concurrent_connections=1,
    operations_per_second=10,
    data_size_kb=1,
    think_time_ms=0,      # Don't forget this!
    duration_seconds=60
)
```

### 2. Using Predefined Profiles (Recommended)

The easiest way to create load profiles is using the predefined factory methods:

#### Low Load Profile

```python
profile = LoadProfile.low_load()
```

Equivalent to:
```python
LoadProfile(
    name="Low Load",
    concurrent_connections=2,
    operations_per_second=10,
    data_size_kb=10,
    think_time_ms=100,
    duration_seconds=60
)
```

**Best for:**
- Initial testing
- Development environments
- Validating connectivity
- Small databases

#### High Load Profile

```python
profile = LoadProfile.high_load()
```

Equivalent to:
```python
LoadProfile(
    name="High Load",
    concurrent_connections=50,
    operations_per_second=500,
    data_size_kb=1024,
    think_time_ms=0,
    duration_seconds=300
)
```

**Best for:**
- Stress testing
- Performance benchmarking
- Load testing production-like scenarios
- Capacity planning

### 3. Custom Profile Factory Method

Use `LoadProfile.custom()` for convenience:

```python
profile = LoadProfile.custom(
    name="Medium Load",
    concurrent_connections=10,
    operations_per_second=100,
    data_size_kb=500,
    think_time_ms=25,
    duration_seconds=180
)
```

This is identical to the manual constructor but makes it clear you're creating a custom profile.

## Common Use Cases

### Minimal Test Profile

```python
# For quick tests
profile = LoadProfile(
    name="quick_test",
    concurrent_connections=1,
    operations_per_second=10,
    data_size_kb=1,
    think_time_ms=0,
    duration_seconds=10
)
```

### Comprehensive Query Testing

```python
# For bulk data population and queries
profile = LoadProfile(
    name="comprehensive_test",
    concurrent_connections=1,
    operations_per_second=10,
    data_size_kb=1,
    think_time_ms=0,
    duration_seconds=60
)
```

### Sustained Load Test

```python
# For long-running tests
profile = LoadProfile(
    name="sustained_load",
    concurrent_connections=20,
    operations_per_second=200,
    data_size_kb=100,
    think_time_ms=10,
    duration_seconds=3600  # 1 hour
)
```

### Burst Load Test

```python
# For testing peak capacity
profile = LoadProfile(
    name="burst_test",
    concurrent_connections=100,
    operations_per_second=1000,
    data_size_kb=50,
    think_time_ms=0,
    duration_seconds=60
)
```

## Parameter Guidelines

### Concurrent Connections

| Value | Use Case | Notes |
|-------|----------|-------|
| 1-5 | Development, testing | Safe for any environment |
| 10-20 | Moderate load | Good for typical applications |
| 50-100 | High load | Requires proper database tuning |
| 100+ | Stress testing | May exceed connection limits |

### Operations Per Second

| Value | Load Level | Notes |
|-------|------------|-------|
| 1-10 | Very light | Good for initial testing |
| 10-100 | Light-moderate | Typical application load |
| 100-500 | Heavy | Production-like scenarios |
| 500+ | Very heavy | Stress/capacity testing |

### Data Size (KB)

| Value | Use Case | Notes |
|-------|----------|-------|
| 1-10 | Small records | Metadata, configuration |
| 10-100 | Medium records | Typical business data |
| 100-1024 | Large records | Documents, images |
| 1024+ | Very large | Files, large documents |

### Think Time (ms)

| Value | Pattern | Notes |
|-------|---------|-------|
| 0 | No delay | Maximum throughput |
| 10-50 | Rapid user | Quick succession |
| 100-500 | Normal user | Realistic timing |
| 1000+ | Slow user | Long pauses |

### Duration (seconds)

| Value | Use Case | Notes |
|-------|----------|-------|
| 10-60 | Quick test | Validation |
| 60-300 | Standard test | Performance testing |
| 300-1800 | Extended test | Stability testing |
| 1800+ | Long-running | Endurance testing |

## Complete Examples

### Example 1: Development Testing

```python
from oracle_test_lib import OracleTestClient, LoadProfile
import json

with open('db_config.json', 'r') as f:
    db_config = json.load(f)

# Use predefined low load profile
profile = LoadProfile.low_load()

client = OracleTestClient(db_config, profile, use_tls=True)
results = client.run_write_test()
print(results.get_summary())
```

### Example 2: Custom Load Test

```python
# Custom profile for specific requirements
profile = LoadProfile(
    name="api_simulation",
    concurrent_connections=25,
    operations_per_second=250,
    data_size_kb=50,
    think_time_ms=20,
    duration_seconds=300
)

client = OracleTestClient(db_config, profile, use_tls=True)
write_results = client.run_write_test()
read_results = client.run_read_test()
```

### Example 3: Comprehensive Query Testing

```python
# Minimal profile for comprehensive testing
profile = LoadProfile(
    name="query_test",
    concurrent_connections=1,
    operations_per_second=10,
    data_size_kb=1,
    think_time_ms=0,
    duration_seconds=60
)

client = OracleTestClient(db_config, profile, use_tls=True)

# Populate data
conn = OracleTestConnection("test", db_config, use_tls=True)
conn.connect()
stats = client.populate_comprehensive_data(num_rows=50000, connection=conn)

# Run queries
results = client.test_comprehensive_queries(conn, 'all')
```

## Troubleshooting

### Error: Missing Parameter

**Error:**
```
TypeError: LoadProfile.__init__() missing 1 required positional argument: 'think_time_ms'
```

**Solution:**
Make sure all 6 parameters are provided:
```python
profile = LoadProfile(
    name="test",
    concurrent_connections=1,
    operations_per_second=10,
    data_size_kb=1,
    think_time_ms=0,      # Add this!
    duration_seconds=60
)
```

### Error: Too Many Connections

**Error:**
```
ORA-12516: TNS:listener could not find available handler
```

**Solution:**
Reduce `concurrent_connections` or increase database connection limit.

### Error: Out of Memory

**Error:**
```
MemoryError: Unable to allocate array
```

**Solution:**
Reduce `data_size_kb` or `concurrent_connections`.

## Best Practices

1. **Start Small**: Begin with `LoadProfile.low_load()` and increase gradually
2. **Monitor Resources**: Watch CPU, memory, and connection counts
3. **Use Think Time**: Set `think_time_ms > 0` for realistic user simulation
4. **Match Production**: Base profiles on actual production load patterns
5. **Test Incrementally**: Increase load in steps to find limits
6. **Consider Network**: Account for network latency in `think_time_ms`

## Related Documentation

- [README.md](../README.md) - Main documentation
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [COMPREHENSIVE_TESTING.md](COMPREHENSIVE_TESTING.md) - Query testing guide
- [examples/examples.py](../examples/examples.py) - Usage examples

## Summary

- ✅ **Always use all 6 parameters** when constructing LoadProfile manually
- ✅ **Use factory methods** (`low_load()`, `high_load()`, `custom()`) for convenience
- ✅ **Start with predefined profiles** and customize as needed
- ✅ **Set `think_time_ms=0`** for maximum throughput testing
- ✅ **Set `think_time_ms>0`** for realistic user simulation
