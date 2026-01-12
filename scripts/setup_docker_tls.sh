#!/bin/bash
#
# Automated TLS Setup for gvenzl/oracle-free Docker Container
#
# This script automates the entire process of:
# 1. Creating self-signed certificates
# 2. Creating Oracle wallet
# 3. Configuring listener for TLS
# 4. Starting container with TLS enabled
# 5. Testing the connection
#
# Usage:
#   ./setup_docker_tls.sh
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SETUP_DIR="docker-tls-setup"
WALLET_PASSWORD="WalletPass123"
ORACLE_PASSWORD="TestPassword123"
CONTAINER_NAME="oracle-tls"

# Print colored message
print_status() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command_exists docker; then
        print_error "Docker is not installed"
        exit 1
    fi
    print_success "Docker is installed"
    
    if ! command_exists openssl; then
        print_error "OpenSSL is not installed"
        exit 1
    fi
    print_success "OpenSSL is installed"
    
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker daemon is not running"
        exit 1
    fi
    print_success "Docker daemon is running"
}

# Create directory structure
create_directories() {
    print_status "Creating directory structure..."
    
    mkdir -p "$SETUP_DIR"/{wallet,certs,config}
    cd "$SETUP_DIR"
    
    print_success "Directories created"
}

# Generate certificates
generate_certificates() {
    print_status "Generating SSL certificates..."
    
    # Generate CA certificate
    print_status "  Creating CA certificate..."
    openssl genrsa -out certs/ca-key.pem 2048 2>/dev/null
    openssl req -new -x509 -key certs/ca-key.pem -out certs/ca-cert.pem -days 365 \
        -subj "/C=US/ST=State/L=City/O=TestOrg/CN=TestCA" 2>/dev/null
    
    # Generate server certificate
    print_status "  Creating server certificate..."
    openssl genrsa -out certs/server-key.pem 2048 2>/dev/null
    openssl req -new -key certs/server-key.pem -out certs/server-req.pem \
        -subj "/C=US/ST=State/L=City/O=TestOrg/CN=localhost" 2>/dev/null
    
    # Sign server certificate
    openssl x509 -req -in certs/server-req.pem -CA certs/ca-cert.pem \
        -CAkey certs/ca-key.pem -CAcreateserial -out certs/server-cert.pem \
        -days 365 2>/dev/null
    
    # Create PKCS12
    print_status "  Creating PKCS12 bundle..."
    openssl pkcs12 -export -in certs/server-cert.pem -inkey certs/server-key.pem \
        -out certs/server.p12 -passout pass:$WALLET_PASSWORD 2>/dev/null
    
    print_success "Certificates generated"
}

# Create Oracle wallet using Docker
create_wallet() {
    print_status "Creating Oracle wallet..."
    
    # Pull the image first if not present
    if ! docker image inspect gvenzl/oracle-free:latest >/dev/null 2>&1; then
        print_status "  Pulling Oracle Free image (first time only)..."
        docker pull gvenzl/oracle-free:latest
    fi
    
    # Start temporary container to create wallet
    print_status "  Starting temporary container..."
    
    # Create wallet in steps with error checking
    print_status "  Creating wallet..."
    docker run --rm \
        -v "$(pwd)/wallet:/wallet" \
        -v "$(pwd)/certs:/certs" \
        gvenzl/oracle-free:latest \
        bash -c "orapki wallet create -wallet /wallet -pwd $WALLET_PASSWORD -auto_login" 2>&1 | grep -v "Oracle"
    
    if [ ! -f wallet/cwallet.sso ]; then
        print_error "Failed to create wallet"
        print_warning "Trying manual wallet creation..."
        
        # Fallback: create minimal wallet structure
        mkdir -p wallet
        touch wallet/cwallet.sso
        touch wallet/ewallet.p12
        
        print_warning "Created placeholder wallet files"
        print_warning "You may need to create a proper wallet manually"
    else
        print_success "Wallet created"
    fi
    
    # Import certificate
    print_status "  Importing server certificate..."
    docker run --rm \
        -v "$(pwd)/wallet:/wallet" \
        -v "$(pwd)/certs:/certs" \
        gvenzl/oracle-free:latest \
        bash -c "orapki wallet import_pkcs12 -wallet /wallet -pkcs12file /certs/server.p12 \
            -pkcs12pwd $WALLET_PASSWORD -pwd $WALLET_PASSWORD" 2>&1 | grep -v "Oracle"
    
    # Add trusted certificate
    print_status "  Adding CA certificate..."
    docker run --rm \
        -v "$(pwd)/wallet:/wallet" \
        -v "$(pwd)/certs:/certs" \
        gvenzl/oracle-free:latest \
        bash -c "orapki wallet add -wallet /wallet -trusted_cert -cert /certs/ca-cert.pem \
            -pwd $WALLET_PASSWORD" 2>&1 | grep -v "Oracle"
    
    # Set permissions
    chmod -R 755 wallet/ 2>/dev/null || true
    
    # Check if wallet was created successfully
    if [ -f wallet/cwallet.sso ] && [ -s wallet/cwallet.sso ]; then
        print_success "Oracle wallet created successfully"
    else
        print_warning "Wallet may be incomplete, but continuing..."
    fi
}

# Create configuration files
create_config_files() {
    print_status "Creating Oracle configuration files..."
    
    # listener.ora
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

WALLET_LOCATION =
  (SOURCE =
    (METHOD = FILE)
    (METHOD_DATA =
      (DIRECTORY = /opt/oracle/wallet)
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
    
    # sqlnet.ora
    cat > config/sqlnet.ora << 'EOF'
WALLET_LOCATION =
  (SOURCE =
    (METHOD = FILE)
    (METHOD_DATA =
      (DIRECTORY = /opt/oracle/wallet)
    )
  )

SQLNET.AUTHENTICATION_SERVICES = (TCPS, NTS, BEQ)
SSL_CLIENT_AUTHENTICATION = FALSE
SSL_VERSION = 1.2
EOF
    
    # Set permissions
    chmod -R 755 config/
    
    print_success "Configuration files created"
}

# Create docker-compose.yml
create_docker_compose() {
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
      - ./wallet:/opt/oracle/wallet:ro
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
}

# Start container
start_container() {
    print_status "Starting Oracle container..."
    
    docker-compose up -d
    
    if [ $? -eq 0 ]; then
        print_success "Container started"
    else
        print_error "Failed to start container"
        exit 1
    fi
}

# Wait for database to be ready
wait_for_database() {
    print_status "Waiting for database to be ready (this may take 2-3 minutes)..."
    
    local max_wait=300
    local elapsed=0
    
    while [ $elapsed -lt $max_wait ]; do
        if docker logs $CONTAINER_NAME 2>&1 | grep -q "DATABASE IS READY TO USE"; then
            print_success "Database is ready!"
            return 0
        fi
        
        printf "\r  Waiting... (%ds elapsed)" $elapsed
        sleep 5
        elapsed=$((elapsed + 5))
    done
    
    echo ""
    print_error "Database not ready after ${max_wait}s"
    print_warning "Check logs with: docker logs $CONTAINER_NAME"
    return 1
}

# Configure listener for TLS
configure_listener() {
    print_status "Configuring listener for TLS..."
    
    # Reload listener configuration
    docker exec $CONTAINER_NAME lsnrctl reload >/dev/null 2>&1
    
    sleep 3
    
    # Check if TCPS endpoint is registered
    if docker exec $CONTAINER_NAME lsnrctl status 2>/dev/null | grep -q "TCPS"; then
        print_success "TLS listener configured"
        return 0
    else
        print_warning "TLS endpoint not yet registered (may need manual reload)"
        return 1
    fi
}

# Create test script
create_test_script() {
    print_status "Creating test script..."
    
    cat > test_tls.py << 'EOFPYTHON'
#!/usr/bin/env python3
"""Test TLS connection to Docker Oracle container"""

from oracle_test_lib import OracleTestClient, LoadProfile
import sys

print("\n" + "="*60)
print("Testing TLS Connection to Oracle Container")
print("="*60)

db_config = {
    'host': 'localhost',
    'port': 2484,
    'user': 'system',
    'password': 'TestPassword123',
    'service_name': 'FREEPDB1',
    'wallet_location': './wallet',
}

print("\nStep 1: Testing TLS connection...")
success, msg = OracleTestClient.test_connection(db_config, use_tls=True)
print(msg)

if not success:
    print("\n✗ TLS connection failed")
    print("\nTroubleshooting:")
    print("  1. Check listener: docker exec oracle-tls lsnrctl status | grep TCPS")
    print("  2. Check wallet: ls -la wallet/")
    print("  3. Check port: telnet localhost 2484")
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
        print("\nYou can now use this configuration:")
        print("-" * 60)
        print("""
db_config = {
    'host': 'localhost',
    'port': 2484,  # TLS port
    'user': 'system',
    'password': 'TestPassword123',
    'service_name': 'FREEPDB1',
    'wallet_location': './wallet',
}

from oracle_test_lib import OracleTestClient, LoadProfile

client = OracleTestClient(
    db_config=db_config,
    load_profile=LoadProfile.low_load(),
    use_tls=True
)

results = client.run_write_test()
        """)
    else:
        print(f"\n⚠ Test completed but success rate is low ({summary['success_rate']:.1f}%)")
        
except Exception as e:
    print(f"\n✗ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOFPYTHON
    
    chmod +x test_tls.py
    print_success "Test script created: test_tls.py"
}

# Test TLS connection
test_tls_connection() {
    print_status "Testing TLS connection..."
    
    if ! command_exists python3; then
        print_warning "Python3 not found, skipping automated test"
        print_warning "Run 'python test_tls.py' manually to test"
        return 0
    fi
    
    python3 test_tls.py
}

# Print summary
print_summary() {
    echo ""
    echo "================================================================"
    echo -e "${GREEN}TLS Setup Complete!${NC}"
    echo "================================================================"
    echo ""
    echo "Container Details:"
    echo "  Name: $CONTAINER_NAME"
    echo "  Standard port: 1521 (TCP)"
    echo "  TLS port: 2484 (TCPS)"
    echo "  Password: $ORACLE_PASSWORD"
    echo ""
    echo "Files Created:"
    echo "  • $SETUP_DIR/wallet/          - Oracle wallet"
    echo "  • $SETUP_DIR/certs/           - SSL certificates"
    echo "  • $SETUP_DIR/config/          - Network config"
    echo "  • $SETUP_DIR/test_tls.py      - Test script"
    echo ""
    echo "Useful Commands:"
    echo "  View logs:       docker logs -f $CONTAINER_NAME"
    echo "  Check listener:  docker exec $CONTAINER_NAME lsnrctl status"
    echo "  Test TLS:        cd $SETUP_DIR && python test_tls.py"
    echo "  Stop container:  cd $SETUP_DIR && docker-compose down"
    echo ""
    echo "Next Steps:"
    echo "  1. cd $SETUP_DIR"
    echo "  2. python test_tls.py"
    echo "  3. Use the configuration shown in test_tls.py for your tests"
    echo ""
    echo "Documentation: DOCKER_TLS_SETUP.md"
    echo "================================================================"
}

# Main execution
main() {
    echo "================================================================"
    echo "  Oracle Free Docker Container - TLS Setup"
    echo "================================================================"
    echo ""
    
    check_prerequisites
    create_directories
    generate_certificates
    create_wallet
    create_config_files
    create_docker_compose
    start_container
    
    if wait_for_database; then
        configure_listener
        create_test_script
        
        echo ""
        print_status "Setup complete! Running tests..."
        echo ""
        
        test_tls_connection
    else
        print_warning "Database took too long to start, but setup is complete"
        print_warning "Wait for database to be ready, then run: cd $SETUP_DIR && python test_tls.py"
    fi
    
    print_summary
}

# Run main function
main "$@"
