# Oracle Test Library - Architecture Documentation

## Overview

The Oracle Test Library is designed as a modular, extensible framework for comprehensive Oracle database client testing. It focuses on three key test scenarios:
1. Large write operations
2. Large read operations
3. Multiple concurrent TLS connections

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Application                        │
│  (CLI, Script, or Integration with CI/CD)                   │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  OracleTestSuite                             │
│  - Orchestrates multiple test scenarios                     │
│  - Aggregates results                                        │
│  - Provides high-level reporting                            │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  OracleTestClient                            │
│  - Manages test execution                                    │
│  - Handles concurrent operations                            │
│  - Collects metrics                                          │
│  - Applies load profiles                                     │
└────────┬───────────────┴───────────────┬────────────────────┘
         │                               │
┌────────▼──────────┐          ┌────────▼──────────┐
│  LoadProfile      │          │  TestResults       │
│  - Low Load       │          │  - Metrics         │
│  - High Load      │          │  - Statistics      │
│  - Custom         │          │  - Summaries       │
└───────────────────┘          └────────────────────┘
         │
┌────────▼────────────────────────────────────────────────────┐
│              OracleTestConnection (Pool)                     │
│  - Individual database connections                           │
│  - TLS/SSL support                                           │
│  - Connection lifecycle management                           │
└────────┬────────────────────────────────────────────────────┘
         │
┌────────▼────────────────────────────────────────────────────┐
│                   Oracle Database                            │
│  - test_large_data table (CLOB storage)                     │
│  - test_metrics table (performance tracking)                │
│  - Sequence generators                                       │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. LoadProfile

**Purpose**: Defines the characteristics of a test workload.

**Attributes**:
- `concurrent_connections`: Number of simultaneous database connections
- `operations_per_second`: Target throughput
- `data_size_kb`: Size of data for each operation
- `think_time_ms`: Delay between operations
- `duration_seconds`: Total test duration

**Predefined Profiles**:
- **Low Load**: Conservative profile for baseline testing
  - 2 connections, 10 ops/sec, 10KB data
- **High Load**: Aggressive profile for stress testing
  - 50 connections, 500 ops/sec, 1MB data

**Design Rationale**: 
Separating load configuration allows for:
- Easy comparison between different load levels
- Reusable test configurations
- Clear documentation of test parameters

### 2. TestMetrics

**Purpose**: Captures detailed metrics for individual operations.

**Key Metrics**:
- Duration (ms)
- Throughput (MB/s)
- Success/failure status
- Error messages
- Connection identifier

**Design Rationale**:
Granular per-operation metrics enable:
- Percentile latency analysis (P95, P99)
- Throughput distribution analysis
- Connection-specific performance tracking
- Failure root cause analysis

### 3. TestResults

**Purpose**: Aggregates metrics and provides statistical analysis.

**Capabilities**:
- Success rate calculation
- Latency statistics (avg, median, P95, P99)
- Throughput analysis
- Data volume tracking

**Design Rationale**:
Centralized result processing ensures:
- Consistent metric calculation
- Easy result comparison
- Comprehensive test reporting

### 4. OracleTestConnection

**Purpose**: Manages individual database connections with TLS support.

**Features**:
- Connection pooling compatibility
- TLS/SSL configuration
- Context manager support
- Connection lifecycle tracking

**Design Rationale**:
Isolated connection management allows:
- Independent connection testing
- TLS configuration per connection
- Thread-safe connection handling
- Clean resource management

### 5. OracleTestClient

**Purpose**: Core testing engine that executes test scenarios.

**Key Methods**:
- `test_large_write()`: Single large write operation
- `test_large_read()`: Single large read operation
- `test_concurrent_operations()`: Parallel operation execution
- `run_write_test()`: Complete write test scenario
- `run_read_test()`: Complete read test scenario
- `run_mixed_test()`: Combined read/write scenario

**Design Rationale**:
Flexible test execution supports:
- Various test patterns (read, write, mixed)
- Custom operation definitions
- Concurrent execution models
- Real-time monitoring

### 6. OracleTestSuite

**Purpose**: Orchestrates comprehensive test campaigns.

**Features**:
- Multiple test scenario execution
- Cross-test result comparison
- Batch test management
- Consolidated reporting

**Design Rationale**:
High-level orchestration enables:
- Automated test campaigns
- CI/CD integration
- Regression testing
- Performance benchmarking

## Data Flow

### Write Operation Flow

```
1. Client.run_write_test()
   ├─> Calculate total operations
   ├─> Distribute across connections
   └─> For each connection:
       ├─> Generate test data (random string)
       ├─> Execute INSERT with CLOB
       ├─> Commit transaction
       ├─> Capture metrics (duration, size)
       └─> Return TestMetrics

2. Aggregate all TestMetrics
3. Calculate statistics
4. Return TestResults
```

### Read Operation Flow

```
1. Client.run_read_test()
   ├─> Calculate total operations
   ├─> Distribute across connections
   └─> For each connection:
       ├─> Execute SELECT with random row
       ├─> Fetch CLOB data
       ├─> Measure data size
       ├─> Capture metrics
       └─> Return TestMetrics

2. Aggregate all TestMetrics
3. Calculate statistics
4. Return TestResults
```

### Concurrent Execution Model

```
ThreadPoolExecutor
├─> Worker Thread 1 (Connection 1)
│   └─> Execute N operations sequentially
├─> Worker Thread 2 (Connection 2)
│   └─> Execute N operations sequentially
├─> Worker Thread 3 (Connection 3)
│   └─> Execute N operations sequentially
...
└─> Worker Thread M (Connection M)
    └─> Execute N operations sequentially

All threads run in parallel
Results collected as futures complete
```

## Database Schema

### test_large_data Table

```sql
CREATE TABLE test_large_data (
    id NUMBER PRIMARY KEY,           -- Unique identifier
    data_chunk CLOB,                 -- Large data storage
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE SEQUENCE test_data_seq START WITH 1;
```

**Purpose**: Stores test data for read/write operations.

**Design Choices**:
- CLOB for variable-size large data (up to 4GB per row)
- Timestamp for temporal analysis
- Sequence for guaranteed unique IDs

### test_metrics Table

```sql
CREATE TABLE test_metrics (
    metric_id NUMBER PRIMARY KEY,
    operation_type VARCHAR2(50),
    duration_ms NUMBER,
    success NUMBER(1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose**: Optional persistent storage for test metrics.

**Use Cases**:
- Historical performance tracking
- Trend analysis
- Long-term benchmarking

## Concurrency Model

### Thread Safety

- Each worker thread gets its own `OracleTestConnection`
- No shared mutable state between threads
- Results aggregated after all threads complete
- Thread pool manages connection lifecycle

### Connection Management

```
Main Thread
├─> Creates ThreadPoolExecutor
├─> Submits N worker tasks
└─> Waits for completion

Worker Thread 1
├─> Creates OracleTestConnection
├─> Executes operations
├─> Closes connection
└─> Returns metrics

Worker Thread 2
├─> Creates OracleTestConnection
├─> Executes operations
├─> Closes connection
└─> Returns metrics
...
```

### Load Distribution

Operations are evenly distributed across connections:
```
total_operations = ops_per_second * duration_seconds
ops_per_connection = total_operations / concurrent_connections
```

## Performance Considerations

### Memory Management

1. **Data Generation**: 
   - Generated on-demand per operation
   - Not stored in memory after transmission

2. **Metrics Storage**:
   - Lightweight dataclass objects
   - O(n) memory where n = total operations
   - For 10,000 ops: ~2-5MB RAM

3. **Connection Pooling**:
   - Fixed number of connections
   - No connection leaks (context managers)

### Network Optimization

1. **TLS Handshake**:
   - Reuse connections (amortize handshake cost)
   - Connection pooling recommended for production

2. **Data Transfer**:
   - CLOB streaming for large data
   - Batching not implemented (focus on individual op metrics)

### Database Impact

1. **Write Operations**:
   - Standard INSERT with AUTO-COMMIT
   - No transaction batching
   - CLOB storage uses secure files

2. **Read Operations**:
   - Random row selection (diverse data access)
   - Full CLOB retrieval
   - No caching to simulate real loads

## Extensibility Points

### Custom Operations

Users can define custom operations:

```python
def custom_operation(connection: OracleTestConnection) -> TestMetrics:
    # Your custom logic
    metric = TestMetrics(...)
    return metric

client.test_concurrent_operations(
    custom_operation,
    num_connections=10,
    operations_per_connection=100
)
```

### Custom Metrics

Extend `TestMetrics` for additional measurements:

```python
@dataclass
class CustomMetrics(TestMetrics):
    cpu_usage: float
    memory_usage: float
    network_latency: float
```

### Custom Load Profiles

Create domain-specific profiles:

```python
class FinancialTransactionProfile(LoadProfile):
    @classmethod
    def eod_batch(cls):
        return cls(
            name="End of Day Batch",
            concurrent_connections=20,
            operations_per_second=1000,
            data_size_kb=50,
            think_time_ms=0,
            duration_seconds=3600
        )
```

## Integration Patterns

### CI/CD Integration

```yaml
# Example GitHub Actions workflow
- name: Run Oracle Tests
  run: |
    python oracle_test_cli.py \
      --config ci-config.json \
      --suite \
      --output test-results.json \
      --min-success-rate 99.0
    
- name: Check Results
  run: |
    if [ $? -ne 0 ]; then
      echo "Tests failed to meet SLA"
      exit 1
    fi
```

### Monitoring Integration

```python
# Export to Prometheus
from prometheus_client import Gauge

latency_gauge = Gauge('oracle_test_latency_ms', 'Operation latency')

results = client.run_write_test()
summary = results.get_summary()
latency_gauge.set(summary['p95_duration_ms'])
```

### Custom Reporting

```python
def generate_html_report(results: TestResults) -> str:
    summary = results.get_summary()
    # Generate HTML charts, tables, etc.
    return html_content
```

## Security Considerations

1. **Credential Management**:
   - Never log passwords
   - Support environment variables
   - Wallet encryption for TLS

2. **TLS Configuration**:
   - Certificate validation
   - Cipher suite selection
   - Hostname verification

3. **SQL Injection**:
   - All queries use parameterized statements
   - No string concatenation for SQL

## Testing Strategy

### Unit Tests
- Mock database connections
- Test metric calculations
- Validate load profile creation
- Test result aggregation

### Integration Tests
- Require actual database
- Test full workflows
- Validate TLS connections
- Test concurrent operations

### Performance Tests
- Baseline performance tracking
- Regression detection
- Scalability validation

## Future Enhancements

1. **Connection Pooling**: Native pool management
2. **Streaming Results**: Real-time metric streaming
3. **Distributed Testing**: Multi-host load generation
4. **Advanced Monitoring**: Built-in Prometheus/Grafana
5. **Result Visualization**: Automated chart generation
6. **Schema Migration**: Automatic version upgrades
7. **Workload Recording**: Record and replay patterns
8. **Adaptive Load**: Dynamic load adjustment

## Conclusion

The Oracle Test Library provides a robust, extensible framework for comprehensive database client testing. Its modular architecture supports various test scenarios while maintaining simplicity and ease of use.
