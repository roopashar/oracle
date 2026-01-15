"""
Oracle Client Testing Library

A comprehensive testing library for Oracle database clients with support for:
- Large write operations
- Large read operations
- Multiple concurrent TLS connections
- Configurable low/high load patterns
- Performance metrics and monitoring
- Thick client mode with Oracle Instant Client
"""

import oracledb
import threading
import time
import random
import string
import socket
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Callable, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import statistics
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global flag to track if thick mode has been initialized
_thick_mode_initialized = False


def init_thick_mode(lib_dir: Optional[str] = None) -> bool:
    """
    Initialize Oracle thick client mode.

    IMPORTANT: This must be called BEFORE creating any Oracle connections.
    Once a thin mode connection is created, thick mode cannot be enabled.

    Args:
        lib_dir: Optional path to Oracle Instant Client directory

    Returns:
        True if thick mode was successfully initialized, False otherwise

    Example:
        >>> from oracle_test_lib import init_thick_mode
        >>> init_thick_mode('/usr/local/lib')  # Call before creating any clients
        >>> # Now create clients with use_thick_mode=True
    """
    global _thick_mode_initialized

    if _thick_mode_initialized:
        logger.info("Thick mode already initialized")
        return True

    try:
        if lib_dir:
            logger.info(f"Initializing thick mode with lib_dir: {lib_dir}")
            oracledb.init_oracle_client(lib_dir=lib_dir)
        else:
            logger.info("Initializing thick mode with default Oracle Client location")
            oracledb.init_oracle_client()

        _thick_mode_initialized = True
        logger.info("Thick mode initialized successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize thick mode: {e}")
        return False


@dataclass
class LoadProfile:
    """Defines load characteristics for testing"""
    name: str
    concurrent_connections: int
    operations_per_second: int
    data_size_kb: int
    think_time_ms: int
    duration_seconds: int
    
    @classmethod
    def low_load(cls):
        """Predefined low load profile"""
        return cls(
            name="Low Load",
            concurrent_connections=2,
            operations_per_second=10,
            data_size_kb=10,
            think_time_ms=100,
            duration_seconds=60
        )
    
    @classmethod
    def high_load(cls):
        """Predefined high load profile"""
        return cls(
            name="High Load",
            concurrent_connections=50,
            operations_per_second=500,
            data_size_kb=1024,
            think_time_ms=0,
            duration_seconds=300
        )
    
    @classmethod
    def custom(cls, name: str, **kwargs):
        """Create custom load profile"""
        defaults = {
            'concurrent_connections': 10,
            'operations_per_second': 50,
            'data_size_kb': 100,
            'think_time_ms': 50,
            'duration_seconds': 120
        }
        defaults.update(kwargs)
        return cls(name=name, **defaults)


@dataclass
class TestMetrics:
    """Stores performance metrics for test operations"""
    operation_type: str
    start_time: float
    end_time: float
    success: bool
    error_message: Optional[str] = None
    data_size_bytes: int = 0
    connection_id: Optional[str] = None
    
    @property
    def duration_ms(self) -> float:
        """Calculate operation duration in milliseconds"""
        return (self.end_time - self.start_time) * 1000
    
    @property
    def throughput_mbps(self) -> float:
        """Calculate throughput in MB/s"""
        if self.duration_ms == 0:
            return 0
        mb = self.data_size_bytes / (1024 * 1024)
        seconds = self.duration_ms / 1000
        return mb / seconds if seconds > 0 else 0


@dataclass
class TestResults:
    """Aggregated test results and statistics"""
    load_profile: LoadProfile
    metrics: List[TestMetrics] = field(default_factory=list)
    
    def add_metric(self, metric: TestMetrics):
        """Add a metric to results"""
        self.metrics.append(metric)
    
    def get_summary(self) -> Dict[str, Any]:
        """Generate summary statistics"""
        if not self.metrics:
            return {"error": "No metrics collected"}

        successful = [m for m in self.metrics if m.success]
        failed = [m for m in self.metrics if not m.success]

        # Separate read and write operations
        read_metrics = [m for m in successful if 'read' in m.operation_type.lower()]
        write_metrics = [m for m in successful if 'write' in m.operation_type.lower()]

        durations = [m.duration_ms for m in successful]
        throughputs = [m.throughput_mbps for m in successful if m.throughput_mbps > 0]

        summary = {
            "load_profile": self.load_profile.name,
            "total_operations": len(self.metrics),
            "successful_operations": len(successful),
            "failed_operations": len(failed),
            "success_rate": len(successful) / len(self.metrics) * 100 if self.metrics else 0,
            "total_data_transferred_mb": sum(m.data_size_bytes for m in successful) / (1024 * 1024),
        }

        if durations:
            summary.update({
                "avg_duration_ms": statistics.mean(durations),
                "min_duration_ms": min(durations),
                "max_duration_ms": max(durations),
                "median_duration_ms": statistics.median(durations),
                "p50_duration_ms": statistics.median(durations),
                "p95_duration_ms": statistics.quantiles(durations, n=20)[18] if len(durations) > 1 else durations[0],
                "p99_duration_ms": statistics.quantiles(durations, n=100)[98] if len(durations) > 1 else durations[0],
            })

        if throughputs:
            summary.update({
                "avg_throughput_mbps": statistics.mean(throughputs),
                "min_throughput_mbps": min(throughputs),
                "max_throughput_mbps": max(throughputs),
            })

        # Add separate read metrics
        if read_metrics:
            read_durations = [m.duration_ms for m in read_metrics]
            read_throughputs = [m.throughput_mbps for m in read_metrics if m.throughput_mbps > 0]
            summary.update({
                "read_operations": len(read_metrics),
                "read_data_mb": sum(m.data_size_bytes for m in read_metrics) / (1024 * 1024),
                "read_avg_duration_ms": statistics.mean(read_durations),
                "read_min_duration_ms": min(read_durations),
                "read_max_duration_ms": max(read_durations),
                "read_p50_duration_ms": statistics.median(read_durations),
                "read_p95_duration_ms": statistics.quantiles(read_durations, n=20)[18] if len(read_durations) > 1 else read_durations[0],
                "read_p99_duration_ms": statistics.quantiles(read_durations, n=100)[98] if len(read_durations) > 1 else read_durations[0],
            })
            if read_throughputs:
                summary["read_avg_throughput_mbps"] = statistics.mean(read_throughputs)

        # Add separate write metrics
        if write_metrics:
            write_durations = [m.duration_ms for m in write_metrics]
            write_throughputs = [m.throughput_mbps for m in write_metrics if m.throughput_mbps > 0]
            summary.update({
                "write_operations": len(write_metrics),
                "write_data_mb": sum(m.data_size_bytes for m in write_metrics) / (1024 * 1024),
                "write_avg_duration_ms": statistics.mean(write_durations),
                "write_min_duration_ms": min(write_durations),
                "write_max_duration_ms": max(write_durations),
                "write_p50_duration_ms": statistics.median(write_durations),
                "write_p95_duration_ms": statistics.quantiles(write_durations, n=20)[18] if len(write_durations) > 1 else write_durations[0],
                "write_p99_duration_ms": statistics.quantiles(write_durations, n=100)[98] if len(write_durations) > 1 else write_durations[0],
            })
            if write_throughputs:
                summary["write_avg_throughput_mbps"] = statistics.mean(write_throughputs)

        return summary


class OracleTestConnection:
    """Represents a single Oracle database connection for testing"""

    def __init__(self, connection_id: str, config: Dict[str, Any], use_tls: bool = True, use_thick_mode: bool = False):
        self.connection_id = connection_id
        self.config = config
        self.use_tls = use_tls
        self.use_thick_mode = use_thick_mode
        self.connection: Optional[oracledb.Connection] = None
        self.cursor: Optional[oracledb.Cursor] = None
        
    def connect(self) -> bool:
        """Establish connection to Oracle database"""
        try:
            # Initialize thick mode if requested (only needs to be done once globally)
            if self.use_thick_mode:
                global _thick_mode_initialized
                if not _thick_mode_initialized:
                    try:
                        # Get lib_dir from config or use default
                        lib_dir = self.config.get('thick_mode_lib_dir')
                        if lib_dir:
                            logger.info(f"Initializing thick mode with lib_dir: {lib_dir}")
                            oracledb.init_oracle_client(lib_dir=lib_dir)
                        else:
                            logger.info("Initializing thick mode with default Oracle Client location")
                            oracledb.init_oracle_client()
                        _thick_mode_initialized = True
                        logger.info("Thick mode initialized successfully")
                    except Exception as e:
                        error_msg = str(e)
                        if "DPY-2019" in error_msg or "thin mode has already been enabled" in error_msg:
                            logger.warning("Failed to initialize thick mode: Thin mode already in use")
                            logger.warning("IMPORTANT: Thick mode must be initialized BEFORE any connections are created")
                            logger.warning("Solution: Call init_thick_mode() at the start of your script, before creating any clients")
                        else:
                            logger.warning(f"Failed to initialize thick mode: {e}")
                        logger.warning("Falling back to thin mode")
                        self.use_thick_mode = False

            # Configure TLS if requested
            if self.use_tls:
                # Set up TLS parameters
                dsn = oracledb.makedsn(
                    self.config['host'],
                    self.config['port'],
                    service_name=self.config.get('service_name', 'ORCLPDB1')
                )

                self.connection = oracledb.connect(
                    user=self.config['user'],
                    password=self.config['password'],
                    dsn=dsn,
                    # TLS configuration
                    ssl_context=self.config.get('ssl_context'),
                    wallet_location=self.config.get('wallet_location'),
                    wallet_password=self.config.get('wallet_password')
                )
            else:
                self.connection = oracledb.connect(
                    user=self.config['user'],
                    password=self.config['password'],
                    host=self.config['host'],
                    port=self.config['port'],
                    service_name=self.config.get('service_name', 'ORCLPDB1')
                )

            self.cursor = self.connection.cursor()
            mode = "thick" if self.use_thick_mode and _thick_mode_initialized else "thin"
            logger.info(f"Connection {self.connection_id} established ({mode} mode)")
            return True

        except Exception as e:
            logger.error(f"Connection {self.connection_id} failed: {str(e)}")
            return False
    
    def disconnect(self):
        """Close the database connection"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            logger.info(f"Connection {self.connection_id} closed")
        except Exception as e:
            logger.error(f"Error closing connection {self.connection_id}: {str(e)}")
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


class OracleTestClient:
    """Main test client for Oracle database testing"""
    
    def __init__(
        self,
        db_config: Dict[str, Any],
        load_profile: LoadProfile,
        use_tls: bool = True,
        setup_tables: bool = True,
        use_prepared_statements: bool = True,
        use_thick_mode: bool = False
    ):
        """
        Initialize Oracle test client

        Args:
            db_config: Database connection configuration
            load_profile: Load profile for testing
            use_tls: Whether to use TLS connections
            setup_tables: Whether to automatically create test tables
            use_prepared_statements: Whether to use prepared statements (recommended)
            use_thick_mode: Whether to use Oracle thick client mode (requires Oracle Instant Client)
        """
        self.db_config = db_config
        self.load_profile = load_profile
        self.use_tls = use_tls
        self.use_prepared_statements = use_prepared_statements
        self.use_thick_mode = use_thick_mode
        self.results = TestResults(load_profile=load_profile)
        self._stop_flag = threading.Event()
        
        # Prepared statement SQL templates
        self._prepared_statements = {
            'insert': "INSERT INTO test_large_data (id, data_chunk) VALUES (test_data_seq.NEXTVAL, :data)",
            'select_random': """
                SELECT data_chunk
                FROM test_large_data
                WHERE ROWNUM = 1
                ORDER BY DBMS_RANDOM.VALUE
            """,
            'select_by_id': "SELECT data_chunk FROM test_large_data WHERE id = :id",
            'insert_metric': """
                INSERT INTO test_metrics (metric_id, operation_type, duration_ms, success, created_at)
                VALUES (test_data_seq.NEXTVAL, :op_type, :duration, :success, CURRENT_TIMESTAMP)
            """,
            # Comprehensive table queries
            'select_by_status': """
                SELECT * FROM test_comprehensive
                WHERE status = :status
                AND ROWNUM <= :limit
            """,
            'select_by_category': """
                SELECT * FROM test_comprehensive
                WHERE category = :category
                AND ROWNUM <= :limit
            """,
            'select_by_price_range': """
                SELECT * FROM test_comprehensive
                WHERE price BETWEEN :min_price AND :max_price
                AND ROWNUM <= :limit
            """,
            'select_by_date_range': """
                SELECT * FROM test_comprehensive
                WHERE date_field BETWEEN :start_date AND :end_date
                AND ROWNUM <= :limit
            """,
            'aggregate_by_category': """
                SELECT category, COUNT(*) as count, AVG(price) as avg_price, SUM(quantity) as total_qty
                FROM test_comprehensive
                WHERE category = :category
                GROUP BY category
            """,
        }
        
        if setup_tables:
            self._setup_test_tables()
    
    @staticmethod
    def test_connection(db_config: Dict[str, Any], use_tls: bool = False) -> tuple[bool, str]:
        """
        Test database connectivity without creating tables
        
        Args:
            db_config: Database connection configuration
            use_tls: Whether to use TLS
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        use_thick_mode = db_config.get('use_thick_mode', False)
        conn = OracleTestConnection("connection_test", db_config, use_tls, use_thick_mode)
        try:
            if conn.connect():
                # Try a simple query
                conn.cursor.execute("SELECT 1 FROM DUAL")
                result = conn.cursor.fetchone()
                conn.disconnect()
                
                if result and result[0] == 1:
                    return True, "✓ Connection successful! Database is accessible."
                else:
                    return False, "✗ Connection established but query failed."
            else:
                error_msg = "✗ Connection failed. Please check:\n"
                error_msg += f"  • Host: {db_config.get('host', 'NOT SET')}\n"
                error_msg += f"  • Port: {db_config.get('port', 'NOT SET')}\n"
                error_msg += f"  • User: {db_config.get('user', 'NOT SET')}\n"
                error_msg += f"  • Service: {db_config.get('service_name', 'NOT SET')}\n"
                if use_tls:
                    error_msg += f"  • TLS: enabled\n"
                    error_msg += f"  • Wallet: {db_config.get('wallet_location', 'NOT SET')}"
                return False, error_msg
        except Exception as e:
            error_str = str(e)
            
            # Check for common service name error
            if 'DPY-6001' in error_str or 'ORA-12514' in error_str or 'not registered' in error_str:
                error_msg = "✗ Service name error: The service is not registered with the listener.\n\n"
                error_msg += f"You specified: '{db_config.get('service_name', 'NOT SET')}'\n\n"
                error_msg += "To find the correct service name, try one of these:\n\n"
                error_msg += "1. Check listener services:\n"
                error_msg += "   lsnrctl services\n\n"
                error_msg += "2. Try common service names:\n"
                error_msg += "   - ORCLPDB1 (pluggable database)\n"
                error_msg += "   - ORCL (container database)\n"
                error_msg += "   - XE (Oracle Express Edition)\n"
                error_msg += "   - XEPDB1 (XE pluggable database)\n\n"
                error_msg += "3. Use the discover_services() method:\n"
                error_msg += "   python -c \"from oracle_test_lib import OracleTestClient; \\\n"
                error_msg += "   OracleTestClient.discover_services('localhost', 1521)\"\n\n"
                error_msg += f"Original error: {error_str}"
                return False, error_msg
            
            return False, f"✗ Connection error: {error_str}"
    
    @staticmethod
    def discover_services(host: str, port: int = 1521) -> List[str]:
        """
        Discover available Oracle services on a host
        
        Args:
            host: Database host
            port: Database port (default: 1521)
            
        Returns:
            List of discovered service names
        """
        import socket
        
        discovered = []
        
        # Common Oracle service names to try
        common_services = [
            'ORCL', 'ORCLPDB1', 'ORCLCDB',
            'XE', 'XEPDB1',
            'FREEPDB1', 'FREE',
            'CDB', 'PDB1', 'PDB2',
            'PROD', 'DEV', 'TEST'
        ]
        
        print(f"Discovering services on {host}:{port}...")
        print("=" * 60)
        
        # First, check if port is open
        try:
            sock = socket.create_connection((host, port), timeout=2)
            sock.close()
            print(f"✓ Port {port} is open on {host}")
        except Exception as e:
            print(f"✗ Cannot connect to {host}:{port}")
            print(f"  Error: {e}")
            print("\nMake sure:")
            print("  1. Oracle database is running")
            print("  2. Listener is started (lsnrctl start)")
            print("  3. Port is not blocked by firewall")
            return []
        
        print(f"\nTrying common service names...")
        print("-" * 60)
        
        for service in common_services:
            try:
                # Try to connect with minimal config
                conn = oracledb.connect(
                    user='SYS',  # Use SYS to test connectivity
                    password='invalid',  # Wrong password is OK for service discovery
                    host=host,
                    port=port,
                    service_name=service,
                    mode=oracledb.SYSDBA
                )
                conn.close()
                print(f"✓ Found: {service}")
                discovered.append(service)
            except Exception as e:
                error_str = str(e)
                # If we get a password error, the service exists
                if 'ORA-01017' in error_str or 'invalid username/password' in error_str.lower():
                    print(f"✓ Found: {service} (credentials needed)")
                    discovered.append(service)
                elif 'DPY-6001' in error_str or 'ORA-12514' in error_str or 'not registered' in error_str:
                    # Service doesn't exist
                    pass
                else:
                    # Other error
                    pass
        
        if discovered:
            print("\n" + "=" * 60)
            print(f"✓ Discovered {len(discovered)} service(s):")
            for svc in discovered:
                print(f"  - {svc}")
            print("\nTry using one of these in your db_config:")
            print("  db_config['service_name'] = '" + discovered[0] + "'")
        else:
            print("\n" + "=" * 60)
            print("✗ No common services found.")
            print("\nTo find the service name manually:")
            print("  1. Run: lsnrctl services")
            print("  2. Look for 'Service' entries")
            print("  3. Use the service name (not the SID)")
            print("\nOr connect to sqlplus and run:")
            print("  SELECT name FROM v$database;")
            print("  SELECT name FROM v$pdbs;")
        
        return discovered
    
    def _setup_test_tables(self):
        """Create necessary test tables"""
        conn = None
        try:
            conn = OracleTestConnection("setup", self.db_config, self.use_tls, self.use_thick_mode)
            if not conn.connect():
                error_msg = "Failed to establish setup connection. Please check:\n"
                error_msg += "  1. Database host and port are correct\n"
                error_msg += "  2. Database credentials are valid\n"
                error_msg += "  3. Database service is running\n"
                error_msg += "  4. Network connectivity is available\n"
                if self.use_tls:
                    error_msg += "  5. TLS/wallet configuration is correct"
                raise RuntimeError(error_msg)

            try:
                # Drop tables if they exist
                for table in ['test_large_data', 'test_metrics', 'test_comprehensive']:
                    try:
                        conn.cursor.execute(f"DROP TABLE {table}")
                        logger.debug(f"Dropped existing table: {table}")
                    except Exception as e:
                        logger.debug(f"Table {table} does not exist or cannot be dropped: {str(e)}")

                # Create large data table (original)
                conn.cursor.execute("""
                    CREATE TABLE test_large_data (
                        id NUMBER PRIMARY KEY,
                        data_chunk CLOB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.debug("Created test_large_data table")

                # Create metrics table (original)
                conn.cursor.execute("""
                    CREATE TABLE test_metrics (
                        metric_id NUMBER PRIMARY KEY,
                        operation_type VARCHAR2(50),
                        duration_ms NUMBER,
                        success NUMBER(1),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.debug("Created test_metrics table")

                # Create comprehensive test table with multiple column types
                conn.cursor.execute("""
                    CREATE TABLE test_comprehensive (
                        id NUMBER PRIMARY KEY,
                        varchar_short VARCHAR2(50),
                        varchar_long VARCHAR2(4000),
                        number_int NUMBER(10),
                        number_decimal NUMBER(10,2),
                        number_float BINARY_DOUBLE,
                        date_field DATE,
                        timestamp_field TIMESTAMP,
                        timestamp_tz TIMESTAMP WITH TIME ZONE,
                        clob_field CLOB,
                        blob_field BLOB,
                        char_field CHAR(10),
                        status VARCHAR2(20),
                        category VARCHAR2(50),
                        price NUMBER(12,2),
                        quantity NUMBER(8),
                        is_active NUMBER(1),
                        email VARCHAR2(255),
                        description VARCHAR2(1000),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.debug("Created test_comprehensive table")

                # Create indexes for query performance testing
                conn.cursor.execute("""
                    CREATE INDEX idx_comprehensive_status ON test_comprehensive(status)
                """)
                conn.cursor.execute("""
                    CREATE INDEX idx_comprehensive_category ON test_comprehensive(category)
                """)
                conn.cursor.execute("""
                    CREATE INDEX idx_comprehensive_date ON test_comprehensive(date_field)
                """)
                conn.cursor.execute("""
                    CREATE INDEX idx_comprehensive_price ON test_comprehensive(price)
                """)
                logger.debug("Created indexes on test_comprehensive table")

                # Create sequence for IDs
                try:
                    conn.cursor.execute("DROP SEQUENCE test_data_seq")
                    logger.debug("Dropped existing sequence: test_data_seq")
                except Exception as e:
                    logger.debug(f"Sequence test_data_seq does not exist: {str(e)}")

                conn.cursor.execute("CREATE SEQUENCE test_data_seq START WITH 1")
                logger.debug("Created test_data_seq sequence")

                conn.connection.commit()
                logger.info("Test tables created successfully")

            except Exception as e:
                logger.error(f"Error setting up tables: {str(e)}")
                if conn.connection:
                    conn.connection.rollback()
                raise RuntimeError(f"Failed to create test tables: {str(e)}")

        finally:
            if conn:
                conn.disconnect()
    
    def _generate_test_data(self, size_kb: int) -> str:
        """Generate random test data of specified size"""
        size_bytes = size_kb * 1024
        # Generate random string data
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(size_bytes))

    def populate_comprehensive_data(
        self,
        num_rows: int,
        batch_size: int = 1000,
        connection: Optional[OracleTestConnection] = None
    ) -> Dict[str, Any]:
        """
        Populate test_comprehensive table with large number of rows

        Args:
            num_rows: Total number of rows to insert
            batch_size: Number of rows per batch insert (default 1000)
            connection: Optional existing connection, creates new one if None

        Returns:
            Dictionary with population statistics
        """
        should_close = False
        if connection is None:
            connection = OracleTestConnection("populate", self.db_config, self.use_tls, self.use_thick_mode)
            if not connection.connect():
                raise RuntimeError("Failed to establish connection for data population")
            should_close = True

        start_time = time.time()
        rows_inserted = 0

        try:
            # Sample data for random generation
            statuses = ['active', 'inactive', 'pending', 'completed', 'cancelled']
            categories = ['electronics', 'clothing', 'food', 'books', 'toys', 'sports', 'home', 'automotive']
            domains = ['example.com', 'test.com', 'demo.org', 'sample.net']

            logger.info(f"Starting population of {num_rows} rows in batches of {batch_size}")

            # Build insert SQL
            insert_sql = """
                INSERT INTO test_comprehensive (
                    id, varchar_short, varchar_long, number_int, number_decimal, number_float,
                    date_field, timestamp_field, timestamp_tz, clob_field, blob_field,
                    char_field, status, category, price, quantity, is_active, email, description
                ) VALUES (
                    test_data_seq.NEXTVAL, :varchar_short, :varchar_long, :number_int,
                    :number_decimal, :number_float, :date_field, :timestamp_field, :timestamp_tz,
                    :clob_field, :blob_field, :char_field, :status, :category, :price,
                    :quantity, :is_active, :email, :description
                )
            """

            batches = (num_rows + batch_size - 1) // batch_size

            for batch_num in range(batches):
                batch_start = batch_num * batch_size
                batch_end = min((batch_num + 1) * batch_size, num_rows)
                current_batch_size = batch_end - batch_start

                # Generate batch data
                batch_data = []
                for i in range(current_batch_size):
                    row_id = batch_start + i

                    # Generate random data for each column
                    row = {
                        'varchar_short': f'item_{row_id}',
                        'varchar_long': ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(100, 500))),
                        'number_int': random.randint(1, 1000000),
                        'number_decimal': round(random.uniform(0, 999999.99), 2),
                        'number_float': random.uniform(0, 1000000),
                        'date_field': datetime.now() - timedelta(days=random.randint(0, 365)),
                        'timestamp_field': datetime.now() - timedelta(hours=random.randint(0, 8760)),
                        'timestamp_tz': datetime.now() - timedelta(minutes=random.randint(0, 525600)),
                        'clob_field': ''.join(random.choices(string.ascii_letters + string.digits + ' \n', k=random.randint(1000, 5000))),
                        'blob_field': bytes(random.getrandbits(8) for _ in range(random.randint(100, 1000))),
                        'char_field': f'CHAR{row_id % 10000:05d}',
                        'status': random.choice(statuses),
                        'category': random.choice(categories),
                        'price': round(random.uniform(1.00, 9999.99), 2),
                        'quantity': random.randint(0, 10000),
                        'is_active': random.randint(0, 1),
                        'email': f'user{row_id}@{random.choice(domains)}',
                        'description': f'Description for item {row_id}: ' + ''.join(random.choices(string.ascii_letters + ' ', k=random.randint(50, 200)))
                    }
                    batch_data.append(row)

                # Execute batch insert
                connection.cursor.executemany(insert_sql, batch_data)
                connection.connection.commit()

                rows_inserted += current_batch_size

                if (batch_num + 1) % 10 == 0 or batch_num == batches - 1:
                    elapsed = time.time() - start_time
                    rate = rows_inserted / elapsed if elapsed > 0 else 0
                    logger.info(f"Progress: {rows_inserted}/{num_rows} rows inserted ({rate:.0f} rows/sec)")

            elapsed_time = time.time() - start_time

            stats = {
                'rows_inserted': rows_inserted,
                'elapsed_time_sec': elapsed_time,
                'rows_per_second': rows_inserted / elapsed_time if elapsed_time > 0 else 0,
                'batches': batches,
                'batch_size': batch_size
            }

            logger.info(f"Population complete: {rows_inserted} rows in {elapsed_time:.2f} seconds ({stats['rows_per_second']:.0f} rows/sec)")
            return stats

        except Exception as e:
            logger.error(f"Error during data population: {str(e)}")
            connection.connection.rollback()
            raise RuntimeError(f"Failed to populate data: {str(e)}")

        finally:
            if should_close:
                connection.disconnect()

    def test_comprehensive_queries(
        self,
        connection: OracleTestConnection,
        query_type: str = 'all'
    ) -> Dict[str, Any]:
        """
        Test various query patterns on test_comprehensive table

        Args:
            connection: Database connection
            query_type: Type of query to test ('all', 'select_all', 'where_indexed',
                       'where_non_indexed', 'aggregate', 'join', 'order_by', 'group_by')

        Returns:
            Dictionary with query results and performance metrics
        """
        queries = {}

        # Define test queries
        if query_type in ['all', 'select_all']:
            queries['select_all'] = "SELECT * FROM test_comprehensive WHERE ROWNUM <= 100"

        if query_type in ['all', 'where_indexed']:
            queries['where_status'] = "SELECT * FROM test_comprehensive WHERE status = 'active' AND ROWNUM <= 100"
            queries['where_category'] = "SELECT * FROM test_comprehensive WHERE category = 'electronics' AND ROWNUM <= 100"
            queries['where_price_range'] = "SELECT * FROM test_comprehensive WHERE price BETWEEN 100 AND 500 AND ROWNUM <= 100"
            queries['where_date_range'] = "SELECT * FROM test_comprehensive WHERE date_field >= SYSDATE - 30 AND ROWNUM <= 100"

        if query_type in ['all', 'where_non_indexed']:
            queries['where_varchar_long'] = "SELECT * FROM test_comprehensive WHERE LENGTH(varchar_long) > 200 AND ROWNUM <= 100"
            queries['where_quantity'] = "SELECT * FROM test_comprehensive WHERE quantity > 5000 AND ROWNUM <= 100"

        if query_type in ['all', 'aggregate']:
            queries['count_all'] = "SELECT COUNT(*) as total_rows FROM test_comprehensive"
            queries['avg_price'] = "SELECT AVG(price) as avg_price FROM test_comprehensive"
            queries['sum_quantity'] = "SELECT SUM(quantity) as total_quantity FROM test_comprehensive"
            queries['min_max_price'] = "SELECT MIN(price) as min_price, MAX(price) as max_price FROM test_comprehensive"

        if query_type in ['all', 'group_by']:
            queries['group_by_status'] = "SELECT status, COUNT(*) as count, AVG(price) as avg_price FROM test_comprehensive GROUP BY status"
            queries['group_by_category'] = "SELECT category, COUNT(*) as count, SUM(quantity) as total_qty FROM test_comprehensive GROUP BY category"
            queries['group_by_multiple'] = """
                SELECT status, category, COUNT(*) as count, AVG(price) as avg_price
                FROM test_comprehensive
                GROUP BY status, category
                ORDER BY count DESC
            """

        if query_type in ['all', 'order_by']:
            queries['order_by_price'] = "SELECT * FROM test_comprehensive ORDER BY price DESC FETCH FIRST 100 ROWS ONLY"
            queries['order_by_date'] = "SELECT * FROM test_comprehensive ORDER BY date_field DESC FETCH FIRST 100 ROWS ONLY"

        if query_type in ['all', 'complex']:
            queries['complex_where'] = """
                SELECT *
                FROM test_comprehensive
                WHERE status IN ('active', 'pending')
                  AND category = 'electronics'
                  AND price > 100
                  AND is_active = 1
                  AND date_field >= SYSDATE - 180
                ORDER BY price DESC
                FETCH FIRST 50 ROWS ONLY
            """
            queries['having_clause'] = """
                SELECT category, status, COUNT(*) as count, AVG(price) as avg_price
                FROM test_comprehensive
                GROUP BY category, status
                HAVING COUNT(*) > 10 AND AVG(price) > 100
                ORDER BY count DESC
            """

        results = {}

        for query_name, sql in queries.items():
            start_time = time.time()
            try:
                connection.cursor.execute(sql)
                rows = connection.cursor.fetchall()
                elapsed_time = time.time() - start_time

                results[query_name] = {
                    'success': True,
                    'rows_returned': len(rows),
                    'elapsed_time_ms': elapsed_time * 1000,
                    'query': sql
                }

                logger.info(f"Query '{query_name}': {len(rows)} rows in {elapsed_time*1000:.2f}ms")

            except Exception as e:
                elapsed_time = time.time() - start_time
                results[query_name] = {
                    'success': False,
                    'error': str(e),
                    'elapsed_time_ms': elapsed_time * 1000,
                    'query': sql
                }
                logger.error(f"Query '{query_name}' failed: {str(e)}")

        return results

    def test_query_performance(
        self,
        connection: OracleTestConnection,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        iterations: int = 10
    ) -> Dict[str, Any]:
        """
        Test performance of a specific query over multiple iterations

        Args:
            connection: Database connection
            query: SQL query to test
            params: Optional query parameters
            iterations: Number of times to execute the query

        Returns:
            Dictionary with performance statistics
        """
        execution_times = []
        rows_returned = []
        errors = 0

        logger.info(f"Running query performance test ({iterations} iterations)")

        for i in range(iterations):
            start_time = time.time()
            try:
                if params:
                    connection.cursor.execute(query, params)
                else:
                    connection.cursor.execute(query)

                rows = connection.cursor.fetchall()
                elapsed_time = time.time() - start_time

                execution_times.append(elapsed_time * 1000)  # Convert to ms
                rows_returned.append(len(rows))

            except Exception as e:
                errors += 1
                logger.error(f"Iteration {i+1} failed: {str(e)}")

        if execution_times:
            stats = {
                'query': query,
                'iterations': iterations,
                'successful_iterations': len(execution_times),
                'failed_iterations': errors,
                'avg_time_ms': sum(execution_times) / len(execution_times),
                'min_time_ms': min(execution_times),
                'max_time_ms': max(execution_times),
                'total_time_ms': sum(execution_times),
                'avg_rows_returned': sum(rows_returned) / len(rows_returned) if rows_returned else 0,
                'execution_times_ms': execution_times
            }
        else:
            stats = {
                'query': query,
                'iterations': iterations,
                'successful_iterations': 0,
                'failed_iterations': errors,
                'error': 'All iterations failed'
            }

        logger.info(f"Performance test complete: avg={stats.get('avg_time_ms', 0):.2f}ms, "
                   f"min={stats.get('min_time_ms', 0):.2f}ms, max={stats.get('max_time_ms', 0):.2f}ms")

        return stats

    def test_large_write(
        self,
        connection: OracleTestConnection,
        data_size_kb: int
    ) -> TestMetrics:
        """
        Test large write operation with optional prepared statement
        
        Args:
            connection: Database connection
            data_size_kb: Size of data to write in KB
            
        Returns:
            TestMetrics with operation results
        """
        start_time = time.time()
        metric = TestMetrics(
            operation_type="large_write",
            start_time=start_time,
            end_time=0,
            success=False,
            connection_id=connection.connection_id
        )
        
        try:
            # Generate test data
            test_data = self._generate_test_data(data_size_kb)
            metric.data_size_bytes = len(test_data)
            
            if self.use_prepared_statements:
                # Use prepared statement (more efficient)
                connection.cursor.execute(
                    self._prepared_statements['insert'],
                    {'data': test_data}
                )
            else:
                # Use direct SQL (for comparison)
                connection.cursor.execute(
                    "INSERT INTO test_large_data (id, data_chunk) VALUES (test_data_seq.NEXTVAL, :data)",
                    {'data': test_data}
                )
            
            connection.connection.commit()
            
            metric.success = True
            logger.debug(f"Large write completed: {data_size_kb}KB (prepared: {self.use_prepared_statements})")
            
        except Exception as e:
            metric.error_message = str(e)
            logger.error(f"Large write failed: {str(e)}")
        finally:
            metric.end_time = time.time()
        
        return metric
    
    def test_large_read(
        self,
        connection: OracleTestConnection,
        expected_size_kb: Optional[int] = None
    ) -> TestMetrics:
        """
        Test large read operation with optional prepared statement
        
        Args:
            connection: Database connection
            expected_size_kb: Expected size to read (for metric accuracy)
            
        Returns:
            TestMetrics with operation results
        """
        start_time = time.time()
        metric = TestMetrics(
            operation_type="large_read",
            start_time=start_time,
            end_time=0,
            success=False,
            connection_id=connection.connection_id
        )
        
        try:
            if self.use_prepared_statements:
                # Use prepared statement
                connection.cursor.execute(self._prepared_statements['select_random'])
            else:
                # Use direct SQL
                connection.cursor.execute("""
                    SELECT data_chunk 
                    FROM test_large_data 
                    WHERE ROWNUM = 1
                    ORDER BY DBMS_RANDOM.VALUE
                """)
            
            result = connection.cursor.fetchone()
            if result:
                data = result[0]
                # Handle LOB objects (CLOB/BLOB) - need to read() them first
                if hasattr(data, 'read'):
                    data = data.read()
                metric.data_size_bytes = len(data) if data else 0
                metric.success = True
                logger.debug(f"Large read completed: {metric.data_size_bytes} bytes (prepared: {self.use_prepared_statements})")
            else:
                metric.error_message = "No data found to read"
                
        except Exception as e:
            metric.error_message = str(e)
            logger.error(f"Large read failed: {str(e)}")
        finally:
            metric.end_time = time.time()
        
        return metric
    
    def test_batch_write(
        self,
        connection: OracleTestConnection,
        batch_size: int,
        data_size_kb: int
    ) -> TestMetrics:
        """
        Test batch write operations using prepared statements
        
        Args:
            connection: Database connection
            batch_size: Number of records to insert in batch
            data_size_kb: Size of each data chunk in KB
            
        Returns:
            TestMetrics with operation results
        """
        start_time = time.time()
        metric = TestMetrics(
            operation_type="batch_write",
            start_time=start_time,
            end_time=0,
            success=False,
            connection_id=connection.connection_id
        )
        
        try:
            # Prepare batch data
            batch_data = []
            for _ in range(batch_size):
                test_data = self._generate_test_data(data_size_kb)
                batch_data.append({'data': test_data})
            
            metric.data_size_bytes = sum(len(item['data']) for item in batch_data)
            
            if self.use_prepared_statements:
                # Use executemany with prepared statement (most efficient)
                connection.cursor.executemany(
                    self._prepared_statements['insert'],
                    batch_data
                )
            else:
                # Individual inserts (for comparison)
                for item in batch_data:
                    connection.cursor.execute(
                        "INSERT INTO test_large_data (id, data_chunk) VALUES (test_data_seq.NEXTVAL, :data)",
                        item
                    )
            
            connection.connection.commit()
            
            metric.success = True
            logger.debug(f"Batch write completed: {batch_size} records, {data_size_kb}KB each")
            
        except Exception as e:
            metric.error_message = str(e)
            logger.error(f"Batch write failed: {str(e)}")
        finally:
            metric.end_time = time.time()
        
        return metric
    
    def compare_prepared_vs_direct(
        self,
        num_operations: int = 100,
        data_size_kb: int = 100
    ) -> Dict[str, TestResults]:
        """
        Compare performance of prepared statements vs direct SQL
        
        Args:
            num_operations: Number of operations to test
            data_size_kb: Size of data for each operation
            
        Returns:
            Dictionary with results for both methods
        """
        results = {}
        
        # Test with prepared statements
        logger.info("Testing WITH prepared statements...")
        self.use_prepared_statements = True
        self.results = TestResults(load_profile=self.load_profile)
        
        conn = OracleTestConnection("prepared_test", self.db_config, self.use_tls, self.use_thick_mode)
        if conn.connect():
            try:
                for i in range(num_operations):
                    metric = self.test_large_write(conn, data_size_kb)
                    self.results.add_metric(metric)
            finally:
                conn.disconnect()

        results['prepared'] = self.results

        # Test without prepared statements
        logger.info("Testing WITHOUT prepared statements...")
        self.use_prepared_statements = False
        self.results = TestResults(load_profile=self.load_profile)

        conn = OracleTestConnection("direct_test", self.db_config, self.use_tls, self.use_thick_mode)
        if conn.connect():
            try:
                for i in range(num_operations):
                    metric = self.test_large_write(conn, data_size_kb)
                    self.results.add_metric(metric)
            finally:
                conn.disconnect()
        
        results['direct'] = self.results
        
        # Reset to prepared statements (best practice)
        self.use_prepared_statements = True
        
        return results
    
    def test_concurrent_operations(
        self,
        operation_func: Callable,
        num_connections: int,
        operations_per_connection: int
    ) -> List[TestMetrics]:
        """
        Test concurrent operations across multiple connections
        
        Args:
            operation_func: Function to execute (test_large_write or test_large_read)
            num_connections: Number of concurrent connections
            operations_per_connection: Operations per connection
            
        Returns:
            List of TestMetrics from all operations
        """
        metrics = []
        
        def worker(connection_id: int) -> List[TestMetrics]:
            worker_metrics = []
            conn = OracleTestConnection(
                f"conn_{connection_id}",
                self.db_config,
                self.use_tls,
                self.use_thick_mode
            )
            
            if not conn.connect():
                return worker_metrics
            
            try:
                for i in range(operations_per_connection):
                    if self._stop_flag.is_set():
                        break
                    
                    metric = operation_func(conn)
                    worker_metrics.append(metric)
                    
                    # Apply think time
                    if self.load_profile.think_time_ms > 0:
                        time.sleep(self.load_profile.think_time_ms / 1000)
                        
            finally:
                conn.disconnect()
            
            return worker_metrics
        
        # Execute concurrent workers
        with ThreadPoolExecutor(max_workers=num_connections) as executor:
            futures = [
                executor.submit(worker, i) 
                for i in range(num_connections)
            ]
            
            for future in as_completed(futures):
                try:
                    worker_metrics = future.result()
                    metrics.extend(worker_metrics)
                except Exception as e:
                    logger.error(f"Worker failed: {str(e)}")
        
        return metrics
    
    def run_write_test(self) -> TestResults:
        """
        Run comprehensive write test based on load profile
        
        Returns:
            TestResults with aggregated metrics
        """
        logger.info(f"Starting write test with {self.load_profile.name} profile")
        
        # Calculate operations
        total_operations = (
            self.load_profile.operations_per_second * 
            self.load_profile.duration_seconds
        )
        ops_per_connection = total_operations // self.load_profile.concurrent_connections
        
        # Create wrapper for write operation
        def write_op(conn):
            return self.test_large_write(conn, self.load_profile.data_size_kb)
        
        # Run test
        metrics = self.test_concurrent_operations(
            write_op,
            self.load_profile.concurrent_connections,
            ops_per_connection
        )
        
        # Store results
        for metric in metrics:
            self.results.add_metric(metric)
        
        logger.info(f"Write test completed: {len(metrics)} operations")
        return self.results
    
    def run_read_test(self) -> TestResults:
        """
        Run comprehensive read test based on load profile
        
        Returns:
            TestResults with aggregated metrics
        """
        logger.info(f"Starting read test with {self.load_profile.name} profile")
        
        # Calculate operations
        total_operations = (
            self.load_profile.operations_per_second * 
            self.load_profile.duration_seconds
        )
        ops_per_connection = total_operations // self.load_profile.concurrent_connections
        
        # Create wrapper for read operation
        def read_op(conn):
            return self.test_large_read(conn, self.load_profile.data_size_kb)
        
        # Run test
        metrics = self.test_concurrent_operations(
            read_op,
            self.load_profile.concurrent_connections,
            ops_per_connection
        )
        
        # Store results
        for metric in metrics:
            self.results.add_metric(metric)
        
        logger.info(f"Read test completed: {len(metrics)} operations")
        return self.results
    
    def run_mixed_test(self, read_write_ratio: float = 0.5) -> TestResults:
        """
        Run mixed read/write test
        
        Args:
            read_write_ratio: Ratio of reads to total operations (0.0 to 1.0)
            
        Returns:
            TestResults with aggregated metrics
        """
        logger.info(f"Starting mixed test with {self.load_profile.name} profile")
        
        total_operations = (
            self.load_profile.operations_per_second * 
            self.load_profile.duration_seconds
        )
        
        def mixed_op(conn):
            if random.random() < read_write_ratio:
                return self.test_large_read(conn, self.load_profile.data_size_kb)
            else:
                return self.test_large_write(conn, self.load_profile.data_size_kb)
        
        ops_per_connection = total_operations // self.load_profile.concurrent_connections
        
        metrics = self.test_concurrent_operations(
            mixed_op,
            self.load_profile.concurrent_connections,
            ops_per_connection
        )
        
        for metric in metrics:
            self.results.add_metric(metric)
        
        logger.info(f"Mixed test completed: {len(metrics)} operations")
        return self.results
    
    def stop(self):
        """Stop all running tests"""
        self._stop_flag.set()
        logger.info("Stop signal sent to all test operations")


class OracleTestSuite:
    """Orchestrates multiple test scenarios"""
    
    def __init__(self, db_config: Dict[str, Any], use_tls: bool = True):
        """
        Initialize test suite
        
        Args:
            db_config: Database connection configuration
            use_tls: Whether to use TLS connections
        """
        self.db_config = db_config
        self.use_tls = use_tls
        self.test_results: List[TestResults] = []
    
    def run_all_tests(self, include_high_load: bool = False) -> List[TestResults]:
        """
        Run all test scenarios
        
        Args:
            include_high_load: Whether to include high load tests
            
        Returns:
            List of TestResults from all tests
        """
        results = []
        
        # Test with low load
        logger.info("=" * 60)
        logger.info("Running LOW LOAD tests")
        logger.info("=" * 60)
        
        low_load = LoadProfile.low_load()
        
        # Low load write test
        client = OracleTestClient(self.db_config, low_load, self.use_tls)
        result = client.run_write_test()
        results.append(result)
        
        # Low load read test
        client = OracleTestClient(self.db_config, low_load, self.use_tls, setup_tables=False)
        result = client.run_read_test()
        results.append(result)
        
        # Low load mixed test
        client = OracleTestClient(self.db_config, low_load, self.use_tls, setup_tables=False)
        result = client.run_mixed_test()
        results.append(result)
        
        if include_high_load:
            logger.info("=" * 60)
            logger.info("Running HIGH LOAD tests")
            logger.info("=" * 60)
            
            high_load = LoadProfile.high_load()
            
            # High load write test
            client = OracleTestClient(self.db_config, high_load, self.use_tls, setup_tables=False)
            result = client.run_write_test()
            results.append(result)
            
            # High load read test
            client = OracleTestClient(self.db_config, high_load, self.use_tls, setup_tables=False)
            result = client.run_read_test()
            results.append(result)
        
        self.test_results = results
        return results
    
    def print_summary(self):
        """Print summary of all test results"""
        print("\n" + "=" * 80)
        print("TEST RESULTS SUMMARY")
        print("=" * 80)
        
        for result in self.test_results:
            summary = result.get_summary()
            print(f"\n{summary['load_profile']} Profile:")
            print(f"  Total Operations: {summary['total_operations']}")
            print(f"  Success Rate: {summary['success_rate']:.2f}%")
            print(f"  Total Data Transferred: {summary['total_data_transferred_mb']:.2f} MB")
            
            if 'avg_duration_ms' in summary:
                print(f"  Average Duration: {summary['avg_duration_ms']:.2f} ms")
                print(f"  P95 Duration: {summary['p95_duration_ms']:.2f} ms")
                print(f"  P99 Duration: {summary['p99_duration_ms']:.2f} ms")
            
            if 'avg_throughput_mbps' in summary:
                print(f"  Average Throughput: {summary['avg_throughput_mbps']:.2f} MB/s")
