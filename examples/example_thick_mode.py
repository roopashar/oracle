#!/usr/bin/env python3
"""
Example demonstrating Oracle thick client mode

This script shows how to:
1. Enable thick client mode
2. Compare performance between thin and thick modes
3. Use thick mode with TLS connections
"""
from oracle_test_lib import init_thick_mode, OracleTestClient, LoadProfile
import sys
import os
import json
import time

# Add parent directory to path so we can import oracle_test_lib
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    script_dir = os.getcwd()
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from examples import print_test_results, load_db_config


def example_thick_mode_basic():
    """Basic thick mode example"""
    print("\n=== Example 1: Basic Thick Mode Test ===\n")

    # Load configuration
    db_config = load_db_config()

    # IMPORTANT: Initialize thick mode FIRST, before creating any clients
    thick_lib_dir = db_config.get('thick_mode_lib_dir', '/usr/local/lib')
    print(f"Initializing thick mode with lib_dir: {thick_lib_dir}")
    if init_thick_mode(thick_lib_dir):
        print("✓ Thick mode initialized successfully\n")
    else:
        print("✗ Thick mode initialization failed, will use thin mode\n")

    # Create client with thick mode
    load_profile = LoadProfile.low_load()
    client = OracleTestClient(
        db_config=db_config,
        load_profile=load_profile,
        use_tls=True,
        use_thick_mode=True  # Enable thick mode
    )

    # Run write test
    print("Running write test with thick mode...")
    write_results = client.run_write_test()
    print_test_results(write_results, "Thick Mode - Write Test")

    # Run read test
    print("Running read test with thick mode...")
    read_results = client.run_read_test()
    print_test_results(read_results, "Thick Mode - Read Test")


def example_compare_thin_vs_thick():
    """Compare performance between thin and thick modes

    NOTE: This example requires TWO SEPARATE Python sessions:
    1. First session: Run with thin mode only
    2. Second session: Run with thick mode only

    You cannot switch between thin and thick mode in the same Python process.
    """
    print("\n=== Example 2: Thin vs Thick Mode Performance Comparison ===\n")
    print("WARNING: This example should be run in TWO SEPARATE sessions:")
    print("  Session 1: Set use_thick=False below")
    print("  Session 2: Set use_thick=True below")
    print()

    # CONFIGURE THIS: Set to False for thin mode, True for thick mode
    use_thick = False  # Change this and restart script to test thick mode

    # Load configuration
    db_config = load_db_config()

    # Initialize thick mode if requested (MUST be done before any connections)
    if use_thick:
        thick_lib_dir = db_config.get('thick_mode_lib_dir', '/usr/local/lib')
        print(f"Initializing thick mode with lib_dir: {thick_lib_dir}")
        if init_thick_mode(thick_lib_dir):
            print("✓ Thick mode initialized successfully\n")
        else:
            print("✗ Thick mode initialization failed\n")
            return

    # Create load profile for comparison
    load_profile = LoadProfile.custom(
        name="Performance Test",
        concurrent_connections=10,
        operations_per_second=50,
        data_size_kb=100,
        think_time_ms=0,
        duration_seconds=60
    )

    print("Configuration:")
    print(f"  Connections: {load_profile.concurrent_connections}")
    print(f"  Operations/sec: {load_profile.operations_per_second}")
    print(f"  Data size: {load_profile.data_size_kb} KB")
    print(f"  Duration: {load_profile.duration_seconds} seconds")
    print(f"  Mode: {'THICK' if use_thick else 'THIN'}")
    print()

    # Test with selected mode
    mode_name = "THICK" if use_thick else "THIN"
    print(f"Testing with {mode_name} mode...")
    print("-" * 70)
    client = OracleTestClient(
        db_config=db_config,
        load_profile=load_profile,
        use_tls=True,
        use_thick_mode=use_thick
    )

    start = time.time()
    results = client.run_write_test()
    duration = time.time() - start
    summary = results.get_summary()

    print(f"\n{mode_name} mode completed in {duration:.2f} seconds")
    print(f"  Avg latency: {summary['avg_duration_ms']:.2f}ms")
    print(f"  P95 latency: {summary['p95_duration_ms']:.2f}ms")
    print(f"  Throughput: {summary['avg_throughput_mbps']:.2f} MB/s")

    print("\n" + "=" * 70)
    print("Test completed!")
    print("=" * 70)
    print(f"\nTo compare with {'thin' if use_thick else 'thick'} mode:")
    print(f"1. Set use_thick = {not use_thick} in this script")
    print(f"2. Restart Python and run again")
    print("\nNote: You cannot switch modes in the same Python session")
    print("=" * 70)


def example_thick_mode_high_performance():
    """High performance test with thick mode"""
    print("\n=== Example 3: High Performance Test with Thick Mode ===\n")

    # Load configuration
    db_config = load_db_config()

    # IMPORTANT: Initialize thick mode FIRST
    thick_lib_dir = db_config.get('thick_mode_lib_dir', '/usr/local/lib')
    print(f"Initializing thick mode with lib_dir: {thick_lib_dir}")
    if init_thick_mode(thick_lib_dir):
        print("✓ Thick mode initialized successfully\n")
    else:
        print("✗ Thick mode initialization failed, cannot continue\n")
        return

    # High performance profile
    load_profile = LoadProfile.custom(
        name="High Performance (Thick Mode)",
        concurrent_connections=25,
        operations_per_second=200,
        data_size_kb=256,
        think_time_ms=0,
        duration_seconds=120
    )

    print("High performance configuration with thick mode:")
    print(f"  Connections: {load_profile.concurrent_connections}")
    print(f"  Operations/sec: {load_profile.operations_per_second}")
    print(f"  Data size: {load_profile.data_size_kb} KB")
    print(f"  Duration: {load_profile.duration_seconds} seconds")
    print(f"  Expected operations: ~{load_profile.operations_per_second * load_profile.duration_seconds:,}")
    print()

    client = OracleTestClient(
        db_config=db_config,
        load_profile=load_profile,
        use_tls=True,
        use_thick_mode=True
    )

    # Run mixed workload
    print("Running high-performance mixed test (70% reads, 30% writes)...")
    results = client.run_mixed_test(read_write_ratio=0.7)

    print_test_results(results, "High Performance Thick Mode Test")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Oracle Thick Client Mode Examples")
    print("=" * 70)
    print("\nThick mode provides better performance for high-throughput operations")
    print("Requires: Oracle Instant Client installed")
    print()

    # Uncomment the examples you want to run:

    # Example 1: Basic thick mode usage
    example_thick_mode_basic()

    # Example 2: Compare thin vs thick performance
    # example_compare_thin_vs_thick()

    # Example 3: High performance with thick mode
    # example_thick_mode_high_performance()

    print("\n" + "=" * 70)
    print("Examples completed!")
    print("=" * 70)
