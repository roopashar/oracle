# Test Results Output Format

## Updated Examples with Detailed Results

All example functions now print comprehensive test results using the `print_test_results()` helper function.

## Output Format

### Standard Test Results Display

Each test now displays results in this format:

```
======================================================================
Test Name - Results Summary
======================================================================
Load Profile: Profile Name

Operations:
  Total Operations:     10,000
  Successful:           9,985
  Failed:               15
  Success Rate:         99.85%

Operation Breakdown:
  Read Operations:      7,000
  Write Operations:     3,000

Data Transfer:
  Total Data:           976.56 MB
  Avg Throughput:       8.14 MB/s
  Read Data:            683.59 MB
  Read Throughput:      5.70 MB/s
  Write Data:           292.97 MB
  Write Throughput:     2.44 MB/s

Performance Metrics (Overall):
  Average Duration:     125.45 ms
  Min Duration:         45.23 ms
  Max Duration:         567.89 ms
  P50 (Median):         118.34 ms
  P95 Latency:          234.56 ms
  P99 Latency:          345.67 ms

Read Performance:
  Average Duration:     95.23 ms
  Min Duration:         45.23 ms
  Max Duration:         456.78 ms
  P50 (Median):         88.90 ms
  P95 Latency:          178.45 ms
  P99 Latency:          267.89 ms

Write Performance:
  Average Duration:     185.67 ms
  Min Duration:         78.12 ms
  Max Duration:         567.89 ms
  P50 (Median):         178.23 ms
  P95 Latency:          345.56 ms
  P99 Latency:          478.34 ms

Test Duration:          120.00 seconds
======================================================================
```

## Examples Updated

### Example 1: Simple Low Load Test

**Before:**
```
Completed 600 write operations
Success rate: 99.50%
Average duration: 125.45 ms
```

**After:**
```
Running write test...

======================================================================
Write Test - Results Summary
======================================================================
Load Profile: Low Load

Operations:
  Total Operations:     600
  Successful:           597
  Failed:               3
  Success Rate:         99.50%

Data Transfer:
  Total Data:           5.86 MB
  Avg Throughput:       0.10 MB/s

Performance Metrics:
  Average Duration:     125.45 ms
  Min Duration:         89.12 ms
  Max Duration:         245.67 ms
  P50 (Median):         120.34 ms
  P95 Latency:          189.23 ms
  P99 Latency:          220.45 ms

Test Duration:          60.00 seconds
======================================================================

Running read test...

======================================================================
Read Test - Results Summary
======================================================================
Load Profile: Low Load

Operations:
  Total Operations:     600
  Successful:           600
  Failed:               0
  Success Rate:         100.00%

Data Transfer:
  Total Data:           5.86 MB
  Avg Throughput:       0.10 MB/s

Performance Metrics:
  Average Duration:     85.34 ms
  Min Duration:         65.12 ms
  Max Duration:         178.23 ms
  P50 (Median):         82.45 ms
  P95 Latency:          125.67 ms
  P99 Latency:          156.89 ms

Test Duration:          60.00 seconds
======================================================================
```

### Example 2: Custom Load Profile

**After:**
```
Running mixed test (70% reads, 30% writes)...

======================================================================
Custom Load - Mixed Test - Results Summary
======================================================================
Load Profile: Medium Load

Operations:
  Total Operations:     10,000
  Successful:           9,950
  Failed:               50
  Success Rate:         99.50%

Operation Breakdown:
  Read Operations:      6,965
  Write Operations:     2,985

Data Transfer:
  Total Data:           488.28 MB
  Avg Throughput:       4.07 MB/s
  Read Data:            341.80 MB
  Read Throughput:      2.85 MB/s
  Write Data:           146.48 MB
  Write Throughput:     1.22 MB/s

Performance Metrics (Overall):
  Average Duration:     95.67 ms
  Min Duration:         45.23 ms
  Max Duration:         456.78 ms
  P50 (Median):         88.90 ms
  P95 Latency:          178.45 ms
  P99 Latency:          267.89 ms

Read Performance:
  Average Duration:     82.34 ms
  Min Duration:         45.23 ms
  Max Duration:         398.67 ms
  P50 (Median):         78.12 ms
  P95 Latency:          156.78 ms
  P99 Latency:          234.56 ms

Write Performance:
  Average Duration:     135.89 ms
  Min Duration:         67.89 ms
  Max Duration:         456.78 ms
  P50 (Median):         128.45 ms
  P95 Latency:          267.34 ms
  P99 Latency:          356.89 ms

Test Duration:          120.00 seconds
======================================================================
```

### Example 3: High Load Stress Test

**After:**
```
Load Profile: Medium Load (Cloud Optimized)
  Connections: 10
  Target ops/sec: 50
  Data size: 100 KB
  Duration: 120 seconds
  Expected records: ~6,000

Step 1: Populating data with write test...

======================================================================
High Load - Write Test - Results Summary
======================================================================
Load Profile: Medium Load (Cloud Optimized)

Operations:
  Total Operations:     6,000
  Successful:           5,991
  Failed:               9
  Success Rate:         99.85%

Data Transfer:
  Total Data:           585.94 MB
  Avg Throughput:       4.88 MB/s

Performance Metrics:
  Average Duration:     95.23 ms
  Min Duration:         67.45 ms
  Max Duration:         345.67 ms
  P50 (Median):         92.34 ms
  P95 Latency:          156.78 ms
  P99 Latency:          234.56 ms

Test Duration:          120.00 seconds
======================================================================

Step 2: Running high load read test...

======================================================================
High Load - Read Test - Results Summary
======================================================================
Load Profile: Medium Load (Cloud Optimized)

Operations:
  Total Operations:     6,000
  Successful:           5,995
  Failed:               5
  Success Rate:         99.92%

Data Transfer:
  Total Data:           586.12 MB
  Avg Throughput:       4.88 MB/s

Performance Metrics:
  Average Duration:     67.89 ms
  Min Duration:         45.23 ms
  Max Duration:         234.56 ms
  P50 (Median):         65.67 ms
  P95 Latency:          125.45 ms
  P99 Latency:          187.23 ms

Test Duration:          120.00 seconds
======================================================================
```

## Benefits of New Format

### 1. Comprehensive Information

All metrics displayed in one place:
- ✅ Operations count (total, successful, failed)
- ✅ **Separate read/write operation counts**
- ✅ Success rate
- ✅ Data transfer statistics
- ✅ **Separate read/write data and throughput**
- ✅ Throughput
- ✅ Performance metrics (avg, min, max, percentiles)
- ✅ **Separate read/write performance metrics**
- ✅ Test duration

### 2. Easy to Read

- Clear section headers
- Aligned columns
- Formatted numbers (commas, decimal places)
- Visual separators

### 3. Professional Output

- Consistent formatting across all tests
- Looks professional for reports
- Easy to copy/paste into documentation

### 4. Comparable Results

- Same format for all tests
- Easy to compare different test runs
- Clear metric labels

## Helper Function

### `print_test_results(results, test_name)`

**Parameters:**
- `results` - TestResults object from any test
- `test_name` - Name to display in the header

**Usage:**
```python
# Run any test
results = client.run_write_test()

# Print detailed results
print_test_results(results, "My Write Test")
```

**Location:** `examples/examples.py` - Lines 21-57

## Metrics Explained

### Operations Metrics

| Metric | Description | Format |
|--------|-------------|--------|
| Total Operations | Total number of operations attempted | Number with commas |
| Successful | Number of successful operations | Number with commas |
| Failed | Number of failed operations | Number with commas |
| Success Rate | Percentage of successful operations | XX.XX% |
| **Read Operations** | **Number of read operations** | **Number with commas** |
| **Write Operations** | **Number of write operations** | **Number with commas** |

### Data Transfer Metrics

| Metric | Description | Format |
|--------|-------------|--------|
| Total Data | Total amount of data transferred | XX.XX MB |
| Avg Throughput | Average data transfer rate | XX.XX MB/s |
| **Read Data** | **Total data read from database** | **XX.XX MB** |
| **Read Throughput** | **Average read data transfer rate** | **XX.XX MB/s** |
| **Write Data** | **Total data written to database** | **XX.XX MB** |
| **Write Throughput** | **Average write data transfer rate** | **XX.XX MB/s** |

### Performance Metrics

**Overall Performance (all operations combined):**

| Metric | Description | Format |
|--------|-------------|--------|
| Average Duration | Mean operation duration | XX.XX ms |
| Min Duration | Fastest operation | XX.XX ms |
| Max Duration | Slowest operation | XX.XX ms |
| P50 (Median) | 50th percentile (half faster, half slower) | XX.XX ms |
| P95 Latency | 95th percentile (95% faster) | XX.XX ms |
| P99 Latency | 99th percentile (99% faster) | XX.XX ms |

**Read Performance (read operations only):**

| Metric | Description | Format |
|--------|-------------|--------|
| Read Avg Duration | Mean read operation duration | XX.XX ms |
| Read Min Duration | Fastest read operation | XX.XX ms |
| Read Max Duration | Slowest read operation | XX.XX ms |
| Read P50 (Median) | 50th percentile for reads | XX.XX ms |
| Read P95 Latency | 95th percentile for reads | XX.XX ms |
| Read P99 Latency | 99th percentile for reads | XX.XX ms |

**Write Performance (write operations only):**

| Metric | Description | Format |
|--------|-------------|--------|
| Write Avg Duration | Mean write operation duration | XX.XX ms |
| Write Min Duration | Fastest write operation | XX.XX ms |
| Write Max Duration | Slowest write operation | XX.XX ms |
| Write P50 (Median) | 50th percentile for writes | XX.XX ms |
| Write P95 Latency | 95th percentile for writes | XX.XX ms |
| Write P99 Latency | 99th percentile for writes | XX.XX ms |

### Test Duration

| Metric | Description | Format |
|--------|-------------|--------|
| Test Duration | Total time the test ran | XX.XX seconds |

## Percentile Explanations

### P50 (Median)
- 50% of operations were faster than this
- 50% of operations were slower than this
- Good indicator of "typical" performance

### P95 Latency
- 95% of operations were faster than this
- Only 5% of operations were slower
- Important for understanding "most" user experience

### P99 Latency
- 99% of operations were faster than this
- Only 1% of operations were slower
- Important for understanding "worst case" scenarios

## Running Examples

```bash
# Run from project root
python3 examples/examples.py

# Or from examples directory
cd examples
python3 examples.py
```

## Example Output - Complete Test Run

```
=== Example 1: Simple Low Load Test ===

Running write test...

======================================================================
Write Test - Results Summary
======================================================================
Load Profile: Low Load

Operations:
  Total Operations:     600
  Successful:           597
  Failed:               3
  Success Rate:         99.50%

Data Transfer:
  Total Data:           5.86 MB
  Avg Throughput:       0.10 MB/s

Performance Metrics:
  Average Duration:     125.45 ms
  Min Duration:         89.12 ms
  Max Duration:         245.67 ms
  P50 (Median):         120.34 ms
  P95 Latency:          189.23 ms
  P99 Latency:          220.45 ms

Test Duration:          60.00 seconds
======================================================================

Running read test...

======================================================================
Read Test - Results Summary
======================================================================
Load Profile: Low Load

Operations:
  Total Operations:     600
  Successful:           600
  Failed:               0
  Success Rate:         100.00%

Data Transfer:
  Total Data:           5.86 MB
  Avg Throughput:       0.10 MB/s

Performance Metrics:
  Average Duration:     85.34 ms
  Min Duration:         65.12 ms
  Max Duration:         178.23 ms
  P50 (Median):         82.45 ms
  P95 Latency:          125.67 ms
  P99 Latency:          156.89 ms

Test Duration:          60.00 seconds
======================================================================
```

## Customizing Output

You can customize the `print_test_results()` function to:
- Add more metrics
- Change formatting
- Export to file
- Add color coding
- Generate graphs

## Summary

✅ **All examples updated** with detailed results printing
✅ **Consistent format** across all tests
✅ **Comprehensive metrics** (operations, data transfer, performance)
✅ **Separate read/write metrics** for detailed performance analysis
✅ **Easy to read** with clear sections and formatting
✅ **Professional output** suitable for reports
✅ **Reusable function** `print_test_results()` for custom tests

The new output format provides all the information you need to understand test performance at a glance, with separate metrics for read and write operations to help identify performance bottlenecks!
