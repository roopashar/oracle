"""
Example usage of the Oracle Test Library

This script demonstrates various ways to use the library for testing Oracle clients.
"""

import sys
import os
import json

# Add parent directory to path so we can import oracle_test_lib
# This works whether running from examples/ directory or project root
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    script_dir = os.getcwd()
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from oracle_test_lib import (
    OracleTestClient,
    OracleTestSuite,
    LoadProfile
)


def print_test_results(results, test_name: str):
    """Print detailed test results with separate read/write metrics"""
    summary = results.get_summary()

    print(f"\n{'='*70}")
    print(f"{test_name} - Results Summary")
    print(f"{'='*70}")
    print(f"Load Profile: {summary['load_profile']}")
    print(f"\nOperations:")
    print(f"  Total Operations:     {summary['total_operations']:,}")
    print(f"  Successful:           {summary['successful_operations']:,}")
    print(f"  Failed:               {summary['failed_operations']:,}")
    print(f"  Success Rate:         {summary['success_rate']:.2f}%")

    # Display read/write breakdown if available
    if 'read_operations' in summary or 'write_operations' in summary:
        print(f"\nOperation Breakdown:")
        if 'read_operations' in summary:
            print(f"  Read Operations:      {summary['read_operations']:,}")
        if 'write_operations' in summary:
            print(f"  Write Operations:     {summary['write_operations']:,}")

    print(f"\nData Transfer:")
    print(f"  Total Data:           {summary['total_data_transferred_mb']:.2f} MB")
    if 'avg_throughput_mbps' in summary:
        print(f"  Avg Throughput:       {summary['avg_throughput_mbps']:.2f} MB/s")

    # Display read/write data breakdown
    if 'read_data_mb' in summary:
        print(f"  Read Data:            {summary['read_data_mb']:.2f} MB")
        if 'read_avg_throughput_mbps' in summary:
            print(f"  Read Throughput:      {summary['read_avg_throughput_mbps']:.2f} MB/s")
    if 'write_data_mb' in summary:
        print(f"  Write Data:           {summary['write_data_mb']:.2f} MB")
        if 'write_avg_throughput_mbps' in summary:
            print(f"  Write Throughput:     {summary['write_avg_throughput_mbps']:.2f} MB/s")

    print(f"\nPerformance Metrics (Overall):")
    if 'avg_duration_ms' in summary:
        print(f"  Average Duration:     {summary['avg_duration_ms']:.2f} ms")
    if 'min_duration_ms' in summary:
        print(f"  Min Duration:         {summary['min_duration_ms']:.2f} ms")
    if 'max_duration_ms' in summary:
        print(f"  Max Duration:         {summary['max_duration_ms']:.2f} ms")
    if 'p50_duration_ms' in summary:
        print(f"  P50 (Median):         {summary['p50_duration_ms']:.2f} ms")
    if 'p95_duration_ms' in summary:
        print(f"  P95 Latency:          {summary['p95_duration_ms']:.2f} ms")
    if 'p99_duration_ms' in summary:
        print(f"  P99 Latency:          {summary['p99_duration_ms']:.2f} ms")

    # Display separate read metrics
    if 'read_avg_duration_ms' in summary:
        print(f"\nRead Performance:")
        print(f"  Average Duration:     {summary['read_avg_duration_ms']:.2f} ms")
        print(f"  Min Duration:         {summary['read_min_duration_ms']:.2f} ms")
        print(f"  Max Duration:         {summary['read_max_duration_ms']:.2f} ms")
        print(f"  P50 (Median):         {summary['read_p50_duration_ms']:.2f} ms")
        print(f"  P95 Latency:          {summary['read_p95_duration_ms']:.2f} ms")
        print(f"  P99 Latency:          {summary['read_p99_duration_ms']:.2f} ms")

    # Display separate write metrics
    if 'write_avg_duration_ms' in summary:
        print(f"\nWrite Performance:")
        print(f"  Average Duration:     {summary['write_avg_duration_ms']:.2f} ms")
        print(f"  Min Duration:         {summary['write_min_duration_ms']:.2f} ms")
        print(f"  Max Duration:         {summary['write_max_duration_ms']:.2f} ms")
        print(f"  P50 (Median):         {summary['write_p50_duration_ms']:.2f} ms")
        print(f"  P95 Latency:          {summary['write_p95_duration_ms']:.2f} ms")
        print(f"  P99 Latency:          {summary['write_p99_duration_ms']:.2f} ms")

    if 'total_duration_seconds' in summary:
        print(f"\nTest Duration:          {summary['total_duration_seconds']:.2f} seconds")

    print(f"{'='*70}\n")


def load_db_config(config_file: str = '../db_config.json') -> dict:
    """Load database configuration from JSON file"""
    import os
    # Try current directory first, then parent directory
    if not os.path.exists(config_file):
        config_file = 'db_config.json'
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Configuration file {config_file} not found")
        print("Using default inline configuration instead")
        # Fallback to inline config
        return {
            'host': 'localhost',
            'port': 1521,
            'user': 'system',
            'password': 'TestPassword123',
            'service_name': 'FREEPDB1',
            'wallet_location': '/Users/rsharma/Downloads/oracle/docker-tls-setup/wallet',
            'wallet_password': 'WalletPass123',
        }
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON configuration: {e}")
        raise


# Example 0: Test database connection
def example_test_connection():
    """Test database connectivity before running tests"""
    print("\n=== Example 0: Test Database Connection ===\n")

    # Load database configuration from JSON file
    db_config = load_db_config()

    # Test connection without creating tables
    print("Testing database connection...")
    success, message = OracleTestClient.test_connection(db_config, use_tls=True)
    
    print(message)
    
    if success:
        print("\n✓ Connection successful! You can now run tests.")
        return True
    else:
        print("\n✗ Connection failed. Please fix the issues above.")
        print("See TROUBLESHOOTING.md for detailed help.")
        return False


# Example 1: Simple low load test
def example_simple_test():
    """Run a simple low-load test"""
    print("\n=== Example 1: Simple Low Load Test ===\n")
    
    # Configure database connection
    # Load database configuration from JSON file
    db_config = load_db_config()
    
    # Create test client with low load profile
    load_profile = LoadProfile.low_load()
    client = OracleTestClient(
        db_config=db_config,
        load_profile=load_profile,
        use_tls=True
    )
    
    # Run write test
    print("Running write test...")
    write_results = client.run_write_test()
    print_test_results(write_results, "Write Test")

    # Run read test
    print("Running read test...")
    read_results = client.run_read_test()
    print_test_results(read_results, "Read Test")


# Example 2: Custom load profile
def example_custom_load(concurrent_connections=None,
        operations_per_second=None,
        data_size_kb=None,
        think_time_ms=25,
        duration_seconds=None):
    """Create and use a custom load profile"""
    print("\n=== Example 2: Custom Load Profile ===\n")
    
    # Load database configuration from JSON file
    db_config = load_db_config()
    
    # Create custom load profile
    custom_load = LoadProfile.custom(
        name="Medium Load",
        concurrent_connections=concurrent_connections,
        operations_per_second=operations_per_second,
        data_size_kb=data_size_kb,
        think_time_ms=think_time_ms,
        duration_seconds=duration_seconds
    )
    
    # Run test with custom profile
    client = OracleTestClient(
        db_config=db_config,
        load_profile=custom_load,
        use_tls=False  # Disable TLS for this test
    )
    
    print("Running mixed test (70% reads, 30% writes)...")
    results = client.run_mixed_test(read_write_ratio=0.7)
    print_test_results(results, "Custom Load - Mixed Test")


# Example 3: High load stress test
def example_high_load_test():
    """Run high load stress test"""
    print("\n=== Example 3: High Load Stress Test ===\n")

    # Load database configuration from JSON file
    db_config = load_db_config()

    # Use a medium load profile optimized for cloud/RDS environments
    # For full high load, uncomment: high_load = LoadProfile.high_load()
    high_load = LoadProfile.custom(
        name="Medium Load (Cloud Optimized)",
        concurrent_connections=10,    # Reduced from 50 for RDS
        operations_per_second=50,     # Reduced from 500 for realistic throughput
        data_size_kb=100,             # Reduced from 1024 (100KB instead of 1MB)
        think_time_ms=0,
        duration_seconds=120          # Reduced from 300 (2 minutes)
    )
    print(f"Load Profile: {high_load.name}")
    print(f"  Connections: {high_load.concurrent_connections}")
    print(f"  Target ops/sec: {high_load.operations_per_second}")
    print(f"  Data size: {high_load.data_size_kb} KB")
    print(f"  Duration: {high_load.duration_seconds} seconds")
    print(f"  Expected records: ~{high_load.operations_per_second * high_load.duration_seconds:,}")
    print()

    client = OracleTestClient(
        db_config=db_config,
        load_profile=high_load,
        use_tls=True
    )

    # First, run write test to populate data
    print("Step 1: Populating data with write test...")
    write_results = client.run_write_test()
    print_test_results(write_results, "High Load - Write Test")

    # Now run read test with populated data
    print("Step 2: Running high load read test...")
    read_results = client.run_read_test()
    print_test_results(read_results, "High Load - Read Test")


# Example 4: Testing TLS connections specifically
def example_tls_test():
    """Test multiple concurrent TLS connections"""
    print("\n=== Example 4: Concurrent TLS Connection Test ===\n")
    # Load database configuration from JSON file
    db_config = load_db_config()
    
    # Focus on connection concurrency
    tls_load = LoadProfile.custom(
        name="TLS Connection Test",
        concurrent_connections=100,  # Many concurrent TLS connections
        operations_per_second=50,
        data_size_kb=50,
        think_time_ms=10,
        duration_seconds=120
    )
    
    client = OracleTestClient(
        db_config=db_config,
        load_profile=tls_load,
        use_tls=True
    )
    
    results = client.run_mixed_test(read_write_ratio=0.5)
    summary = results.get_summary()
    
    print(f"TLS connection test with {tls_load.concurrent_connections} connections:")
    print(f"  Total operations: {summary['total_operations']}")
    print(f"  Failed operations: {summary['failed_operations']}")
    print(f"  Success rate: {summary['success_rate']:.2f}%")


# Example 5: Large data transfer test
def example_large_data_test():
    """Test with very large data transfers"""
    print("\n=== Example 5: Large Data Transfer Test ===\n")
    
    # Load database configuration from JSON file
    db_config = load_db_config()
    
    # Profile optimized for large data
    large_data_load = LoadProfile.custom(
        name="Large Data Test",
        concurrent_connections=5,
        operations_per_second=10,
        data_size_kb=5120,  # 5 MB per operation
        think_time_ms=0,
        duration_seconds=60
    )
    
    client = OracleTestClient(
        db_config=db_config,
        load_profile=large_data_load,
        use_tls=True
    )
    
    # Test large writes
    print("Testing large writes...")
    write_results = client.run_write_test()
    write_summary = write_results.get_summary()
    
    print(f"Large write test:")
    print(f"  Total data written: {write_summary['total_data_transferred_mb']:.2f} MB")
    print(f"  Average throughput: {write_summary.get('avg_throughput_mbps', 0):.2f} MB/s")
    
    # Test large reads
    client2 = OracleTestClient(
        db_config=db_config,
        load_profile=large_data_load,
        use_tls=True,
        setup_tables=False
    )
    
    print("\nTesting large reads...")
    read_results = client2.run_read_test()
    read_summary = read_results.get_summary()
    
    print(f"Large read test:")
    print(f"  Total data read: {read_summary['total_data_transferred_mb']:.2f} MB")
    print(f"  Average throughput: {read_summary.get('avg_throughput_mbps', 0):.2f} MB/s")


# Example 6: Full test suite
def example_full_suite():
    """Run complete test suite"""
    print("\n=== Example 6: Full Test Suite ===\n")
    
    # Load database configuration from JSON file
    db_config = load_db_config()
    
    # Create test suite
    suite = OracleTestSuite(db_config=db_config, use_tls=True)
    
    # Run all tests (including high load)
    results = suite.run_all_tests(include_high_load=True)
    
    # Print comprehensive summary
    suite.print_summary()
    
    # Export results to file
    import json
    with open('test_results.json', 'w') as f:
        summaries = [r.get_summary() for r in results]
        json.dump(summaries, f, indent=2)
    
    print("\nResults exported to test_results.json")


# Example 7: Prepared statements performance comparison
def example_prepared_statements():
    """Compare prepared statements vs direct SQL"""
    print("\n=== Example 7: Prepared Statements Performance ===\n")
    
    # Load database configuration from JSON file
    db_config = load_db_config()
    
    # Test profile
    profile = LoadProfile.custom(
        name="Prepared Statement Test",
        concurrent_connections=5,
        operations_per_second=50,
        data_size_kb=100,
        duration_seconds=60
    )
    
    # Client with prepared statements (default)
    client = OracleTestClient(
        db_config=db_config,
        load_profile=profile,
        use_tls=False,
        use_prepared_statements=True  # Explicitly enable
    )
    
    print("Testing with prepared statements enabled...")
    results_prepared = client.run_write_test()
    summary_prepared = results_prepared.get_summary()
    
    # Client without prepared statements
    client_direct = OracleTestClient(
        db_config=db_config,
        load_profile=profile,
        use_tls=False,
        use_prepared_statements=False,  # Disable
        setup_tables=False
    )
    
    print("Testing with direct SQL...")
    results_direct = client_direct.run_write_test()
    summary_direct = results_direct.get_summary()
    
    # Compare results
    print("\nPerformance Comparison:")
    print(f"  Prepared Statements:")
    print(f"    Average latency: {summary_prepared.get('avg_duration_ms', 0):.2f} ms")
    print(f"    P95 latency: {summary_prepared.get('p95_duration_ms', 0):.2f} ms")
    
    print(f"  Direct SQL:")
    print(f"    Average latency: {summary_direct.get('avg_duration_ms', 0):.2f} ms")
    print(f"    P95 latency: {summary_direct.get('p95_duration_ms', 0):.2f} ms")
    
    # Calculate improvement
    avg_prep = summary_prepared.get('avg_duration_ms', 0)
    avg_direct = summary_direct.get('avg_duration_ms', 0)
    if avg_direct > 0:
        improvement = ((avg_direct - avg_prep) / avg_direct) * 100
        print(f"\nPrepared statements are {improvement:.1f}% faster!")


# Example 8: Batch operations
def example_batch_operations():
    """Test batch write operations"""
    print("\n=== Example 8: Batch Operations ===\n")
    
    # Load database configuration from JSON file
    db_config = load_db_config()
    
    from oracle_test_lib import OracleTestConnection
    
    profile = LoadProfile.custom(
        name="Batch Test",
        concurrent_connections=1,
        operations_per_second=10,
        data_size_kb=50,
        duration_seconds=30
    )
    
    client = OracleTestClient(
        db_config=db_config,
        load_profile=profile,
        use_tls=False,
        use_prepared_statements=True
    )
    
    # Test different batch sizes
    batch_sizes = [10, 50, 100, 500]
    
    print("Testing batch operations with different sizes...")
    for batch_size in batch_sizes:
        conn = OracleTestConnection(f"batch_{batch_size}", db_config, False)
        if conn.connect():
            metric = client.test_batch_write(conn, batch_size, 50)
            conn.disconnect()
            
            print(f"\nBatch size {batch_size}:")
            print(f"  Duration: {metric.duration_ms:.2f} ms")
            print(f"  Throughput: {metric.throughput_mbps:.2f} MB/s")
            print(f"  Records/sec: {batch_size / (metric.duration_ms / 1000):.1f}")


# Example 9: Using the comparison utility
def example_auto_comparison():
    """Use built-in comparison method"""
    print("\n=== Example 9: Automatic Comparison ===\n")
    
    # Load database configuration from JSON file
    db_config = load_db_config()
    
    profile = LoadProfile.low_load()
    
    client = OracleTestClient(
        db_config=db_config,
        load_profile=profile,
        use_tls=False
    )
    
    # Run automatic comparison
    results = client.compare_prepared_vs_direct(
        num_operations=100,
        data_size_kb=100
    )
    
    print("\nComparison Results:")
    for method, result in results.items():
        summary = result.get_summary()
        print(f"\n{method.upper()}:")
        print(f"  Avg latency: {summary.get('avg_duration_ms', 0):.2f} ms")
        print(f"  P95 latency: {summary.get('p95_duration_ms', 0):.2f} ms")
        print(f"  Success rate: {summary['success_rate']:.2f}%")


# Example 10: Monitoring during execution
def example_with_monitoring():
    """Run test with real-time monitoring"""
    print("\n=== Example 7: Test with Monitoring ===\n")
    
    import threading
    import time
    
    # Load database configuration from JSON file
    db_config = load_db_config()
    
    load_profile = LoadProfile.custom(
        name="Monitored Test",
        concurrent_connections=20,
        operations_per_second=100,
        data_size_kb=200,
        think_time_ms=0,
        duration_seconds=60
    )
    
    client = OracleTestClient(
        db_config=db_config,
        load_profile=load_profile,
        use_tls=True
    )
    
    # Monitor function
    def monitor():
        while not stop_monitoring.is_set():
            time.sleep(5)
            current_metrics = len(client.results.metrics)
            successful = sum(1 for m in client.results.metrics if m.success)
            print(f"Progress: {current_metrics} operations, {successful} successful")
    
    # Start monitoring thread
    stop_monitoring = threading.Event()
    monitor_thread = threading.Thread(target=monitor)
    monitor_thread.start()
    
    try:
        # Run test
        results = client.run_mixed_test()
    finally:
        # Stop monitoring
        stop_monitoring.set()
        monitor_thread.join()
    
    # Print final summary
    summary = results.get_summary()
    print(f"\nTest completed:")
    print(f"  Total operations: {summary['total_operations']}")
    print(f"  Success rate: {summary['success_rate']:.2f}%")


if __name__ == "__main__":
    # Run examples
    # Uncomment the examples you want to run
    
    # ALWAYS test connection first!
    # from oracle_test_lib import OracleTestClient, LoadProfile
    #
    # # Step 1: Discover services
    # services = OracleTestClient.discover_services('localhost', 1521)
    # print(f"Found: {services}")

    #example_test_connection()
    
    # Then uncomment other examples as needed:
    #example_simple_test()
    example_custom_load(concurrent_connections=10,
        operations_per_second=100,
        data_size_kb=500,
        think_time_ms=25,
        duration_seconds=180)
    #example_high_load_test()
    #example_tls_test()
    # example_large_data_test()
    # example_full_suite()
    #example_prepared_statements()
    # example_batch_operations()
    # example_auto_comparison()
    # example_with_monitoring()
    
    #print("\nUncomment the examples you want to run in the script.")
    #print("Make sure to update the db_config with your actual database credentials.")
