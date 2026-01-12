#!/usr/bin/env python3
"""
Example script demonstrating comprehensive query testing with multiple column types

This script shows how to:
1. Create a comprehensive table with multiple column types
2. Populate it with a large number of rows
3. Run various query patterns and measure performance
"""

import sys
import os
import json
import logging
from datetime import datetime

# Add parent directory to path so we can import oracle_test_lib
# This works whether running from examples/ directory or project root
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    script_dir = os.getcwd()
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from oracle_test_lib import OracleTestClient, OracleTestConnection, LoadProfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_file: str = '../db_config.json') -> dict:
    """Load database configuration from JSON file"""
    import os
    # Try parent directory first, then current directory
    if not os.path.exists(config_file):
        config_file = 'db_config.json'
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            logger.info(f"Loaded configuration from {config_file}")
            return config
    except FileNotFoundError:
        logger.error(f"Configuration file {config_file} not found")
        logger.error(f"Please create {config_file} with your database credentials in the project root")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON configuration: {e}")
        raise


def main():
    """Main execution function"""

    # Load database configuration from JSON file
    logger.info("Loading database configuration...")
    db_config = load_config('../db_config.json')

    # Create a simple load profile for testing
    load_profile = LoadProfile(
        name="comprehensive_test",
        concurrent_connections=1,
        operations_per_second=10,
        data_size_kb=1,
        think_time_ms=0,
        duration_seconds=60
    )

    # Initialize the test client (this will create tables)
    logger.info("Initializing test client and creating tables...")
    client = OracleTestClient(
        db_config=db_config,
        load_profile=load_profile,
        use_tls=True,
        setup_tables=True  # This creates all tables including test_comprehensive
    )

    # Create a connection for testing
    logger.info("Creating test connection...")
    conn = OracleTestConnection("test_conn", db_config, use_tls=True)
    if not conn.connect():
        logger.error("Failed to connect to database")
        return

    try:
        # Step 1: Populate the comprehensive table with test data
        logger.info("\n" + "="*60)
        logger.info("STEP 1: Populating test_comprehensive table")
        logger.info("="*60)

        num_rows = 10000  # Start with 10K rows, increase as needed
        batch_size = 1000

        logger.info(f"Inserting {num_rows} rows in batches of {batch_size}...")
        population_stats = client.populate_comprehensive_data(
            num_rows=num_rows,
            batch_size=batch_size,
            connection=conn
        )

        logger.info(f"Population complete!")
        logger.info(f"  Rows inserted: {population_stats['rows_inserted']}")
        logger.info(f"  Time taken: {population_stats['elapsed_time_sec']:.2f} seconds")
        logger.info(f"  Rate: {population_stats['rows_per_second']:.0f} rows/second")

        # Step 2: Run comprehensive query tests
        logger.info("\n" + "="*60)
        logger.info("STEP 2: Running comprehensive query tests")
        logger.info("="*60)

        # Test all query types
        query_types = [
            'select_all',
            'where_indexed',
            'where_non_indexed',
            'aggregate',
            'group_by',
            'order_by',
            'complex'
        ]

        for query_type in query_types:
            logger.info(f"\nTesting query type: {query_type}")
            results = client.test_comprehensive_queries(conn, query_type)

            # Print results summary
            for query_name, result in results.items():
                if result['success']:
                    logger.info(f"  {query_name}: {result['rows_returned']} rows in {result['elapsed_time_ms']:.2f}ms")
                else:
                    logger.error(f"  {query_name}: FAILED - {result['error']}")

        # Step 3: Test performance of specific queries
        logger.info("\n" + "="*60)
        logger.info("STEP 3: Testing query performance (10 iterations)")
        logger.info("="*60)

        test_queries = [
            {
                'name': 'Indexed WHERE on status',
                'query': "SELECT * FROM test_comprehensive WHERE status = 'active' AND ROWNUM <= 100"
            },
            {
                'name': 'Price range query',
                'query': "SELECT * FROM test_comprehensive WHERE price BETWEEN 100 AND 500 AND ROWNUM <= 100"
            },
            {
                'name': 'Complex multi-condition',
                'query': """
                    SELECT *
                    FROM test_comprehensive
                    WHERE status = 'active'
                      AND category IN ('electronics', 'clothing')
                      AND price > 50
                      AND is_active = 1
                    FETCH FIRST 50 ROWS ONLY
                """
            },
            {
                'name': 'Aggregate GROUP BY',
                'query': "SELECT category, COUNT(*) as count, AVG(price) as avg_price FROM test_comprehensive GROUP BY category"
            }
        ]

        for test_query in test_queries:
            logger.info(f"\nTesting: {test_query['name']}")
            perf_stats = client.test_query_performance(
                connection=conn,
                query=test_query['query'],
                iterations=10
            )

            if perf_stats.get('successful_iterations', 0) > 0:
                logger.info(f"  Average time: {perf_stats['avg_time_ms']:.2f}ms")
                logger.info(f"  Min time: {perf_stats['min_time_ms']:.2f}ms")
                logger.info(f"  Max time: {perf_stats['max_time_ms']:.2f}ms")
                logger.info(f"  Avg rows: {perf_stats['avg_rows_returned']:.0f}")
            else:
                logger.error(f"  All iterations failed!")

        # Step 4: Test with prepared statements
        logger.info("\n" + "="*60)
        logger.info("STEP 4: Testing prepared statements")
        logger.info("="*60)

        # Test prepared statement for status query
        logger.info("\nTesting prepared statement: select_by_status")
        start_time = datetime.now()
        conn.cursor.execute(
            client._prepared_statements['select_by_status'],
            {'status': 'active', 'limit': 100}
        )
        rows = conn.cursor.fetchall()
        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        logger.info(f"  Result: {len(rows)} rows in {elapsed:.2f}ms")

        # Test prepared statement for category query
        logger.info("\nTesting prepared statement: select_by_category")
        start_time = datetime.now()
        conn.cursor.execute(
            client._prepared_statements['select_by_category'],
            {'category': 'electronics', 'limit': 100}
        )
        rows = conn.cursor.fetchall()
        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        logger.info(f"  Result: {len(rows)} rows in {elapsed:.2f}ms")

        # Test prepared statement for price range
        logger.info("\nTesting prepared statement: select_by_price_range")
        start_time = datetime.now()
        conn.cursor.execute(
            client._prepared_statements['select_by_price_range'],
            {'min_price': 100, 'max_price': 500, 'limit': 100}
        )
        rows = conn.cursor.fetchall()
        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        logger.info(f"  Result: {len(rows)} rows in {elapsed:.2f}ms")

        # Step 5: Get table statistics
        logger.info("\n" + "="*60)
        logger.info("STEP 5: Table statistics")
        logger.info("="*60)

        # Count rows
        conn.cursor.execute("SELECT COUNT(*) FROM test_comprehensive")
        total_rows = conn.cursor.fetchone()[0]
        logger.info(f"Total rows in test_comprehensive: {total_rows}")

        # Get status distribution
        conn.cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM test_comprehensive
            GROUP BY status
            ORDER BY count DESC
        """)
        logger.info("\nStatus distribution:")
        for row in conn.cursor.fetchall():
            logger.info(f"  {row[0]}: {row[1]} rows")

        # Get category distribution
        conn.cursor.execute("""
            SELECT category, COUNT(*) as count, AVG(price) as avg_price
            FROM test_comprehensive
            GROUP BY category
            ORDER BY count DESC
        """)
        logger.info("\nCategory distribution:")
        for row in conn.cursor.fetchall():
            logger.info(f"  {row[0]}: {row[1]} rows, avg price: ${row[2]:.2f}")

        logger.info("\n" + "="*60)
        logger.info("TEST COMPLETE!")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"Error during testing: {e}", exc_info=True)

    finally:
        # Clean up
        logger.info("\nCleaning up connections...")
        conn.disconnect()


if __name__ == "__main__":
    main()
