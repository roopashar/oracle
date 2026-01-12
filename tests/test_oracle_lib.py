"""
Unit tests for Oracle Test Library

Run with: pytest test_oracle_lib.py -v
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from oracle_test_lib import (
    LoadProfile,
    TestMetrics,
    TestResults,
    OracleTestConnection,
    OracleTestClient,
    OracleTestSuite
)


class TestLoadProfile:
    """Test LoadProfile class"""
    
    def test_low_load_profile(self):
        """Test low load profile creation"""
        profile = LoadProfile.low_load()
        
        assert profile.name == "Low Load"
        assert profile.concurrent_connections == 2
        assert profile.operations_per_second == 10
        assert profile.data_size_kb == 10
        assert profile.think_time_ms == 100
        assert profile.duration_seconds == 60
    
    def test_high_load_profile(self):
        """Test high load profile creation"""
        profile = LoadProfile.high_load()
        
        assert profile.name == "High Load"
        assert profile.concurrent_connections == 50
        assert profile.operations_per_second == 500
        assert profile.data_size_kb == 1024
        assert profile.think_time_ms == 0
        assert profile.duration_seconds == 300
    
    def test_custom_profile(self):
        """Test custom profile creation"""
        profile = LoadProfile.custom(
            name="Test Profile",
            concurrent_connections=15,
            operations_per_second=75,
            data_size_kb=256
        )
        
        assert profile.name == "Test Profile"
        assert profile.concurrent_connections == 15
        assert profile.operations_per_second == 75
        assert profile.data_size_kb == 256
        # Check defaults are applied
        assert profile.think_time_ms == 50
        assert profile.duration_seconds == 120


class TestTestMetrics:
    """Test TestMetrics class"""
    
    def test_metric_creation(self):
        """Test creating a metric"""
        metric = TestMetrics(
            operation_type="test_write",
            start_time=time.time(),
            end_time=time.time() + 0.1,
            success=True,
            data_size_bytes=1024
        )
        
        assert metric.operation_type == "test_write"
        assert metric.success is True
        assert metric.data_size_bytes == 1024
    
    def test_duration_calculation(self):
        """Test duration calculation"""
        start = time.time()
        end = start + 0.5  # 500ms
        
        metric = TestMetrics(
            operation_type="test",
            start_time=start,
            end_time=end,
            success=True
        )
        
        # Should be approximately 500ms
        assert 490 <= metric.duration_ms <= 510
    
    def test_throughput_calculation(self):
        """Test throughput calculation"""
        start = time.time()
        end = start + 1.0  # 1 second
        
        metric = TestMetrics(
            operation_type="test",
            start_time=start,
            end_time=end,
            success=True,
            data_size_bytes=10 * 1024 * 1024  # 10 MB
        )
        
        # Should be approximately 10 MB/s
        assert 9.5 <= metric.throughput_mbps <= 10.5
    
    def test_zero_throughput(self):
        """Test throughput with zero duration"""
        metric = TestMetrics(
            operation_type="test",
            start_time=1.0,
            end_time=1.0,  # Same time
            success=True,
            data_size_bytes=1024
        )
        
        assert metric.throughput_mbps == 0


class TestTestResults:
    """Test TestResults class"""
    
    def test_add_metric(self):
        """Test adding metrics to results"""
        profile = LoadProfile.low_load()
        results = TestResults(load_profile=profile)
        
        metric = TestMetrics(
            operation_type="test",
            start_time=time.time(),
            end_time=time.time() + 0.1,
            success=True
        )
        
        results.add_metric(metric)
        assert len(results.metrics) == 1
    
    def test_summary_statistics(self):
        """Test summary statistics generation"""
        profile = LoadProfile.low_load()
        results = TestResults(load_profile=profile)
        
        # Add multiple metrics
        for i in range(100):
            start = time.time()
            metric = TestMetrics(
                operation_type="test_write",
                start_time=start,
                end_time=start + (0.05 + i * 0.001),  # Varying durations
                success=i < 95,  # 95% success rate
                data_size_bytes=1024 * 100
            )
            results.add_metric(metric)
        
        summary = results.get_summary()
        
        assert summary['total_operations'] == 100
        assert summary['successful_operations'] == 95
        assert summary['failed_operations'] == 5
        assert summary['success_rate'] == 95.0
        assert 'avg_duration_ms' in summary
        assert 'p95_duration_ms' in summary
        assert 'p99_duration_ms' in summary
    
    def test_empty_results_summary(self):
        """Test summary with no metrics"""
        profile = LoadProfile.low_load()
        results = TestResults(load_profile=profile)
        
        summary = results.get_summary()
        assert 'error' in summary


class TestOracleTestConnection:
    """Test OracleTestConnection class"""
    
    def test_connection_creation(self):
        """Test connection object creation"""
        config = {
            'host': 'localhost',
            'port': 1521,
            'user': 'test',
            'password': 'test',
            'service_name': 'TEST'
        }
        
        conn = OracleTestConnection("test_conn", config, use_tls=False)
        
        assert conn.connection_id == "test_conn"
        assert conn.config == config
        assert conn.use_tls is False
        assert conn.connection is None
        assert conn.cursor is None
    
    @patch('oracle_test_lib.oracledb.connect')
    def test_successful_connection(self, mock_connect):
        """Test successful database connection"""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        config = {
            'host': 'localhost',
            'port': 1521,
            'user': 'test',
            'password': 'test',
            'service_name': 'TEST'
        }
        
        conn = OracleTestConnection("test_conn", config, use_tls=False)
        result = conn.connect()
        
        assert result is True
        assert conn.connection is not None
        assert conn.cursor is not None
    
    @patch('oracle_test_lib.oracledb.connect')
    def test_failed_connection(self, mock_connect):
        """Test failed database connection"""
        mock_connect.side_effect = Exception("Connection failed")
        
        config = {
            'host': 'localhost',
            'port': 1521,
            'user': 'test',
            'password': 'test',
            'service_name': 'TEST'
        }
        
        conn = OracleTestConnection("test_conn", config, use_tls=False)
        result = conn.connect()
        
        assert result is False
        assert conn.connection is None


class TestOracleTestClient:
    """Test OracleTestClient class"""
    
    @patch('oracle_test_lib.OracleTestConnection')
    def test_client_creation(self, mock_conn_class):
        """Test client creation"""
        config = {
            'host': 'localhost',
            'port': 1521,
            'user': 'test',
            'password': 'test',
            'service_name': 'TEST'
        }
        
        # Mock the connection to avoid actual DB setup
        mock_instance = MagicMock()
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=None)
        mock_instance.connection = MagicMock()
        mock_instance.cursor = MagicMock()
        mock_conn_class.return_value = mock_instance
        
        profile = LoadProfile.low_load()
        client = OracleTestClient(
            db_config=config,
            load_profile=profile,
            use_tls=False,
            setup_tables=True
        )
        
        assert client.db_config == config
        assert client.load_profile == profile
        assert client.use_tls is False
    
    def test_data_generation(self):
        """Test test data generation"""
        config = {
            'host': 'localhost',
            'port': 1521,
            'user': 'test',
            'password': 'test'
        }
        profile = LoadProfile.low_load()
        
        with patch('oracle_test_lib.OracleTestConnection'):
            client = OracleTestClient(config, profile, setup_tables=False)
        
        # Test 1KB data generation
        data = client._generate_test_data(1)
        assert len(data) == 1024
        
        # Test 10KB data generation
        data = client._generate_test_data(10)
        assert len(data) == 10240
    
    @patch('oracle_test_lib.OracleTestConnection')
    def test_write_operation(self, mock_conn_class):
        """Test large write operation"""
        config = {'host': 'localhost', 'port': 1521, 'user': 'test', 'password': 'test'}
        profile = LoadProfile.low_load()
        
        # Create mock connection
        mock_conn = MagicMock()
        mock_conn.connection_id = "test_conn"
        mock_conn.cursor = MagicMock()
        mock_conn.connection = MagicMock()
        
        with patch('oracle_test_lib.OracleTestConnection'):
            client = OracleTestClient(config, profile, setup_tables=False)
        
        # Test write
        metric = client.test_large_write(mock_conn, 10)
        
        assert metric.operation_type == "large_write"
        assert metric.connection_id == "test_conn"
        assert metric.data_size_bytes > 0


class TestOracleTestSuite:
    """Test OracleTestSuite class"""
    
    def test_suite_creation(self):
        """Test suite creation"""
        config = {
            'host': 'localhost',
            'port': 1521,
            'user': 'test',
            'password': 'test'
        }
        
        suite = OracleTestSuite(db_config=config, use_tls=True)
        
        assert suite.db_config == config
        assert suite.use_tls is True
        assert len(suite.test_results) == 0


class TestIntegration:
    """Integration tests (require actual database)"""
    
    @pytest.mark.integration
    def test_full_workflow(self):
        """Test complete workflow - requires actual database"""
        # This test is marked and should only run when explicitly requested
        # with actual database credentials
        pytest.skip("Integration test - requires actual database")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
