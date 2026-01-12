# Enable TLS on gvenzl/oracle-free Docker Container

## Complete Step-by-Step Guide

This guide shows you how to configure the `gvenzl/oracle-free` container to accept TLS connections for testing TLS client connectivity.

---

## Quick Setup (Automated)

I've created scripts to automate the entire TLS setup. Choose your method:

### Method 1: Using Setup Script (Easiest)

```bash
# Run the automated setup script
./setup_docker_tls.sh

# This will:
# 1. Create self-signed certificates
# 2. Create Oracle wallet
# 3. Configure listener for TLS
# 4. Start container with TLS enabled
# 5. Test the connection
```

### Method 2: Manual Step-by-Step

Follow the detailed steps below for full control.

---

## Manual Setup Steps

### Step 1: Create Directory Structure

```bash
# Create directories
mkdir -p docker-tls-setup/{wallet,certs,config}
cd docker-tls-setup

# Directory structure:
# docker-tls-setup/
# ├── wallet/      # Oracle wallet files
# ├── certs/       # SSL certificates
# └── config/      # Oracle network config
```

### Step 2: Generate Self-Signed Certificates

```bash
# Generate CA certificate
openssl genrsa -out certs/ca-key.pem 2048
openssl req -new -x509 -key certs/ca-key.pem -out certs/ca-cert.pem -days 365 \
  -subj "/C=US/ST=State/L=City/O=Test/CN=TestCA"

# Generate server certificate
openssl genrsa -out certs/server-key.pem 2048
openssl req -new -key certs/server-key.pem -out certs/server-req.pem \
  -subj "/C=US/ST=State/L=City/O=Test/CN=localhost"

# Sign server certificate with CA
openssl x509 -req -in certs/server-req.pem -CA certs/ca-cert.pem \
  -CAkey certs/ca-key.pem -CAcreateserial -out certs/server-cert.pem -days 365

# Create PKCS12 for Oracle wallet
openssl pkcs12 -export -in certs/server-cert.pem -inkey certs/server-key.pem \
  -out certs/server.p12 -passout pass:WalletPass123
```

### Step 3: Create Oracle Wallet

You have two options:

#### Option A: Using orapki (If Oracle Client Installed Locally)

```bash
# Create wallet
orapki wallet create -wallet wallet -pwd WalletPass123 -auto_login

# Import server certificate
orapki wallet import_pkcs12 -wallet wallet -pkcs12file certs/server.p12 \
  -pkcs12pwd WalletPass123 -pwd WalletPass123

# Add CA certificate as trusted
orapki wallet add -wallet wallet -trusted_cert -cert certs/ca-cert.pem \
  -pwd WalletPass123

# Verify wallet
orapki wallet display -wallet wallet
```

#### Option B: Create Inside Container (Easier)

```bash
# Start temporary container to create wallet
docker run --rm -it \
  -v $(pwd)/wallet:/wallet \
  -v $(pwd)/certs:/certs \
  gvenzl/oracle-free:latest bash

# Inside container:
orapki wallet create -wallet /wallet -pwd WalletPass123 -auto_login
orapki wallet import_pkcs12 -wallet /wallet -pkcs12file /certs/server.p12 \
  -pkcs12pwd WalletPass123 -pwd WalletPass123
orapki wallet add -wallet /wallet -trusted_cert -cert /certs/ca-cert.pem \
  -pwd WalletPass123
exit
```

### Step 4: Create Network Configuration Files

#### listener.ora

```bash
cat > config/listener.ora << 'EOF'
# Standard listener
LISTENER =
  (DESCRIPTION_LIST =
    (DESCRIPTION =
      (ADDRESS = (PROTOCOL = TCP)(HOST = 0.0.0.0)(PORT = 1521))
    )
  )

# TLS listener
LISTENER_TLS =
  (DESCRIPTION_LIST =
    (DESCRIPTION =
      (ADDRESS = (PROTOCOL = TCPS)(HOST = 0.0.0.0)(PORT = 2484))
    )
  )

# Wallet location
WALLET_LOCATION =
  (SOURCE =
    (METHOD = FILE)
    (METHOD_DATA =
      (DIRECTORY = /opt/oracle/wallet)
    )
  )

# Don't require client certificates
SSL_CLIENT_AUTHENTICATION = FALSE

# Use default listener name
SID_LIST_LISTENER =
  (SID_LIST =
    (SID_DESC =
      (GLOBAL_DBNAME = FREE)
      (ORACLE_HOME = /opt/oracle/product/23ai/dbhomeFree)
      (SID_NAME = FREE)
    )
  )
EOF
```

#### sqlnet.ora

```bash
cat > config/sqlnet.ora << 'EOF'
# Wallet location
WALLET_LOCATION =
  (SOURCE =
    (METHOD = FILE)
    (METHOD_DATA =
      (DIRECTORY = /opt/oracle/wallet)
    )
  )

# Enable TLS
SQLNET.AUTHENTICATION_SERVICES = (TCPS, NTS, BEQ)

# Don't require client certificates
SSL_CLIENT_AUTHENTICATION = FALSE

# SSL/TLS version
SSL_VERSION = 1.2

# Cipher suites (optional - for stronger security)
# SSL_CIPHER_SUITES = (SSL_RSA_WITH_AES_256_CBC_SHA)
EOF
```

#### tnsnames.ora (optional)

```bash
cat > config/tnsnames.ora << 'EOF'
FREEPDB1_TLS =
  (DESCRIPTION =
    (ADDRESS = (PROTOCOL = TCPS)(HOST = localhost)(PORT = 2484))
    (CONNECT_DATA =
      (SERVER = DEDICATED)
      (SERVICE_NAME = FREEPDB1)
    )
  )

FREE_TLS =
  (DESCRIPTION =
    (ADDRESS = (PROTOCOL = TCPS)(HOST = localhost)(PORT = 2484))
    (CONNECT_DATA =
      (SERVER = DEDICATED)
      (SERVICE_NAME = FREE)
    )
  )
EOF
```

### Step 5: Create docker-compose.yml

```bash
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  oracle-tls:
    image: gvenzl/oracle-free:latest
    container_name: oracle-tls
    ports:
      - "1521:1521"  # Standard port
      - "2484:2484"  # TLS port
    environment:
      - ORACLE_PASSWORD=TestPassword123
    volumes:
      - oracle-data:/opt/oracle/oradata
      - ./wallet:/opt/oracle/wallet:ro
      - ./config:/opt/oracle/network/admin:ro
    healthcheck:
      test: ["CMD-SHELL", "healthcheck.sh"]
      interval: 30s
      timeout: 10s
      retries: 10
      start_period: 120s
    restart: unless-stopped
    # Give oracle user access to wallet
    user: "54321:54321"

volumes:
  oracle-data:
    driver: local
EOF
```

### Step 6: Set Permissions

```bash
# Set correct ownership for Oracle user (UID 54321)
sudo chown -R 54321:54321 wallet config

# Or if sudo not available, make readable by all
chmod -R 755 wallet config
chmod 644 wallet/* config/*
```

### Step 7: Start Container

```bash
# Start with docker-compose
docker-compose up -d

# Wait for database to start
docker-compose logs -f

# Wait for: "DATABASE IS READY TO USE!"
```

### Step 8: Configure Listener for TLS

```bash
# Access container
docker exec -it oracle-tls bash

# Inside container - configure listener
cat >> /opt/oracle/network/admin/listener.ora << 'EOF'

LISTENER_TLS =
  (DESCRIPTION =
    (ADDRESS = (PROTOCOL = TCPS)(HOST = 0.0.0.0)(PORT = 2484))
  )

WALLET_LOCATION =
  (SOURCE =
    (METHOD = FILE)
    (METHOD_DATA =
      (DIRECTORY = /opt/oracle/wallet)
    )
  )

SSL_CLIENT_AUTHENTICATION = FALSE
EOF

# Reload listener
lsnrctl reload

# Verify TLS listener
lsnrctl status | grep -A 5 TCPS

# Should show:
# Listening Endpoints Summary...
#   (DESCRIPTION=(ADDRESS=(PROTOCOL=tcps)(HOST=0.0.0.0)(PORT=2484)))

exit
```

### Step 9: Test TLS Connection

#### Test with Python

```python
from oracle_test_lib import OracleTestClient, LoadProfile

# Configure for TLS
db_config = {
    'host': 'localhost',
    'port': 2484,  # TLS port
    'user': 'system',
    'password': 'TestPassword123',
    'service_name': 'FREEPDB1',
    'wallet_location': './wallet',
    'wallet_password': 'WalletPass123'  # May not be needed for auto-login
}

# Test TLS connection
success, msg = OracleTestClient.test_connection(db_config, use_tls=True)
print(msg)

if success:
    print("\n✓ TLS is working!")
    
    # Run a test
    client = OracleTestClient(
        db_config=db_config,
        load_profile=LoadProfile.low_load(),
        use_tls=True
    )
    
    results = client.run_write_test()
    print(results.get_summary())
else:
    print("\n✗ TLS connection failed")
    print("Check the troubleshooting section below")
```

#### Test with sqlplus

```bash
# Inside or outside container
sqlplus system/TestPassword123@"(DESCRIPTION=(ADDRESS=(PROTOCOL=TCPS)(HOST=localhost)(PORT=2484))(CONNECT_DATA=(SERVICE_NAME=FREEPDB1)))"
```

---

## Troubleshooting

### Issue: "Wallet not found"

```bash
# Check wallet files exist
ls -la wallet/

# Should see:
# cwallet.sso
# ewallet.p12

# Check permissions
ls -l wallet/
# Files should be readable by UID 54321 (oracle user)

# Fix permissions
sudo chown -R 54321:54321 wallet/
# Or
chmod -R 755 wallet/
```

### Issue: "TCPS endpoint not registered"

```bash
# Check listener status
docker exec oracle-tls lsnrctl status

# Should show TCPS endpoint on port 2484

# If not, reload listener
docker exec oracle-tls lsnrctl reload

# Or restart container
docker-compose restart
```

### Issue: "SSL handshake failed"

```bash
# Check wallet is valid
docker exec oracle-tls orapki wallet display -wallet /opt/oracle/wallet

# Check certificates
docker exec oracle-tls ls -la /opt/oracle/wallet/

# Verify network config
docker exec oracle-tls cat /opt/oracle/network/admin/listener.ora
docker exec oracle-tls cat /opt/oracle/network/admin/sqlnet.ora
```

### Issue: "Certificate verification failed"

This usually means the client can't verify the server certificate.

**Solution 1: Add CA certificate to client wallet**

```bash
# On the client side (your host machine)
orapki wallet create -wallet ./client-wallet -pwd ClientPass123 -auto_login
orapki wallet add -wallet ./client-wallet -trusted_cert \
  -cert certs/ca-cert.pem -pwd ClientPass123

# Use client wallet in config
db_config['wallet_location'] = './client-wallet'
```

**Solution 2: Disable verification (testing only!)**

```python
import ssl

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

db_config['ssl_context'] = ssl_context
```

### Issue: "Port 2484 not accessible"

```bash
# Check port is published
docker ps | grep oracle-tls

# Should show: 0.0.0.0:2484->2484/tcp

# Check firewall
sudo netstat -tlnp | grep 2484

# Test port connectivity
telnet localhost 2484
```

### Debug Mode

Enable detailed logging:

```bash
# In container, edit sqlnet.ora
docker exec -it oracle-tls bash

cat >> /opt/oracle/network/admin/sqlnet.ora << 'EOF'

TRACE_LEVEL_CLIENT = 16
TRACE_DIRECTORY_CLIENT = /tmp
TRACE_FILE_CLIENT = sqlnet_client.trc
EOF

# Check trace files
tail -f /tmp/sqlnet_client.trc
```

---

## Verification Checklist

Before testing with the Oracle Test Library:

- [ ] Wallet files exist (`cwallet.sso`, `ewallet.p12`)
- [ ] Wallet files are readable by container
- [ ] listener.ora contains TCPS endpoint on port 2484
- [ ] sqlnet.ora points to wallet location
- [ ] Container exposes port 2484 (check `docker ps`)
- [ ] Listener shows TCPS endpoint (`lsnrctl status`)
- [ ] Can connect to port 2484 (`telnet localhost 2484`)
- [ ] sqlplus TLS connection works

---

## Testing Different TLS Scenarios

### Scenario 1: Server Authentication Only (Most Common)

Server authenticates to client, client doesn't need certificate:

```python
db_config = {
    'host': 'localhost',
    'port': 2484,
    'user': 'system',
    'password': 'TestPassword123',
    'service_name': 'FREEPDB1',
    'wallet_location': './wallet',
}

client = OracleTestClient(db_config, profile, use_tls=True)
```

### Scenario 2: Mutual Authentication

Both server and client authenticate:

```bash
# Configure listener for client auth
# In listener.ora, change:
SSL_CLIENT_AUTHENTICATION = TRUE

# Create client certificate
openssl genrsa -out certs/client-key.pem 2048
openssl req -new -key certs/client-key.pem -out certs/client-req.pem \
  -subj "/C=US/ST=State/L=City/O=Test/CN=client"
openssl x509 -req -in certs/client-req.pem -CA certs/ca-cert.pem \
  -CAkey certs/ca-key.pem -out certs/client-cert.pem -days 365

# Create client wallet
orapki wallet create -wallet ./client-wallet -pwd ClientPass123 -auto_login
openssl pkcs12 -export -in certs/client-cert.pem -inkey certs/client-key.pem \
  -out certs/client.p12 -passout pass:ClientPass123
orapki wallet import_pkcs12 -wallet ./client-wallet -pkcs12file certs/client.p12 \
  -pkcs12pwd ClientPass123 -pwd ClientPass123

# Use in config
db_config['wallet_location'] = './client-wallet'
```

### Scenario 3: Multiple Concurrent TLS Connections

Test connection concurrency:

```python
from oracle_test_lib import OracleTestClient, LoadProfile

tls_load = LoadProfile.custom(
    name="TLS Concurrency Test",
    concurrent_connections=50,
    operations_per_second=100,
    data_size_kb=100,
    duration_seconds=60
)

client = OracleTestClient(db_config, tls_load, use_tls=True)
results = client.run_mixed_test()

summary = results.get_summary()
print(f"Success rate with 50 TLS connections: {summary['success_rate']:.2f}%")
```

---

## Performance Considerations

TLS adds overhead:

- **Latency**: +5-15% per operation (handshake)
- **Throughput**: -5-10% (encryption/decryption)
- **CPU**: Higher CPU usage on both client and server

To minimize impact:

1. **Use connection pooling**
2. **Reuse connections** (avoid frequent connect/disconnect)
3. **Use TLS 1.2+** (faster than older versions)
4. **Choose efficient cipher suites**

---

## Complete Test Example

```python
#!/usr/bin/env python3
"""
Complete TLS test with Docker container
"""

from oracle_test_lib import OracleTestClient, LoadProfile

# Configure for TLS
db_config = {
    'host': 'localhost',
    'port': 2484,
    'user': 'system',
    'password': 'TestPassword123',
    'service_name': 'FREEPDB1',
    'wallet_location': './wallet',
}

print("Testing TLS connection...")
success, msg = OracleTestClient.test_connection(db_config, use_tls=True)
print(msg)

if not success:
    print("\nTroubleshooting steps:")
    print("1. Check wallet exists: ls -la wallet/")
    print("2. Check listener: docker exec oracle-tls lsnrctl status")
    print("3. Check port: telnet localhost 2484")
    exit(1)

print("\n" + "="*60)
print("Running TLS Performance Tests")
print("="*60)

# Test 1: Basic connectivity
print("\nTest 1: Basic TLS connection test")
client = OracleTestClient(
    db_config=db_config,
    load_profile=LoadProfile.low_load(),
    use_tls=True
)
results = client.run_write_test()
print(f"Success rate: {results.get_summary()['success_rate']:.1f}%")

# Test 2: Concurrent connections
print("\nTest 2: Concurrent TLS connections")
concurrent_load = LoadProfile.custom(
    name="TLS Concurrent",
    concurrent_connections=20,
    operations_per_second=50,
    data_size_kb=100,
    duration_seconds=30
)
client2 = OracleTestClient(db_config, concurrent_load, use_tls=True, setup_tables=False)
results2 = client2.run_mixed_test()
summary2 = results2.get_summary()
print(f"20 concurrent connections: {summary2['success_rate']:.1f}% success")
print(f"P95 latency: {summary2.get('p95_duration_ms', 0):.2f} ms")

# Test 3: Large data over TLS
print("\nTest 3: Large data transfer over TLS")
large_data_load = LoadProfile.custom(
    name="TLS Large Data",
    concurrent_connections=5,
    operations_per_second=10,
    data_size_kb=1024,  # 1 MB
    duration_seconds=30
)
client3 = OracleTestClient(db_config, large_data_load, use_tls=True, setup_tables=False)
results3 = client3.run_write_test()
summary3 = results3.get_summary()
print(f"Throughput: {summary3.get('avg_throughput_mbps', 0):.2f} MB/s")
print(f"Data transferred: {summary3['total_data_transferred_mb']:.2f} MB")

print("\n" + "="*60)
print("All TLS tests completed!")
print("="*60)
```

---

## Clean Up

```bash
# Stop container
docker-compose down

# Remove volumes
docker-compose down -v

# Clean up files
cd ..
rm -rf docker-tls-setup/
```

---

## Summary

You can definitely test TLS with the `gvenzl/oracle-free` Docker container:

✅ **Steps:**
1. Generate certificates
2. Create Oracle wallet
3. Configure listener for TCPS
4. Mount wallet and config in container
5. Test with Oracle Test Library

✅ **Use Cases:**
- Testing TLS client behavior
- Performance testing with encryption
- Certificate validation testing
- Concurrent TLS connection testing

✅ **Perfect for:**
- Development
- CI/CD with TLS
- Pre-production testing
- Learning TLS configuration

See `setup_docker_tls.sh` (next file) for full automation!
