#!/usr/bin/env python3
"""Tests for the persistent service implementation."""

import asyncio
import unittest
from datetime import datetime
from unittest.mock import Mock, patch

from croniter import croniter
from fastapi.testclient import TestClient

from persistent_service import PersistentMatchListChangeDetectorService


class TestPersistentService(unittest.TestCase):
    """Test suite for the persistent service implementation."""

    def setUp(self):
        """Set up test environment."""
        # Mock configuration
        self.mock_config = {
            "RUN_MODE": "service",
            "CRON_SCHEDULE": "0 * * * *",
            "HEALTH_SERVER_PORT": "8001",  # Use different port for tests
            "HEALTH_SERVER_HOST": "127.0.0.1",
            "FOGIS_USERNAME": "test_user",
            "FOGIS_PASSWORD": "test_password",
        }

        # Patch the config
        self.config_patcher = patch("persistent_service.get_config")
        self.mock_get_config = self.config_patcher.start()
        self.mock_get_config.return_value = self.mock_config

        # Patch the logger
        self.logger_patcher = patch("persistent_service.get_logger")
        self.mock_get_logger = self.logger_patcher.start()
        self.mock_logger = Mock()
        self.mock_get_logger.return_value = self.mock_logger

    def tearDown(self):
        """Clean up after tests."""
        self.config_patcher.stop()
        self.logger_patcher.stop()

    def test_service_initialization(self):
        """Test that the service initializes correctly."""
        service = PersistentMatchListChangeDetectorService()

        self.assertEqual(service.run_mode, "service")
        self.assertEqual(service.cron_schedule, "0 * * * *")
        self.assertEqual(service.health_server_port, 8001)
        self.assertEqual(service.health_server_host, "127.0.0.1")
        self.assertTrue(service.running)
        self.assertEqual(service.execution_count, 0)
        self.assertIsNotNone(service.app)

    def test_cron_schedule_validation(self):
        """Test cron schedule validation."""
        # Valid cron schedule
        service = PersistentMatchListChangeDetectorService()
        self.assertIsNotNone(service.next_execution)

        # Invalid cron schedule
        self.mock_config["CRON_SCHEDULE"] = "invalid cron"
        with self.assertRaises(ValueError):
            PersistentMatchListChangeDetectorService()

    def test_fastapi_app_creation(self):
        """Test FastAPI application creation."""
        service = PersistentMatchListChangeDetectorService()
        app = service.app

        # Check that the app has the expected routes
        routes = [route.path for route in app.routes]
        self.assertIn("/health", routes)
        self.assertIn("/trigger", routes)
        self.assertIn("/status", routes)

    def test_health_endpoint(self):
        """Test the health check endpoint."""
        service = PersistentMatchListChangeDetectorService()
        client = TestClient(service.app)

        response = client.get("/health")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["service_name"], "match-list-change-detector")
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["run_mode"], "service")
        self.assertEqual(data["cron_schedule"], "0 * * * *")
        self.assertEqual(data["execution_count"], 0)
        self.assertIn("timestamp", data)
        self.assertIn("uptime_seconds", data)

    def test_status_endpoint(self):
        """Test the status endpoint."""
        service = PersistentMatchListChangeDetectorService()
        client = TestClient(service.app)

        response = client.get("/status")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["service_name"], "match-list-change-detector")
        self.assertEqual(data["run_mode"], "service")
        self.assertTrue(data["running"])
        self.assertIn("configuration", data)
        self.assertEqual(data["configuration"]["fogis_username"], "test_user")
        self.assertTrue(data["configuration"]["fogis_password_set"])

    @patch("persistent_service.asyncio.get_event_loop")
    def test_manual_trigger_endpoint(self, mock_get_loop):
        """Test the manual trigger endpoint."""
        service = PersistentMatchListChangeDetectorService()
        client = TestClient(service.app)

        # Mock the executor
        mock_loop = Mock()
        mock_get_loop.return_value = mock_loop
        mock_loop.run_in_executor.return_value = asyncio.Future()
        mock_loop.run_in_executor.return_value.set_result(True)

        response = client.post("/trigger")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("message", data)

    def test_manual_trigger_when_not_running(self):
        """Test manual trigger when service is not running."""
        service = PersistentMatchListChangeDetectorService()
        service.running = False
        client = TestClient(service.app)

        response = client.post("/trigger")
        self.assertEqual(response.status_code, 503)

    @patch("persistent_service.asyncio.get_event_loop")
    async def test_execute_change_detection(self, mock_get_loop):
        """Test the change detection execution."""
        service = PersistentMatchListChangeDetectorService()

        # Mock the executor
        mock_loop = Mock()
        mock_get_loop.return_value = mock_loop
        future = asyncio.Future()
        future.set_result(True)
        mock_loop.run_in_executor.return_value = future

        initial_count = service.execution_count
        result = await service._execute_change_detection()

        self.assertTrue(result)
        self.assertEqual(service.execution_count, initial_count + 1)
        self.assertIsNotNone(service.last_execution)
        self.assertIsNotNone(service.next_execution)

    def test_cron_schedule_calculation(self):
        """Test cron schedule calculation."""
        service = PersistentMatchListChangeDetectorService()

        # Test that next execution is calculated correctly
        now = datetime.now()
        cron = croniter(service.cron_schedule, now)
        expected_next = cron.get_next(datetime)

        # Allow for small time differences
        time_diff = abs((service.next_execution - expected_next).total_seconds())
        self.assertLess(time_diff, 60)  # Within 1 minute

    def test_signal_handler(self):
        """Test signal handler for graceful shutdown."""
        service = PersistentMatchListChangeDetectorService()

        # Mock sys.exit to prevent actual exit
        with patch("persistent_service.sys.exit") as mock_exit:
            service._signal_handler(15, None)  # SIGTERM

            self.assertFalse(service.running)
            mock_exit.assert_called_once_with(0)

    def test_shutdown(self):
        """Test graceful shutdown."""
        service = PersistentMatchListChangeDetectorService()

        # Mock server and thread
        service._server = Mock()
        service.server_thread = Mock()
        service.server_thread.is_alive.return_value = True

        service.shutdown()

        self.assertFalse(service.running)
        self.assertTrue(service._server.should_exit)
        service.server_thread.join.assert_called_once_with(timeout=5)

    def test_oneshot_mode_configuration(self):
        """Test configuration for oneshot mode."""
        self.mock_config["RUN_MODE"] = "oneshot"
        service = PersistentMatchListChangeDetectorService()

        self.assertEqual(service.run_mode, "oneshot")

    def test_default_configuration_values(self):
        """Test default configuration values."""
        # Remove optional config values
        minimal_config = {"FOGIS_USERNAME": "test_user", "FOGIS_PASSWORD": "test_password"}
        self.mock_get_config.return_value = minimal_config

        service = PersistentMatchListChangeDetectorService()

        self.assertEqual(service.run_mode, "oneshot")  # Default
        self.assertEqual(service.cron_schedule, "0 * * * *")  # Default
        self.assertEqual(service.health_server_port, 8000)  # Default
        self.assertEqual(service.health_server_host, "0.0.0.0")  # Default (container-friendly)

    def test_environment_variable_integration(self):
        """Test integration with environment variables."""
        # Test that the service respects environment variables
        test_env = {
            "RUN_MODE": "service",
            "CRON_SCHEDULE": "*/30 * * * *",  # Every 30 minutes
            "HEALTH_SERVER_PORT": "9000",
            "HEALTH_SERVER_HOST": "localhost",
        }

        self.mock_get_config.return_value = test_env
        service = PersistentMatchListChangeDetectorService()

        self.assertEqual(service.run_mode, "service")
        self.assertEqual(service.cron_schedule, "*/30 * * * *")
        self.assertEqual(service.health_server_port, 9000)
        self.assertEqual(service.health_server_host, "localhost")


class TestPersistentServiceIntegration(unittest.TestCase):
    """Integration tests for the persistent service."""

    def setUp(self):
        """Set up integration test environment."""
        self.mock_config = {
            "RUN_MODE": "service",
            "CRON_SCHEDULE": "0 * * * *",
            "HEALTH_SERVER_PORT": "8002",  # Different port for integration tests
            "HEALTH_SERVER_HOST": "127.0.0.1",
            "FOGIS_USERNAME": "test_user",
            "FOGIS_PASSWORD": "test_password",
        }

        self.config_patcher = patch("persistent_service.get_config")
        self.mock_get_config = self.config_patcher.start()
        self.mock_get_config.return_value = self.mock_config

        self.logger_patcher = patch("persistent_service.get_logger")
        self.mock_get_logger = self.logger_patcher.start()
        self.mock_logger = Mock()
        self.mock_get_logger.return_value = self.mock_logger

    def tearDown(self):
        """Clean up after integration tests."""
        self.config_patcher.stop()
        self.logger_patcher.stop()

    def test_service_lifecycle(self):
        """Test complete service lifecycle."""
        service = PersistentMatchListChangeDetectorService()

        # Test initialization
        self.assertTrue(service.running)
        self.assertEqual(service.execution_count, 0)

        # Test shutdown
        service.shutdown()
        self.assertFalse(service.running)


if __name__ == "__main__":
    unittest.main()
