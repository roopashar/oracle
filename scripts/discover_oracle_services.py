#!/usr/bin/env python3
"""
Oracle Service Discovery Tool

This script helps you find the correct Oracle service name for your database.
Run this before using the Oracle Test Library if you're getting service name errors.

Usage:
    python discover_oracle_services.py
    python discover_oracle_services.py --host mydb.example.com --port 1521
"""

import argparse
import socket
import sys

try:
    import oracledb
except ImportError:
    print("Error: oracledb module not installed")
    print("Install it with: pip install oracledb")
    sys.exit(1)


def check_port(host, port):
    """Check if the Oracle port is open"""
    print(f"\n{'='*60}")
    print(f"Step 1: Checking if port {port} is open on {host}")
    print('='*60)
    
    try:
        sock = socket.create_connection((host, port), timeout=3)
        sock.close()
        print(f"✓ Port {port} is OPEN on {host}")
        return True
    except socket.timeout:
        print(f"✗ Connection TIMEOUT - port may be filtered")
        return False
    except socket.error as e:
        print(f"✗ Cannot connect to {host}:{port}")
        print(f"  Error: {e}")
        print("\nPossible causes:")
        print("  1. Oracle listener is not running")
        print("  2. Firewall is blocking the port")
        print("  3. Wrong host or port")
        return False


def discover_services(host, port):
    """Discover Oracle services"""
    print(f"\n{'='*60}")
    print(f"Step 2: Discovering Oracle services")
    print('='*60)
    
    # Common service names to try
    common_services = [
        'XE',          # Oracle Express Edition
        'XEPDB1',      # XE Pluggable DB
        'FREE',        # Oracle Free
        'FREEPDB1',    # Free Pluggable DB
        'ORCL',        # Standard Oracle
        'ORCLPDB1',    # Standard Pluggable DB
        'ORCLCDB',     # Container DB
        'CDB',         # Container DB
        'PDB1',        # Pluggable DB 1
        'PROD',        # Production
        'DEV',         # Development
        'TEST',        # Test
    ]
    
    discovered = []
    
    print(f"\nTrying {len(common_services)} common service names...")
    print(f"{'-'*60}")
    
    for service in common_services:
        try:
            # Try to connect (will fail on password but that's OK)
            conn = oracledb.connect(
                user='test_user',
                password='wrong_password',
                host=host,
                port=port,
                service_name=service
            )
            conn.close()
            print(f"✓ {service:<15} - Found")
            discovered.append(service)
            
        except Exception as e:
            error_str = str(e)
            
            # Check for specific error types
            if 'ORA-01017' in error_str or 'invalid username/password' in error_str.lower():
                # Password error means service exists!
                print(f"✓ {service:<15} - Found (authentication needed)")
                discovered.append(service)
                
            elif 'DPY-6001' in error_str or 'ORA-12514' in error_str:
                # Service not registered
                print(f"✗ {service:<15} - Not found")
                
            elif 'ORA-12505' in error_str:
                # SID not known (wrong type)
                print(f"✗ {service:<15} - Wrong identifier type")
                
            else:
                # Other error
                print(f"? {service:<15} - Unknown error: {error_str[:40]}")
    
    return discovered


def test_service(host, port, service, user, password):
    """Test a specific service with credentials"""
    print(f"\n{'='*60}")
    print(f"Step 3: Testing service with your credentials")
    print('='*60)
    
    print(f"\nTrying to connect to:")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  Service: {service}")
    print(f"  User: {user}")
    print(f"  Password: {'*' * len(password)}")
    
    try:
        conn = oracledb.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            service_name=service
        )
        
        # Try a simple query
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM DUAL")
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        print(f"\n✓✓✓ SUCCESS! ✓✓✓")
        print(f"\nYour connection works with:")
        print(f"  service_name = '{service}'")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Connection failed")
        print(f"Error: {e}")
        return False


def print_config(host, port, service, user):
    """Print the working configuration"""
    print(f"\n{'='*60}")
    print("Use this configuration in your code:")
    print('='*60)
    print(f"""
db_config = {{
    'host': '{host}',
    'port': {port},
    'user': '{user}',
    'password': 'your_password',
    'service_name': '{service}'
}}

from oracle_test_lib import OracleTestClient, LoadProfile

client = OracleTestClient(
    db_config=db_config,
    load_profile=LoadProfile.low_load(),
    use_tls=False
)
""")


def main():
    parser = argparse.ArgumentParser(
        description='Discover Oracle database services',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python discover_oracle_services.py
  python discover_oracle_services.py --host db.example.com --port 1521
  python discover_oracle_services.py --host localhost --user testuser --password pass
        """
    )
    
    parser.add_argument('--host', default='localhost',
                       help='Database host (default: localhost)')
    parser.add_argument('--port', type=int, default=1521,
                       help='Database port (default: 1521)')
    parser.add_argument('--user', help='Database user (optional, for testing)')
    parser.add_argument('--password', help='Database password (optional, for testing)')
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("ORACLE SERVICE DISCOVERY TOOL")
    print("="*60)
    print(f"Scanning: {args.host}:{args.port}")
    
    # Step 1: Check if port is open
    if not check_port(args.host, args.port):
        print("\n✗ Cannot proceed - port is not accessible")
        print("\nTroubleshooting steps:")
        print("  1. Make sure Oracle database is running")
        print("  2. Start the listener: lsnrctl start")
        print("  3. Check firewall settings")
        print("  4. Verify host and port are correct")
        return 1
    
    # Step 2: Discover services
    discovered = discover_services(args.host, args.port)
    
    if not discovered:
        print("\n" + "="*60)
        print("✗ No services discovered automatically")
        print("="*60)
        print("\nTo find services manually, run on the database server:")
        print("  lsnrctl services")
        print("\nOr connect with sqlplus and run:")
        print("  SELECT name FROM v$database;")
        print("  SELECT name FROM v$pdbs;")
        return 1
    
    print("\n" + "="*60)
    print(f"✓ Found {len(discovered)} service(s):")
    print("="*60)
    for svc in discovered:
        print(f"  • {svc}")
    
    # Step 3: Test with credentials if provided
    if args.user and args.password:
        print(f"\nYou provided credentials - testing connection...")
        
        for service in discovered:
            if test_service(args.host, args.port, service, args.user, args.password):
                print_config(args.host, args.port, service, args.user)
                return 0
        
        print("\n✗ None of the discovered services worked with your credentials")
        print("Double-check your username and password")
        return 1
    else:
        print("\n" + "="*60)
        print("Next step: Test with your credentials")
        print("="*60)
        print(f"\nRun again with credentials to test:")
        print(f"  python {sys.argv[0]} \\")
        print(f"    --host {args.host} \\")
        print(f"    --port {args.port} \\")
        print(f"    --user YOUR_USERNAME \\")
        print(f"    --password YOUR_PASSWORD")
        print(f"\nOr try these service names in your code:")
        for svc in discovered:
            print(f"  db_config['service_name'] = '{svc}'")
        return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
