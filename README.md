# Oracle Client Test Library

A comprehensive Python library for testing Oracle database clients with support for large reads/writes, concurrent TLS connections, configurable load patterns, and comprehensive query testing.

## Features

- **Large Write Operations**: Test writing large data chunks (configurable KB to MB)
- **Large Read Operations**: Test reading large data sets with performance metrics
- **Concurrent TLS Connections**: Test multiple simultaneous secure connections
- **Configurable Load Profiles**: Switch between low, high, or custom load patterns
- **Comprehensive Query Testing**: Test multiple column types with bulk data population
- **Prepared Statements**: Optimized SQL execution with prepared statement support
- **Batch Operations**: Efficient bulk inserts using executemany
- **Performance Metrics**: Detailed statistics including latency, throughput, and success rates
- **Thread-Safe**: Built-in support for concurrent testing scenarios

## Project Structure

```
oracle/
├── oracle_test_lib.py          # Main library (core functionality)
├── oracle_test_cli.py           # Command-line interface
├── db_config.json               # Database configuration (git-ignored)
├── setup.py                     # Package installation
├── requirements.txt             # Python dependencies
├── README.md                    # This file
│
├── docs/                        # Documentation
│   ├── QUICKSTART.md           # Quick start guide
│   ├── INSTALLATION.md         # Installation instructions
│   ├── DB_CONFIG_SETUP.md      # Database configuration guide
│   ├── COMPREHENSIVE_TESTING.md # Comprehensive testing guide
│   ├── DOCKER_TLS_SETUP.md     # Docker TLS setup guide
│   ├── ARCHITECTURE.md         # Architecture documentation
│   ├── PROJECT_SUMMARY.md      # Project summary
│   └── LOAD_PROFILE_COMPARISON.md   # Compare load profiles
│
├── examples/                    # Example scripts
│   ├── examples.py             # Basic usage examples
│   └── example_comprehensive_test.py  # Comprehensive query testing
│
├── scripts/                     # Utility scripts
│   ├── install.sh              # Installation script
│   ├── discover_oracle_services.py  # Service discovery tool
│   ├── setup_docker_tls.sh     # Docker TLS setup (full)
│   └── setup_docker_tls_simple.sh   # Docker TLS setup (simple)
│
├── tests/                       # Test suite
│   └── test_oracle_lib.py      # Unit tests
│
└── config/                      # Configuration templates
    ├── config.example.json      # CLI config example
    └── db_config.json.example   # Database config template
```

## Quick Start

### 1. Installation

```bash
# Clone or download the project
cd oracle

# Install dependencies
./scripts/install.sh

# Or install manually
pip install -e .
```

See [docs/INSTALLATION.md](docs/INSTALLATION.md) for detailed instructions.

### 2. Configuration

Create `db_config.json` in the project root:

```bash
cp config/db_config.json.example db_config.json
```

Edit with your database credentials:

```json
{
  "host": "localhost",
  "port": 1521,
  "user": "system",
  "password": "YourPassword",
  "service_name": "FREEPDB1",
  "wallet_location": "/path/to/wallet",
  "wallet_password": "WalletPass123"
}
```

See [docs/DB_CONFIG_SETUP.md](docs/DB_CONFIG_SETUP.md) for detailed configuration options.

### 3. Run Examples

```bash
# Basic examples
cd examples
python3 examples.py

# Comprehensive query testing
python3 example_comprehensive_test.py

# From project root
python3 examples/examples.py
```

## Basic Usage

```python
from oracle_test_lib import OracleTestClient, LoadProfile
import json

# Load database configuration
with open('db_config.json', 'r') as f:
    db_config = json.load(f)

# Create client with low load profile
load_profile = LoadProfile.low_load()
client = OracleTestClient(db_config, load_profile, use_tls=True)

# Run write test
results = client.run_write_test()
print(results.get_summary())
```

## Load Profiles

### Predefined Profiles

| Profile | Connections | Ops/Sec | Data Size | Think Time | Duration |
|---------|------------|---------|-----------|------------|----------|
| **Low Load** | 2 | 10 | 10 KB | 100ms | 60s |
| **High Load** | 50 | 500 | 1024 KB | 0ms | 300s |

### Custom Profile

```python
custom_load = LoadProfile.custom(
    name="Medium Load",
    concurrent_connections=10,
    operations_per_second=100,
    data_size_kb=500,
    think_time_ms=25,
    duration_seconds=180
)

client = OracleTestClient(db_config, custom_load, use_tls=True)
```

## Comprehensive Query Testing

Test large datasets with multiple column types:

```python
from oracle_test_lib import OracleTestClient, OracleTestConnection, LoadProfile

# Create client (automatically creates tables)
client = OracleTestClient(db_config, load_profile, use_tls=True)
conn = OracleTestConnection("test", db_config, use_tls=True)
conn.connect()

# Populate table with 50,000 rows
stats = client.populate_comprehensive_data(num_rows=50000, connection=conn)
print(f"Populated {stats['rows_inserted']} rows at {stats['rows_per_second']:.0f} rows/sec")

# Run query tests
results = client.test_comprehensive_queries(conn, 'all')

# Test query performance
perf = client.test_query_performance(
    conn,
    "SELECT * FROM test_comprehensive WHERE status = 'active' AND ROWNUM <= 100",
    iterations=10
)
print(f"Average query time: {perf['avg_time_ms']:.2f}ms")
```

See [docs/COMPREHENSIVE_TESTING.md](docs/COMPREHENSIVE_TESTING.md) for detailed guide.

## Command-Line Interface

```bash
# Test connection
python oracle_test_cli.py --host localhost --user system --password pass --test-connection

# Run write test
python oracle_test_cli.py --host localhost --user system --password pass \
  --test-type write --output results.json

# Run with config file
python oracle_test_cli.py --config config/config.example.json --test-type read
```

## TLS/SSL Configuration

### Using Wallet

```json
{
  "host": "localhost",
  "port": 2484,
  "user": "system",
  "password": "TestPassword123",
  "service_name": "FREEPDB1",
  "wallet_location": "/path/to/wallet",
  "wallet_password": "WalletPass123"
}
```

```python
client = OracleTestClient(db_config, load_profile, use_tls=True)
```

### Using SSL Context

```python
import ssl

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

db_config['ssl_context'] = ssl_context
client = OracleTestClient(db_config, load_profile, use_tls=True)
```

See [docs/DOCKER_TLS_SETUP.md](docs/DOCKER_TLS_SETUP.md) for Docker TLS setup.

## Testing

```bash
# Run unit tests
cd tests
pytest test_oracle_lib.py -v

# Or from project root
pytest tests/test_oracle_lib.py -v
```

## Documentation

| Document | Description |
|----------|-------------|
| [QUICKSTART.md](docs/QUICKSTART.md) | Quick start guide and basic examples |
| [INSTALLATION.md](docs/INSTALLATION.md) | Installation instructions for all platforms |
| [DB_CONFIG_SETUP.md](docs/DB_CONFIG_SETUP.md) | Database configuration guide |
| [LOADPROFILE_REFERENCE.md](docs/LOADPROFILE_REFERENCE.md) | LoadProfile parameters and usage guide |
| [COMPREHENSIVE_TESTING.md](docs/COMPREHENSIVE_TESTING.md) | Comprehensive query testing guide |
| [TEST_RESULTS_OUTPUT.md](TEST_RESULTS_OUTPUT.md) | Test results output format and examples |
| [SEPARATE_READ_WRITE_METRICS.md](SEPARATE_READ_WRITE_METRICS.md) | Separate read/write metrics feature guide |
| [LOAD_PROFILE_COMPARISON.md](docs/LOAD_PROFILE_COMPARISON.md) | Load profile comparison (original vs cloud-optimized) |
| [DOCKER_TLS_SETUP.md](docs/DOCKER_TLS_SETUP.md) | Docker TLS/SSL setup guide |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Architecture and design patterns |
| [PROJECT_SUMMARY.md](docs/PROJECT_SUMMARY.md) | Complete project overview |

## Examples

| Script | Description |
|--------|-------------|
| [examples.py](examples/examples.py) | Basic usage examples for all features |
| [example_comprehensive_test.py](examples/example_comprehensive_test.py) | Comprehensive query testing with bulk data |

## Utility Scripts

| Script | Description |
|--------|-------------|
| [install.sh](scripts/install.sh) | Automated installation script |
| [discover_oracle_services.py](scripts/discover_oracle_services.py) | Discover Oracle services automatically |
| [setup_docker_tls.sh](scripts/setup_docker_tls.sh) | Complete Docker TLS setup |
| [setup_docker_tls_simple.sh](scripts/setup_docker_tls_simple.sh) | Simplified Docker TLS setup |

## Key Features

### Comprehensive Test Table

The `test_comprehensive` table includes 20+ column types for thorough testing:
- VARCHAR2, NUMBER, DATE, TIMESTAMP (with/without timezone)
- CLOB, BLOB, CHAR
- Business fields (status, category, price, quantity, email, description)
- Indexed columns for performance testing

### Bulk Data Population

Efficiently populate tables with millions of rows:
```python
stats = client.populate_comprehensive_data(
    num_rows=1000000,
    batch_size=2000,
    connection=conn
)
```

### Query Performance Testing

Test various query patterns:
- Simple SELECT queries
- WHERE clauses on indexed/non-indexed columns
- Aggregate functions (COUNT, AVG, SUM, MIN, MAX)
- GROUP BY and ORDER BY
- Complex multi-condition queries

## Performance Tips

1. **Batch Size**: For bulk inserts, use batch sizes of 500-2000 rows
2. **Indexes**: The comprehensive table includes indexes on frequently queried columns
3. **Connection Pooling**: Use multiple connections for concurrent testing
4. **Prepared Statements**: Enable `use_prepared_statements=True` for better performance

## Troubleshooting

### Connection Issues

```bash
# Test connectivity
python oracle_test_cli.py --host localhost --user system --password pass --test-connection

# Discover services
python scripts/discover_oracle_services.py --host localhost --user system --password pass
```

### Configuration File Not Found

Ensure `db_config.json` exists in the project root:
```bash
ls -la db_config.json
```

See [docs/DB_CONFIG_SETUP.md](docs/DB_CONFIG_SETUP.md) for more troubleshooting.

## Requirements

- Python 3.8+
- oracledb (python-oracledb)
- Oracle Database 12c+

## License

This project is for testing and development purposes.

## Contributing

When adding new features:
1. Add documentation to `docs/`
2. Add examples to `examples/`
3. Add tests to `tests/`
4. Update this README

## Security

- Never commit `db_config.json` (already in `.gitignore`)
- Use `chmod 600 db_config.json` to restrict permissions
- Rotate passwords regularly
- Use least-privilege accounts for testing

## Related Resources

- [Oracle Python Driver Documentation](https://python-oracledb.readthedocs.io/)
- [Oracle Database Documentation](https://docs.oracle.com/en/database/)
- [Oracle Instant Client](https://www.oracle.com/database/technologies/instant-client.html)

## Support

For issues, questions, or contributions:
1. Check [docs/](docs/) for detailed documentation
2. Review [examples/](examples/) for usage patterns
3. Run [scripts/discover_oracle_services.py](scripts/discover_oracle_services.py) for connection issues
