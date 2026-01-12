# Comprehensive Database Testing Guide

This guide explains the enhanced schema and testing capabilities for querying large datasets with multiple column types.

## Overview

The project now includes a comprehensive test table (`test_comprehensive`) with 20+ columns of various data types, along with methods to populate it with large amounts of data and run diverse query patterns.

## New Database Schema

### Table: `test_comprehensive`

This table includes multiple Oracle data types for comprehensive testing:

| Column | Type | Description |
|--------|------|-------------|
| `id` | NUMBER | Primary key (auto-increment via sequence) |
| `varchar_short` | VARCHAR2(50) | Short variable-length string |
| `varchar_long` | VARCHAR2(4000) | Long variable-length string |
| `number_int` | NUMBER(10) | Integer numbers |
| `number_decimal` | NUMBER(10,2) | Decimal numbers with 2 decimal places |
| `number_float` | BINARY_DOUBLE | Floating-point numbers |
| `date_field` | DATE | Date values |
| `timestamp_field` | TIMESTAMP | Timestamp values |
| `timestamp_tz` | TIMESTAMP WITH TIME ZONE | Timestamp with timezone |
| `clob_field` | CLOB | Character Large Object |
| `blob_field` | BLOB | Binary Large Object |
| `char_field` | CHAR(10) | Fixed-length character |
| `status` | VARCHAR2(20) | Status field (indexed) |
| `category` | VARCHAR2(50) | Category field (indexed) |
| `price` | NUMBER(12,2) | Price field (indexed) |
| `quantity` | NUMBER(8) | Quantity field |
| `is_active` | NUMBER(1) | Boolean flag (0 or 1) |
| `email` | VARCHAR2(255) | Email address |
| `description` | VARCHAR2(1000) | Description text |
| `created_at` | TIMESTAMP | Auto-populated creation timestamp |
| `updated_at` | TIMESTAMP | Auto-populated update timestamp |

### Indexes

The following indexes are created for performance testing:

- `idx_comprehensive_status` on `status`
- `idx_comprehensive_category` on `category`
- `idx_comprehensive_date` on `date_field`
- `idx_comprehensive_price` on `price`

## New Methods

### 1. `populate_comprehensive_data()`

Populates the `test_comprehensive` table with a large number of rows.

**Signature:**
```python
def populate_comprehensive_data(
    self,
    num_rows: int,
    batch_size: int = 1000,
    connection: Optional[OracleTestConnection] = None
) -> Dict[str, Any]
```

**Parameters:**
- `num_rows`: Total number of rows to insert
- `batch_size`: Number of rows per batch insert (default: 1000)
- `connection`: Optional existing connection (creates new if None)

**Returns:**
```python
{
    'rows_inserted': int,
    'elapsed_time_sec': float,
    'rows_per_second': float,
    'batches': int,
    'batch_size': int
}
```

**Example:**
```python
client = OracleTestClient(db_config, load_profile, use_tls=True)
conn = OracleTestConnection("test", db_config, use_tls=True)
conn.connect()

# Populate with 100,000 rows
stats = client.populate_comprehensive_data(
    num_rows=100000,
    batch_size=1000,
    connection=conn
)

print(f"Inserted {stats['rows_inserted']} rows at {stats['rows_per_second']:.0f} rows/sec")
```

### 2. `test_comprehensive_queries()`

Tests various query patterns on the comprehensive table.

**Signature:**
```python
def test_comprehensive_queries(
    self,
    connection: OracleTestConnection,
    query_type: str = 'all'
) -> Dict[str, Any]
```

**Parameters:**
- `connection`: Database connection
- `query_type`: Type of queries to run
  - `'all'`: All query types (default)
  - `'select_all'`: Simple SELECT queries
  - `'where_indexed'`: WHERE clauses on indexed columns
  - `'where_non_indexed'`: WHERE clauses on non-indexed columns
  - `'aggregate'`: Aggregate functions (COUNT, AVG, SUM, MIN, MAX)
  - `'group_by'`: GROUP BY queries
  - `'order_by'`: ORDER BY queries
  - `'complex'`: Complex multi-condition queries

**Returns:**
```python
{
    'query_name': {
        'success': bool,
        'rows_returned': int,
        'elapsed_time_ms': float,
        'query': str
    },
    ...
}
```

**Example:**
```python
# Test all query types
results = client.test_comprehensive_queries(conn, 'all')

# Test only aggregate queries
agg_results = client.test_comprehensive_queries(conn, 'aggregate')

# Print results
for query_name, result in results.items():
    if result['success']:
        print(f"{query_name}: {result['rows_returned']} rows in {result['elapsed_time_ms']:.2f}ms")
```

### 3. `test_query_performance()`

Tests performance of a specific query over multiple iterations.

**Signature:**
```python
def test_query_performance(
    self,
    connection: OracleTestConnection,
    query: str,
    params: Optional[Dict[str, Any]] = None,
    iterations: int = 10
) -> Dict[str, Any]
```

**Parameters:**
- `connection`: Database connection
- `query`: SQL query to test
- `params`: Optional query parameters (for bind variables)
- `iterations`: Number of times to execute the query (default: 10)

**Returns:**
```python
{
    'query': str,
    'iterations': int,
    'successful_iterations': int,
    'failed_iterations': int,
    'avg_time_ms': float,
    'min_time_ms': float,
    'max_time_ms': float,
    'total_time_ms': float,
    'avg_rows_returned': float,
    'execution_times_ms': List[float]
}
```

**Example:**
```python
# Test a specific query 20 times
stats = client.test_query_performance(
    connection=conn,
    query="SELECT * FROM test_comprehensive WHERE status = 'active' AND price > 100",
    iterations=20
)

print(f"Average: {stats['avg_time_ms']:.2f}ms")
print(f"Min: {stats['min_time_ms']:.2f}ms")
print(f"Max: {stats['max_time_ms']:.2f}ms")

# Test with bind variables
stats = client.test_query_performance(
    connection=conn,
    query="SELECT * FROM test_comprehensive WHERE status = :status AND price > :min_price",
    params={'status': 'active', 'min_price': 100},
    iterations=20
)
```

## New Prepared Statements

The following prepared statements are now available via `client._prepared_statements`:

### `select_by_status`
```sql
SELECT * FROM test_comprehensive
WHERE status = :status
AND ROWNUM <= :limit
```

### `select_by_category`
```sql
SELECT * FROM test_comprehensive
WHERE category = :category
AND ROWNUM <= :limit
```

### `select_by_price_range`
```sql
SELECT * FROM test_comprehensive
WHERE price BETWEEN :min_price AND :max_price
AND ROWNUM <= :limit
```

### `select_by_date_range`
```sql
SELECT * FROM test_comprehensive
WHERE date_field BETWEEN :start_date AND :end_date
AND ROWNUM <= :limit
```

### `aggregate_by_category`
```sql
SELECT category, COUNT(*) as count, AVG(price) as avg_price, SUM(quantity) as total_qty
FROM test_comprehensive
WHERE category = :category
GROUP BY category
```

**Usage Example:**
```python
# Using prepared statements
conn.cursor.execute(
    client._prepared_statements['select_by_status'],
    {'status': 'active', 'limit': 100}
)
rows = conn.cursor.fetchall()

conn.cursor.execute(
    client._prepared_statements['select_by_price_range'],
    {'min_price': 50.00, 'max_price': 500.00, 'limit': 1000}
)
rows = conn.cursor.fetchall()
```

## Sample Data Distribution

When populated, the table contains randomly generated data with:

### Status Values
- `active`
- `inactive`
- `pending`
- `completed`
- `cancelled`

### Category Values
- `electronics`
- `clothing`
- `food`
- `books`
- `toys`
- `sports`
- `home`
- `automotive`

### Other Fields
- **Price**: Random values between $1.00 and $9,999.99
- **Quantity**: Random integers between 0 and 10,000
- **Dates**: Random dates within the last year
- **Email**: Generated as `user{id}@{domain}`
- **CLOB fields**: Random text 1000-5000 characters
- **BLOB fields**: Random binary data 100-1000 bytes

## Configuration

Before running any tests, you need to configure your database connection. The project uses a `db_config.json` file:

```json
{
  "host": "localhost",
  "port": 1521,
  "user": "system",
  "password": "TestPassword123",
  "service_name": "FREEPDB1",
  "wallet_location": "/path/to/wallet",
  "wallet_password": "WalletPass123"
}
```

Create this file in the project root directory with your actual database credentials.

## Usage Example

See [example_comprehensive_test.py](example_comprehensive_test.py) for a complete working example.

### Quick Start

```python
from oracle_test_lib import OracleTestClient, OracleTestConnection, LoadProfile
import json

# Load config from JSON file
with open('db_config.json', 'r') as f:
    db_config = json.load(f)

# Create client (automatically creates tables)
load_profile = LoadProfile(
    name="test",
    concurrent_connections=1,
    operations_per_second=10,
    data_size_kb=1,
    think_time_ms=0,
    duration_seconds=60
)
client = OracleTestClient(db_config, load_profile, use_tls=True, setup_tables=True)

# Create connection
conn = OracleTestConnection("test", db_config, use_tls=True)
conn.connect()

# Populate table with 50,000 rows
print("Populating data...")
stats = client.populate_comprehensive_data(num_rows=50000, batch_size=1000, connection=conn)
print(f"Populated {stats['rows_inserted']} rows in {stats['elapsed_time_sec']:.2f}s")

# Run query tests
print("\nRunning query tests...")
results = client.test_comprehensive_queries(conn, 'all')
for query_name, result in results.items():
    if result['success']:
        print(f"{query_name}: {result['rows_returned']} rows in {result['elapsed_time_ms']:.2f}ms")

# Test specific query performance
print("\nTesting query performance...")
perf_stats = client.test_query_performance(
    connection=conn,
    query="SELECT * FROM test_comprehensive WHERE status = 'active' AND ROWNUM <= 100",
    iterations=10
)
print(f"Average: {perf_stats['avg_time_ms']:.2f}ms")

# Cleanup
conn.disconnect()
```

## Performance Tips

1. **Batch Size**: For bulk inserts, adjust `batch_size` based on your network latency and row complexity. Typical values: 500-2000.

2. **Indexes**: The table includes indexes on frequently queried columns. Use EXPLAIN PLAN to verify index usage:
   ```sql
   EXPLAIN PLAN FOR SELECT * FROM test_comprehensive WHERE status = 'active';
   SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY);
   ```

3. **Large Datasets**: Start with 10K-100K rows for testing. For stress testing, gradually increase to 1M+ rows.

4. **Query Limits**: Most test queries limit results with `ROWNUM` or `FETCH FIRST` to prevent overwhelming memory. Adjust as needed.

5. **Connection Pooling**: For concurrent testing, use multiple connections from the load profile.

## Testing Scenarios

### Scenario 1: Index Performance Comparison
```python
# Test indexed column query
results_indexed = client.test_query_performance(
    conn,
    "SELECT * FROM test_comprehensive WHERE status = 'active' AND ROWNUM <= 100",
    iterations=50
)

# Test non-indexed column query
results_non_indexed = client.test_query_performance(
    conn,
    "SELECT * FROM test_comprehensive WHERE quantity > 5000 AND ROWNUM <= 100",
    iterations=50
)

print(f"Indexed avg: {results_indexed['avg_time_ms']:.2f}ms")
print(f"Non-indexed avg: {results_non_indexed['avg_time_ms']:.2f}ms")
```

### Scenario 2: Aggregate Query Scaling
```python
# Test aggregation on different dataset sizes
for size in [1000, 10000, 100000]:
    # Populate table
    client.populate_comprehensive_data(num_rows=size, connection=conn)

    # Test aggregate query
    stats = client.test_query_performance(
        conn,
        "SELECT category, COUNT(*), AVG(price) FROM test_comprehensive GROUP BY category",
        iterations=10
    )
    print(f"{size} rows: {stats['avg_time_ms']:.2f}ms avg")
```

### Scenario 3: Complex Multi-Condition Queries
```python
# Test various WHERE clause combinations
results = client.test_comprehensive_queries(conn, 'complex')
for query_name, result in results.items():
    print(f"{query_name}: {result['elapsed_time_ms']:.2f}ms")
```

## Troubleshooting

### Issue: Slow bulk inserts

**Solution**: Increase batch_size or disable indexes during bulk insert:
```python
# Drop indexes before bulk insert
conn.cursor.execute("DROP INDEX idx_comprehensive_status")
# ... other indexes

# Populate data
client.populate_comprehensive_data(num_rows=1000000, batch_size=2000, connection=conn)

# Recreate indexes
conn.cursor.execute("CREATE INDEX idx_comprehensive_status ON test_comprehensive(status)")
# ... other indexes
```

### Issue: Out of memory errors

**Solution**: Reduce `batch_size` or limit query results more aggressively with ROWNUM.

### Issue: Slow aggregate queries

**Solution**: Ensure statistics are up to date:
```sql
EXEC DBMS_STATS.GATHER_TABLE_STATS('YOUR_USERNAME', 'TEST_COMPREHENSIVE');
```

## Additional Resources

- [oracle_test_lib.py](oracle_test_lib.py) - Main library implementation
- [example_comprehensive_test.py](example_comprehensive_test.py) - Complete example script
- [examples.py](examples.py) - Original examples
- [README.md](README.md) - Project overview
