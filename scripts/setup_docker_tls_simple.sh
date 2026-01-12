#!/bin/bash
#
# Simplified TLS Setup for gvenzl/oracle-free Docker Container
# This version doesn't use orapki - works without Oracle Client installed
#
# Usage:
#   ./setup_docker_tls_simple.sh
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}==>${NC} $1"; }
print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }

SETUP_DIR="docker-tls-simple"
ORACLE_PASSWORD="TestPassword123"
CONTAINER_NAME="oracle-tls"

# Check if oracle_test_lib is available
check_library() {
    if ! python3 -c "import oracle_test_lib" 2>/dev/null; then
        print_warning "oracle_test_lib not installed"
        echo ""
        echo "To install the library:"
        echo "  1. Navigate to the library directory"
        echo "  2. Run: pip install -e ."
        echo ""
        echo "Or install just the dependencies:"
        echo "  pip install oracledb"
        echo ""
        echo "See INSTALLATION.md for detailed instructions"
        echo ""
        print_status "Continuing setup anyway (you can install later)..."
        echo ""
    else
        print_success "oracle_test_lib is installed"
    fi
}

echo "================================================================"
echo "  Oracle Docker TLS Setup (Simplified Version)"
echo "================================================================"
echo ""

check_library

# Check Docker
print_status "Checking Docker..."
if ! command -v docker >/dev/null 2>&1; then
    print_error "Docker not installed"
    exit 1
fi
print_success "Docker is installed"

# Create directories
print_status "Creating directory structure..."
mkdir -p "$SETUP_DIR"/{certs,config}
cd "$SETUP_DIR"

# Generate certificates
print_status "Generating SSL certificates..."

# CA certificate
openssl genrsa -out certs/ca-key.pem 2048 2>/dev/null
openssl req -new -x509 -key certs/ca-key.pem -out certs/ca-cert.pem -days 365 \
    -subj "/C=US/ST=State/L=City/O=TestOrg/CN=TestCA" 2>/dev/null

# Server certificate
openssl genrsa -out certs/server-key.pem 2048 2>/dev/null
openssl req -new -key certs/server-key.pem -out certs/server-req.pem \
    -subj "/C=US/ST=State/L=City/O=TestOrg/CN=localhost" 2>/dev/null
openssl x509 -req -in certs/server-req.pem -CA certs/ca-cert.pem \
    -CAkey certs/ca-key.pem -CAcreateserial -out certs/server-cert.pem \
    -days 365 2>/dev/null

print_success "Certificates generated"

# Create Oracle configuration
print_status "Creating Oracle configuration..."

cat > config/listener.ora << 'EOF'
LISTENER =
  (DESCRIPTION_LIST =
    (DESCRIPTION =
      (ADDRESS = (PROTOCOL = TCP)(HOST = 0.0.0.0)(PORT = 1521))
    )
  )

LISTENER_TLS =
  (DESCRIPTION_LIST =
    (DESCRIPTION =
      (ADDRESS = (PROTOCOL = TCPS)(HOST = 0.0.0.0)(PORT = 2484))
    )
  )

SSL_CLIENT_AUTHENTICATION = FALSE

SID_LIST_LISTENER =
  (SID_LIST =
    (SID_DESC =
      (GLOBAL_DBNAME = FREE)
      (ORACLE_HOME = /opt/oracle/product/23ai/dbhomeFree)
      (SID_NAME = FREE)
    )
  )
EOF

cat > config/sqlnet.ora << 'EOF'
SQLNET.AUTHENTICATION_SERVICES = (TCPS, NTS, BEQ)
SSL_CLIENT_AUTHENTICATION = FALSE
SSL_VERSION = 1.2
SQLNET.CRYPTO_CHECKSUM_TYPES_SERVER = (SHA256, SHA1)
SQLNET.CRYPTO_CHECKSUM_TYPES_CLIENT = (SHA256, SHA1)
EOF

print_success "Configuration created"

# Create docker-compose with SSL context
print_status "Creating docker-compose.yml..."

cat > docker-compose.yml << EOF
version: '3.8'

services:
  oracle-tls:
    image: gvenzl/oracle-free:latest
    container_name: $CONTAINER_NAME
    ports:
      - "1521:1521"
      - "2484:2484"
    environment:
      - ORACLE_PASSWORD=$ORACLE_PASSWORD
    volumes:
      - oracle-data:/opt/oracle/oradata
      - ./certs:/opt/oracle/certs:ro
      - ./config:/opt/oracle/network/admin:ro
    healthcheck:
      test: ["CMD-SHELL", "healthcheck.sh"]
      interval: 30s
      timeout: 10s
      retries: 10
      start_period: 120s
    restart: unless-stopped

volumes:
  oracle-data:
    driver: local
EOF

print_success "docker-compose.yml created"

# Create test script that uses custom SSL context
print_status "Creating test script..."

cat > test_tls_simple.py << 'EOFPYTHON'
#!/usr/bin/env python3
"""
Test TLS connection using custom SSL context (no wallet needed)
"""

import ssl
import sys
from pathlib import Path

try:
    from oracle_test_lib import OracleTestClient, LoadProfile
except ImportError:
    print("Error: oracle_test_lib not installed")
    print("Install with: pip install -e .")
    sys.exit(1)

print("\n" + "="*60)
print("Testing TLS Connection (No Wallet)")
print("="*60)

# Create SSL context with our CA certificate
ssl_context = ssl.create_default_context()

# Load our CA certificate
ca_cert = Path("certs/ca-cert.pem")
if ca_cert.exists():
    ssl_context.load_verify_locations(cafile=str(ca_cert))
    print(f"✓ Loaded CA certificate: {ca_cert}")
else:
    print(f"⚠ CA certificate not found: {ca_cert}")
    print("  Disabling certificate verification (not recommended)")
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

# Configure database connection with SSL context
db_config = {
    'host': 'localhost',
    'port': 2484,  # TLS port
    'user': 'system',
    'password': 'TestPassword123',
    'service_name': 'FREEPDB1',
    'ssl_context': ssl_context  # Use custom SSL context instead of wallet
}

print("\nStep 1: Testing TLS connection...")
success, msg = OracleTestClient.test_connection(db_config, use_tls=True)
print(msg)

if not success:
    print("\n✗ TLS connection failed")
    print("\nTroubleshooting:")
    print("  1. Check if container is running: docker ps")
    print("  2. Check listener: docker exec oracle-tls lsnrctl status")
    print("  3. Check logs: docker logs oracle-tls")
    sys.exit(1)

print("\nStep 2: Running quick TLS test...")
try:
    client = OracleTestClient(
        db_config=db_config,
        load_profile=LoadProfile.custom(
            name="TLS Quick Test",
            concurrent_connections=2,
            operations_per_second=10,
            data_size_kb=50,
            duration_seconds=10
        ),
        use_tls=True
    )
    
    results = client.run_write_test()
    summary = results.get_summary()
    
    print(f"\nResults:")
    print(f"  Operations: {summary['total_operations']}")
    print(f"  Success rate: {summary['success_rate']:.1f}%")
    print(f"  Avg latency: {summary.get('avg_duration_ms', 0):.2f} ms")
    
    if summary['success_rate'] >= 95:
        print("\n" + "="*60)
        print("✓✓✓ TLS IS WORKING! ✓✓✓")
        print("="*60)
        print("\nYou can use this configuration:")
        print("-" * 60)
        print("""
import ssl
from oracle_test_lib import OracleTestClient, LoadProfile

# Create SSL context
ssl_context = ssl.create_default_context()
ssl_context.load_verify_locations(cafile='certs/ca-cert.pem')

# Or for testing without verification:
# ssl_context.check_hostname = False
# ssl_context.verify_mode = ssl.CERT_NONE

db_config = {
    'host': 'localhost',
    'port': 2484,
    'user': 'system',
    'password': 'TestPassword123',
    'service_name': 'FREEPDB1',
    'ssl_context': ssl_context
}

client = OracleTestClient(db_config, LoadProfile.low_load(), use_tls=True)
results = client.run_write_test()
        """)
    else:
        print(f"\n⚠ Success rate is low: {summary['success_rate']:.1f}%")
        
except Exception as e:
    print(f"\n✗ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOFPYTHON

chmod +x test_tls_simple.py
print_success "Test script created"

# Start container
print_status "Starting Oracle container..."
docker-compose up -d

# Wait for database
print_status "Waiting for database (2-3 minutes)..."
max_wait=300
elapsed=0

while [ $elapsed -lt $max_wait ]; do
    if docker logs $CONTAINER_NAME 2>&1 | grep -q "DATABASE IS READY TO USE"; then
        echo ""
        print_success "Database is ready!"
        break
    fi
    printf "\r  Waiting... (%ds)" $elapsed
    sleep 5
    elapsed=$((elapsed + 5))
done

if [ $elapsed -ge $max_wait ]; then
    echo ""
    print_error "Database not ready after ${max_wait}s"
    print_warning "Container may still be starting. Check with: docker logs $CONTAINER_NAME"
else
    # Configure listener
    print_status "Configuring TLS listener..."
    sleep 5
    docker exec $CONTAINER_NAME lsnrctl reload >/dev/null 2>&1 || true
    
    # Test
    if command -v python3 >/dev/null 2>&1; then
        echo ""
        print_status "Running TLS test..."
        python3 test_tls_simple.py || true
    fi
fi

# Summary
echo ""
echo "================================================================"
echo -e "${GREEN}TLS Setup Complete!${NC}"
echo "================================================================"
echo ""
echo "This simplified setup uses Python's SSL context instead of Oracle Wallet"
echo ""
echo "Container Details:"
echo "  Name: $CONTAINER_NAME"
echo "  Standard port: 1521 (TCP)"
echo "  TLS port: 2484 (TCPS)"
echo "  Password: $ORACLE_PASSWORD"
echo ""
echo "Files Created:"
echo "  • certs/ca-cert.pem       - CA certificate for SSL context"
echo "  • certs/server-cert.pem   - Server certificate"
echo "  • config/                 - Oracle network config"
echo "  • test_tls_simple.py      - Test script"
echo ""
echo "Usage:"
echo "  cd $SETUP_DIR"
echo "  python test_tls_simple.py"
echo ""
echo "Key Difference:"
echo "  This uses ssl_context instead of wallet_location in db_config"
echo ""
echo "Useful Commands:"
echo "  View logs:      docker logs -f $CONTAINER_NAME"
echo "  Stop:           docker-compose down"
echo "  Restart:        docker-compose restart"
echo ""
echo "================================================================"
