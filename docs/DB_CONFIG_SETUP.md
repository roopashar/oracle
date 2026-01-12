# Database Configuration Setup

This guide explains how to configure your Oracle database connection for the test library.

## Configuration File

The project now uses a `db_config.json` file to store database credentials, making it easier to manage and share configuration across different scripts.

## Setup Steps

### 1. Create Configuration File

Copy the example template:

```bash
cp db_config.json.example db_config.json
```

Or create `db_config.json` manually in the project root with your database credentials:

```json
{
  "host": "localhost",
  "port": 1521,
  "user": "system",
  "password": "TestPassword123",
  "service_name": "FREEPDB1",
  "wallet_location": "/Users/rsharma/Downloads/oracle/docker-tls-setup/wallet",
  "wallet_password": "WalletPass123"
}
```

### 2. Update Configuration

Edit `db_config.json` with your actual values:

| Field | Description | Example |
|-------|-------------|---------|
| `host` | Oracle database hostname or IP | `localhost`, `192.168.1.100` |
| `port` | Database port number | `1521` (default), `2484` (TLS) |
| `user` | Database username | `system`, `testuser` |
| `password` | Database password | Your password |
| `service_name` | Oracle service name | `FREEPDB1`, `ORCLPDB1`, `XEPDB1` |
| `wallet_location` | Path to Oracle wallet (for TLS) | `/path/to/wallet` |
| `wallet_password` | Wallet password (for TLS) | Your wallet password |

### 3. Secure the File

The `db_config.json` file contains sensitive credentials. It's already added to `.gitignore` to prevent accidental commits.

**Important**: Never commit `db_config.json` to version control!

### 4. Verify Configuration

Test your database connection:

```python
python3 examples.py
```

Or run the connection test specifically:

```python
from oracle_test_lib import OracleTestClient
import json

# Load config
with open('db_config.json', 'r') as f:
    db_config = json.load(f)

# Test connection
success, message = OracleTestClient.test_connection(db_config, use_tls=True)
print(message)
```

## Configuration Options

### Non-TLS Connection

For connections without TLS, you can omit the wallet fields:

```json
{
  "host": "localhost",
  "port": 1521,
  "user": "system",
  "password": "TestPassword123",
  "service_name": "FREEPDB1"
}
```

Then use `use_tls=False` in your code:

```python
client = OracleTestClient(db_config, load_profile, use_tls=False)
```

### TLS/SSL Connection

For TLS connections, include wallet configuration:

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

Use `use_tls=True`:

```python
client = OracleTestClient(db_config, load_profile, use_tls=True)
```

### SSL Context (Alternative to Wallet)

You can also provide a custom SSL context instead of wallet:

```python
import ssl
import json

# Load base config
with open('db_config.json', 'r') as f:
    db_config = json.load(f)

# Create SSL context
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Add to config
db_config['ssl_context'] = ssl_context

client = OracleTestClient(db_config, load_profile, use_tls=True)
```

## Usage in Scripts

### Load and Use Configuration

All example scripts now load configuration from the JSON file:

```python
import json
from oracle_test_lib import OracleTestClient, LoadProfile

# Load database configuration
with open('db_config.json', 'r') as f:
    db_config = json.load(f)

# Use configuration
load_profile = LoadProfile.low_load()
client = OracleTestClient(db_config, load_profile, use_tls=True)
results = client.run_write_test()
```

### Inline Configuration (Alternative)

If you prefer, you can still define configuration inline:

```python
db_config = {
    'host': 'localhost',
    'port': 1521,
    'user': 'testuser',
    'password': 'testpass',
    'service_name': 'FREEPDB1',
}

client = OracleTestClient(db_config, load_profile, use_tls=False)
```

## Scripts Updated

The following scripts now use `db_config.json`:

- [examples.py](examples.py) - All example functions
- [example_comprehensive_test.py](example_comprehensive_test.py) - Comprehensive query testing

## Troubleshooting

### File Not Found Error

```
FileNotFoundError: [Errno 2] No such file or directory: 'db_config.json'
```

**Solution**: Create the `db_config.json` file in the project root directory.

### Connection Failed

```
RuntimeError: Failed to establish setup connection
```

**Solutions**:
1. Verify database is running: `lsnrctl status` or check Docker container
2. Check host and port are correct
3. Verify username and password
4. Confirm service_name exists: `SELECT name FROM v$active_services;`
5. For TLS: verify wallet path and password are correct

### Invalid JSON

```
json.JSONDecodeError: Expecting property name enclosed in double quotes
```

**Solution**: Ensure `db_config.json` uses valid JSON format:
- Use double quotes for strings (not single quotes)
- No trailing commas
- Use `null` for null values (not `None`)

### Permission Denied

```
PermissionError: [Errno 13] Permission denied: 'db_config.json'
```

**Solution**: Check file permissions:
```bash
chmod 600 db_config.json
```

## Security Best Practices

1. **Never commit** `db_config.json` to version control (already in `.gitignore`)
2. **Restrict file permissions**: `chmod 600 db_config.json` (owner read/write only)
3. **Use environment variables** for CI/CD:
   ```python
   import os
   db_config = {
       'host': os.getenv('DB_HOST', 'localhost'),
       'user': os.getenv('DB_USER'),
       'password': os.getenv('DB_PASSWORD'),
       # ...
   }
   ```
4. **Use secrets management** in production (AWS Secrets Manager, HashiCorp Vault, etc.)
5. **Rotate passwords regularly**
6. **Use least-privilege accounts** for testing

## Example Configurations

### Local Docker Oracle Free

```json
{
  "host": "localhost",
  "port": 1521,
  "user": "system",
  "password": "TestPassword123",
  "service_name": "FREEPDB1"
}
```

### Local Docker with TLS

```json
{
  "host": "localhost",
  "port": 2484,
  "user": "system",
  "password": "TestPassword123",
  "service_name": "FREEPDB1",
  "wallet_location": "/Users/rsharma/Downloads/oracle/docker-tls-setup/wallet",
  "wallet_password": "WalletPass123"
}
```

### Oracle XE

```json
{
  "host": "localhost",
  "port": 1521,
  "user": "system",
  "password": "oracle",
  "service_name": "XEPDB1"
}
```

### Remote Oracle Cloud

```json
{
  "host": "your-db.oraclecloud.com",
  "port": 1521,
  "user": "admin",
  "password": "YourCloudPassword",
  "service_name": "yourdb_high",
  "wallet_location": "/path/to/cloud/wallet",
  "wallet_password": "CloudWalletPass"
}
```

## Related Documentation

- [README.md](README.md) - Main project documentation
- [COMPREHENSIVE_TESTING.md](COMPREHENSIVE_TESTING.md) - Comprehensive testing guide
- [DOCKER_TLS_SETUP.md](DOCKER_TLS_SETUP.md) - TLS setup with Docker
- [examples.py](examples.py) - Usage examples
