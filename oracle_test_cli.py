#!/usr/bin/env python3
"""
Command-line interface for Oracle Test Library

Usage:
    oracle-test --host localhost --user testuser --password testpass [options]
"""

import argparse
import sys
import json
import logging
from pathlib import Path
from oracle_test_lib import (
    OracleTestClient,
    OracleTestSuite,
    LoadProfile
)


def setup_logging(verbose: bool):
    """Configure logging based on verbosity"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def load_config_file(config_path: str) -> dict:
    """Load configuration from JSON file"""
    with open(config_path, 'r') as f:
        return json.load(f)


def create_db_config(args) -> dict:
    """Create database config from arguments"""
    config = {
        'host': args.host,
        'port': args.port,
        'user': args.user,
        'password': args.password,
        'service_name': args.service_name,
    }
    
    if args.wallet_location:
        config['wallet_location'] = args.wallet_location
    
    if args.wallet_password:
        config['wallet_password'] = args.wallet_password
    
    return config


def run_single_test(args):
    """Run a single test"""
    db_config = create_db_config(args)
    
    # Create load profile
    if args.load_profile == 'low':
        profile = LoadProfile.low_load()
    elif args.load_profile == 'high':
        profile = LoadProfile.high_load()
    else:  # custom
        profile = LoadProfile.custom(
            name="Custom",
            concurrent_connections=args.connections,
            operations_per_second=args.ops_per_sec,
            data_size_kb=args.data_size_kb,
            think_time_ms=args.think_time_ms,
            duration_seconds=args.duration
        )
    
    # Check if comparison test requested
    if args.compare_prepared:
        print("\n" + "=" * 60)
        print("PREPARED STATEMENT PERFORMANCE COMPARISON")
        print("=" * 60)
        
        client = OracleTestClient(
            db_config=db_config,
            load_profile=profile,
            use_tls=args.use_tls,
            setup_tables=not args.no_setup,
            use_prepared_statements=True  # Will be toggled in comparison
        )
        
        results = client.compare_prepared_vs_direct(
            num_operations=100,
            data_size_kb=args.data_size_kb
        )
        
        print("\n" + "=" * 60)
        print("COMPARISON RESULTS")
        print("=" * 60)
        
        for method, result in results.items():
            summary = result.get_summary()
            print(f"\n{method.upper()} SQL:")
            print(f"  Average duration: {summary.get('avg_duration_ms', 0):.2f} ms")
            print(f"  P95 duration: {summary.get('p95_duration_ms', 0):.2f} ms")
            print(f"  Success rate: {summary['success_rate']:.2f}%")
        
        # Calculate improvement
        prepared_avg = results['prepared'].get_summary().get('avg_duration_ms', 0)
        direct_avg = results['direct'].get_summary().get('avg_duration_ms', 0)
        if direct_avg > 0:
            improvement = ((direct_avg - prepared_avg) / direct_avg) * 100
            print(f"\nPrepared statements are {improvement:.1f}% faster")
        
        return 0
    
    print(f"\nRunning {args.test_type} test with {profile.name} profile...")
    print(f"Connections: {profile.concurrent_connections}")
    print(f"Operations/sec: {profile.operations_per_second}")
    print(f"Data size: {profile.data_size_kb} KB")
    print(f"Duration: {profile.duration_seconds}s")
    print(f"Prepared statements: {'enabled' if not args.no_prepared_statements else 'disabled'}")
    print("-" * 60)
    
    # Create client
    client = OracleTestClient(
        db_config=db_config,
        load_profile=profile,
        use_tls=args.use_tls,
        setup_tables=not args.no_setup,
        use_prepared_statements=not args.no_prepared_statements
    )
    
    # Run test
    if args.test_type == 'write':
        results = client.run_write_test()
    elif args.test_type == 'read':
        results = client.run_read_test()
    elif args.test_type == 'batch':
        # Batch write test
        print("Running batch write test...")
        conn = OracleTestConnection("batch_test", db_config, args.use_tls)
        if conn.connect():
            try:
                for i in range(10):  # 10 batches
                    metric = client.test_batch_write(conn, args.batch_size, profile.data_size_kb)
                    client.results.add_metric(metric)
            finally:
                conn.disconnect()
        results = client.results
    else:  # mixed
        results = client.run_mixed_test(read_write_ratio=args.read_ratio)
    
    # Print summary
    summary = results.get_summary()
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    print(f"Total operations: {summary['total_operations']}")
    print(f"Successful: {summary['successful_operations']}")
    print(f"Failed: {summary['failed_operations']}")
    print(f"Success rate: {summary['success_rate']:.2f}%")
    print(f"Data transferred: {summary['total_data_transferred_mb']:.2f} MB")
    
    if 'avg_duration_ms' in summary:
        print(f"\nLatency Statistics:")
        print(f"  Average: {summary['avg_duration_ms']:.2f} ms")
        print(f"  Median: {summary['median_duration_ms']:.2f} ms")
        print(f"  Min: {summary['min_duration_ms']:.2f} ms")
        print(f"  Max: {summary['max_duration_ms']:.2f} ms")
        print(f"  P95: {summary['p95_duration_ms']:.2f} ms")
        print(f"  P99: {summary['p99_duration_ms']:.2f} ms")
    
    if 'avg_throughput_mbps' in summary:
        print(f"\nThroughput Statistics:")
        print(f"  Average: {summary['avg_throughput_mbps']:.2f} MB/s")
        print(f"  Min: {summary['min_throughput_mbps']:.2f} MB/s")
        print(f"  Max: {summary['max_throughput_mbps']:.2f} MB/s")
    
    # Export results if requested
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"\nResults exported to: {output_path}")
    
    return 0 if summary['success_rate'] >= args.min_success_rate else 1


def run_test_suite(args):
    """Run complete test suite"""
    db_config = create_db_config(args)
    
    print("\n" + "=" * 60)
    print("ORACLE TEST SUITE")
    print("=" * 60)
    
    suite = OracleTestSuite(db_config=db_config, use_tls=args.use_tls)
    results = suite.run_all_tests(include_high_load=args.include_high_load)
    
    # Print summary
    suite.print_summary()
    
    # Export results
    if args.output:
        output_path = Path(args.output)
        summaries = [r.get_summary() for r in results]
        with open(output_path, 'w') as f:
            json.dump(summaries, f, indent=2)
        print(f"\nResults exported to: {output_path}")
    
    # Check if all tests passed minimum success rate
    all_passed = all(
        r.get_summary()['success_rate'] >= args.min_success_rate 
        for r in results
    )
    
    return 0 if all_passed else 1


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Oracle Database Client Testing Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run write test with low load
  oracle-test --host localhost --user test --password pass --test-type write
  
  # Run mixed test with custom load
  oracle-test --host db.example.com --user admin --password secret \\
    --test-type mixed --load-profile custom --connections 20 --ops-per-sec 100
  
  # Run full test suite with TLS
  oracle-test --host secure-db.example.com --user admin --password secret \\
    --suite --use-tls --wallet-location /opt/wallet --include-high-load
  
  # Run test from config file
  oracle-test --config config.json --test-type read --output results.json
        """
    )
    
    # Connection arguments
    conn_group = parser.add_argument_group('Connection Options')
    conn_group.add_argument('--host', help='Database host')
    conn_group.add_argument('--port', type=int, default=1521, help='Database port (default: 1521)')
    conn_group.add_argument('--user', help='Database user')
    conn_group.add_argument('--password', help='Database password')
    conn_group.add_argument('--service-name', default='ORCLPDB1', help='Service name (default: ORCLPDB1)')
    conn_group.add_argument('--use-tls', action='store_true', help='Enable TLS connections')
    conn_group.add_argument('--wallet-location', help='Oracle wallet location for TLS')
    conn_group.add_argument('--wallet-password', help='Oracle wallet password')
    
    # Test configuration
    test_group = parser.add_argument_group('Test Options')
    test_group.add_argument('--test-connection', action='store_true',
                           help='Test database connection and exit')
    test_group.add_argument('--discover-services', action='store_true',
                           help='Discover available database services and exit')
    test_group.add_argument('--test-type', choices=['write', 'read', 'mixed', 'batch'], 
                           default='mixed', help='Type of test to run (default: mixed)')
    test_group.add_argument('--load-profile', choices=['low', 'high', 'custom'],
                           default='low', help='Load profile (default: low)')
    test_group.add_argument('--suite', action='store_true', 
                           help='Run complete test suite')
    test_group.add_argument('--include-high-load', action='store_true',
                           help='Include high load tests in suite')
    test_group.add_argument('--no-setup', action='store_true',
                           help='Skip table setup (tables must exist)')
    test_group.add_argument('--no-prepared-statements', action='store_true',
                           help='Disable prepared statements (not recommended)')
    test_group.add_argument('--compare-prepared', action='store_true',
                           help='Compare prepared vs direct SQL performance')
    test_group.add_argument('--batch-size', type=int, default=100,
                           help='Batch size for batch operations (default: 100)')
    
    # Custom load profile arguments
    custom_group = parser.add_argument_group('Custom Load Options')
    custom_group.add_argument('--connections', type=int, default=10,
                             help='Concurrent connections (default: 10)')
    custom_group.add_argument('--ops-per-sec', type=int, default=50,
                             help='Operations per second (default: 50)')
    custom_group.add_argument('--data-size-kb', type=int, default=100,
                             help='Data size in KB (default: 100)')
    custom_group.add_argument('--think-time-ms', type=int, default=50,
                             help='Think time in ms (default: 50)')
    custom_group.add_argument('--duration', type=int, default=120,
                             help='Test duration in seconds (default: 120)')
    custom_group.add_argument('--read-ratio', type=float, default=0.5,
                             help='Read ratio for mixed tests (default: 0.5)')
    
    # Output options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument('--output', '-o', help='Output file for results (JSON)')
    output_group.add_argument('--verbose', '-v', action='store_true',
                             help='Enable verbose logging')
    output_group.add_argument('--min-success-rate', type=float, default=95.0,
                             help='Minimum success rate percentage (default: 95.0)')
    
    # Config file
    parser.add_argument('--config', help='Load configuration from JSON file')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Load config file if provided
    if args.config:
        try:
            config = load_config_file(args.config)
            # Override with config file values
            for key, value in config.items():
                if not hasattr(args, key) or getattr(args, key) is None:
                    setattr(args, key, value)
        except Exception as e:
            print(f"Error loading config file: {e}", file=sys.stderr)
            return 1
    
    # Discover services if requested (doesn't require full config)
    if args.discover_services:
        print("\n" + "=" * 60)
        print("DISCOVERING ORACLE SERVICES")
        print("=" * 60)
        
        host = args.host or 'localhost'
        port = args.port or 1521
        
        print(f"Scanning {host}:{port}...\n")
        
        from oracle_test_lib import OracleTestClient
        services = OracleTestClient.discover_services(host, port)
        
        return 0 if services else 1
    
    # Validate required arguments
    if not args.host or not args.user or not args.password:
        if not args.config:
            parser.error("--host, --user, and --password are required (or use --config)")
    
    # Test connection if requested
    if args.test_connection:
        print("\n" + "=" * 60)
        print("TESTING DATABASE CONNECTION")
        print("=" * 60)
        print(f"Host: {args.host}")
        print(f"Port: {args.port}")
        print(f"User: {args.user}")
        print(f"Service: {args.service_name}")
        print(f"TLS: {'enabled' if args.use_tls else 'disabled'}")
        print("-" * 60)
        
        db_config = create_db_config(args)
        success, message = OracleTestClient.test_connection(db_config, args.use_tls)
        
        print("\n" + message)
        
        if success:
            print("\n✓ Database connection successful!")
            print("You can now run tests with this configuration.")
            return 0
        else:
            print("\n✗ Database connection failed!")
            print("See TROUBLESHOOTING.md for help resolving connection issues.")
            return 1
    
    try:
        if args.suite:
            return run_test_suite(args)
        else:
            return run_single_test(args)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        return 130
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
