# Oracle Test Library - Quick Start Guide

## Installation

```bash
# Install from source
pip install -e .

# Or install with all features
pip install -e ".[all]"
```

## Step 0: Test Your Connection First! ⚠️

```python
from oracle_test_lib import OracleTestClient

db_config = {
    'host': 'localhost',
    'port': 1521,
    'user': 'testuser',
    'password': 'testpass',
    'service_name': 'ORCLPDB1',
}

# Test connection
success, message = OracleTestClient.test_connection(db_config, use_tls=False)
print(message)

if not success:
    print("Fix connection issues before proceeding")
    exit(1)
```

Or use the CLI:

```bash
python oracle_test_cli.py \
  --host localhost \
  --user testuser \
  --password testpass \
  --test-connection
```

## Basic Usage

### 1. Simple Write Test

```python
from oracle_test_lib import OracleTestClient, LoadProfile

# Configure your database
db_config = {
    'host': 'localhost',
    'port': 1521,
    'user': 'testuser',
    'password': 'testpass',
    'service_name': 'ORCLPDB1',
}

# Run a simple write test
client = OracleTestClient(
    db_config=db_config,
    load_profile=LoadProfile.low_load(),
    use_tls=False
)

results = client.run_write_test()
print(results.get_summary())
```

### 2. Using the CLI

```bash
# Simple test
python oracle_test_cli.py \
  --host localhost \
  --user testuser \
  --password testpass \
  --test-type write

# Custom load test
python oracle_test_cli.py \
  --host localhost \
  --user testuser \
  --password testpass \
  --test-type mixed \
  --load-profile custom \
  --connections 20 \
  --ops-per-sec 100 \
  --data-size-kb 500 \
  --duration 300

# Full test suite
python oracle_test_cli.py \
  --host localhost \
  --user testuser \
  --password testpass \
  --suite \
  --include-high-load \
  --output results.json
```

### 3. Using a Config File

Create `config.json`:
```json
{
  "host": "localhost",
  "port": 1521,
  "user": "testuser",
  "password": "testpass",
  "service_name": "ORCLPDB1",
  "test_type": "mixed",
  "connections": 10,
  "ops_per_sec": 50
}
```

Run test:
```bash
python oracle_test_cli.py --config config.json --output results.json
```

## Common Test Scenarios

### Testing Large Writes

```python
from oracle_test_lib import LoadProfile, OracleTestClient

# Profile for large data writes
large_write_profile = LoadProfile.custom(
    name="Large Writes",
    concurrent_connections=5,
    operations_per_second=20,
    data_size_kb=5120,  # 5 MB per write
    duration_seconds=180
)

client = OracleTestClient(db_config, large_write_profile)
results = client.run_write_test()

summary = results.get_summary()
print(f"Throughput: {summary['avg_throughput_mbps']:.2f} MB/s")
```

### Testing Concurrent TLS Connections

```python
# TLS configuration
db_config_tls = {
    'host': 'secure-db.example.com',
    'port': 2484,
    'user': 'testuser',
    'password': 'testpass',
    'service_name': 'PRODDB',
    'wallet_location': '/opt/oracle/wallet',
    'wallet_password': 'WalletPass123'
}

# High concurrency profile
tls_profile = LoadProfile.custom(
    name="TLS Stress Test",
    concurrent_connections=100,
    operations_per_second=200,
    data_size_kb=100,
    duration_seconds=300
)

client = OracleTestClient(db_config_tls, tls_profile, use_tls=True)
results = client.run_mixed_test()

summary = results.get_summary()
print(f"Success Rate: {summary['success_rate']:.2f}%")
print(f"P95 Latency: {summary['p95_duration_ms']:.2f} ms")
```

### Mixed Read/Write Test

```python
# Balanced load
profile = LoadProfile.custom(
    name="Balanced Load",
    concurrent_connections=20,
    operations_per_second=100,
    data_size_kb=256,
    duration_seconds=300
)

client = OracleTestClient(db_config, profile)

# 70% reads, 30% writes
results = client.run_mixed_test(read_write_ratio=0.7)
```

## Understanding Results

### Key Metrics

```python
summary = results.get_summary()

# Operation counts
print(f"Total ops: {summary['total_operations']}")
print(f"Success rate: {summary['success_rate']:.2f}%")

# Latency metrics
print(f"Average latency: {summary['avg_duration_ms']:.2f} ms")
print(f"P95 latency: {summary['p95_duration_ms']:.2f} ms")
print(f"P99 latency: {summary['p99_duration_ms']:.2f} ms")

# Throughput metrics
print(f"Throughput: {summary['avg_throughput_mbps']:.2f} MB/s")
print(f"Data transferred: {summary['total_data_transferred_mb']:.2f} MB")
```

### Exporting Results

```python
import json

# Export to JSON
with open('test_results.json', 'w') as f:
    json.dump(results.get_summary(), f, indent=2)

# Export detailed metrics
detailed = [{
    'operation': m.operation_type,
    'duration_ms': m.duration_ms,
    'success': m.success,
    'throughput_mbps': m.throughput_mbps
} for m in results.metrics]

with open('detailed_metrics.json', 'w') as f:
    json.dump(detailed, f, indent=2)
```

## Troubleshooting

### Connection Issues

```python
# Test basic connectivity first
from oracle_test_lib import OracleTestConnection

conn = OracleTestConnection("test", db_config, use_tls=False)
if conn.connect():
    print("✓ Connection successful!")
    conn.disconnect()
else:
    print("✗ Connection failed - check credentials")
```

### Performance Issues

1. **Start with low load**:
   ```python
   profile = LoadProfile.low_load()
   ```

2. **Gradually increase**:
   ```python
   for conns in [5, 10, 20, 50]:
       profile = LoadProfile.custom(
           name=f"Test_{conns}",
           concurrent_connections=conns,
           operations_per_second=conns * 5
       )
       # Run test and monitor
   ```

3. **Monitor database**:
   ```sql
   -- Check active sessions
   SELECT COUNT(*) FROM v$session WHERE status = 'ACTIVE';
   
   -- Check waits
   SELECT event, COUNT(*) FROM v$session_wait GROUP BY event;
   ```

## Next Steps

- Read the full [README.md](README.md) for comprehensive documentation
- Check [examples.py](examples.py) for more usage patterns
- Review [test_oracle_lib.py](test_oracle_lib.py) for testing examples
- Customize load profiles for your specific use case

## Getting Help

- Check the logs: Enable verbose mode with `--verbose` flag
- Test incrementally: Start small and increase load gradually
- Monitor resources: Watch database CPU, memory, and I/O
- Review metrics: Use detailed metrics to identify bottlenecks

## Common Commands Cheat Sheet

```bash
# Quick test
python oracle_test_cli.py --host HOST --user USER --password PASS

# Full suite
python oracle_test_cli.py --config config.json --suite --output results.json

# Custom test
python oracle_test_cli.py \
  --host HOST --user USER --password PASS \
  --connections 50 --ops-per-sec 200 --duration 600

# TLS test
python oracle_test_cli.py \
  --host HOST --user USER --password PASS \
  --use-tls --wallet-location /path/to/wallet

# View results
cat results.json | python -m json.tool
```

