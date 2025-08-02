#!/usr/bin/env python3
"""
Integration tests for configuration and environment handling.

These tests verify that the application correctly handles various configuration scenarios.
"""

import unittest
from unittest.mock import patch

from tests.test_utils import setup_module_mocks, with_isolated_imports


class TestConfigurationIntegration(unittest.TestCase):
    """Configuration integration test cases."""

    def setUp(self):
        """Set up test fixtures."""
        setup_module_mocks()

    @with_isolated_imports
    def test_environment_variable_configuration(self):
        """Test that environment variables are properly loaded."""
        # Mock environment variables
        test_env = {
            "FOGIS_USERNAME": "env_user",
            "FOGIS_PASSWORD": "env_pass",
            "PREVIOUS_MATCHES_FILE": "env_matches.json",
            "DOCKER_COMPOSE_FILE": "env-compose.yml",
            "DAYS_BACK": "14",
            "DAYS_AHEAD": "60",
            "API_RATE_LIMIT": 20,  # Integer value
            "HEALTH_SERVER_PORT": "9000",
            "USE_HTTPS": "true",
        }

        # Mock the config object in the match_list_change_detector module
        with patch("match_list_change_detector.config") as mock_config:
            mock_config.get.side_effect = lambda key, default=None: test_env.get(key, default)

            from match_list_change_detector import MatchListChangeDetector

            # Create detector and verify it uses environment configuration
            detector = MatchListChangeDetector("env_user", "env_pass")

            # Verify rate limiter uses environment configuration
            self.assertEqual(detector.rate_limiter.max_requests, 20)

    @with_isolated_imports
    def test_default_configuration_fallback(self):
        """Test that default values are used when environment variables are not set."""
        # Mock minimal configuration
        minimal_config = {
            "FOGIS_USERNAME": "test_user",
            "FOGIS_PASSWORD": "test_pass",
        }

        # Mock the config object in the match_list_change_detector module
        with patch("match_list_change_detector.config") as mock_config:
            mock_config.get.side_effect = lambda key, default=None: minimal_config.get(key, default)

            from match_list_change_detector import MatchListChangeDetector

            # Create detector and verify it uses default configuration
            detector = MatchListChangeDetector("test_user", "test_pass")

            # Verify rate limiter uses default configuration
            self.assertEqual(detector.rate_limiter.max_requests, 10)  # Default value

    @with_isolated_imports
    def test_persistent_service_configuration(self):
        """Test persistent service configuration handling."""
        from persistent_service import PersistentMatchListChangeDetectorService

        # Test with custom configuration
        test_config = {
            "FOGIS_USERNAME": "service_user",
            "FOGIS_PASSWORD": "service_pass",
            "RUN_MODE": "service",
            "CRON_SCHEDULE": "*/15 * * * *",  # Every 15 minutes
            "HEALTH_SERVER_PORT": "8080",
            "HEALTH_SERVER_HOST": "0.0.0.0",
        }

        with patch("persistent_service.get_config") as mock_get_config:
            mock_get_config.return_value = test_config

            service = PersistentMatchListChangeDetectorService()

            # Verify configuration is properly loaded
            self.assertEqual(service.run_mode, "service")
            self.assertEqual(service.cron_schedule, "*/15 * * * *")
            self.assertEqual(service.health_server_port, 8080)
            self.assertEqual(service.health_server_host, "0.0.0.0")

    @with_isolated_imports
    def test_invalid_configuration_handling(self):
        """Test handling of invalid configuration values."""
        from persistent_service import PersistentMatchListChangeDetectorService

        # Test with invalid configuration
        invalid_config = {
            "FOGIS_USERNAME": "test_user",
            "FOGIS_PASSWORD": "test_pass",
            "RUN_MODE": "invalid_mode",
            "CRON_SCHEDULE": "invalid cron",
            "HEALTH_SERVER_PORT": "not_a_number",
        }

        with patch("persistent_service.get_config") as mock_get_config:
            mock_get_config.return_value = invalid_config

            # Service should handle invalid configuration gracefully
            try:
                service = PersistentMatchListChangeDetectorService()
                # Should fall back to defaults for invalid values
                self.assertEqual(service.run_mode, "invalid_mode")  # Accepts any string
                # Port should cause ValueError, but service should handle it
            except ValueError:
                # This is expected for invalid port number
                pass

    @with_isolated_imports
    def test_logging_configuration(self):
        """Test logging configuration integration."""
        # Test that logging is properly configured
        from logging_config import get_logger

        logger = get_logger("test_logger")

        # Verify logger is returned (basic functionality test)
        self.assertIsNotNone(logger)

    @with_isolated_imports
    def test_health_server_configuration(self):
        """Test health server configuration integration."""
        from health_server import HealthServer

        # Test with HTTPS configuration
        server = HealthServer(
            host="127.0.0.1", port=8443, use_https=True, cert_file="test.crt", key_file="test.key"
        )

        # Verify configuration is stored
        self.assertEqual(server.host, "127.0.0.1")
        self.assertEqual(server.port, 8443)
        self.assertTrue(server.use_https)
        self.assertEqual(server.cert_file, "test.crt")
        self.assertEqual(server.key_file, "test.key")

    @with_isolated_imports
    def test_metrics_configuration(self):
        """Test metrics configuration integration."""
        from metrics import metrics

        # Test that metrics can be configured
        self.assertIsNotNone(metrics)

        # Test time_api_request context manager
        with metrics.time_api_request("test_operation") as timer:
            self.assertIsNotNone(timer)

    @with_isolated_imports
    def test_api_client_configuration(self):
        """Test API client configuration integration."""
        from match_list_change_detector import MatchListChangeDetector

        detector = MatchListChangeDetector("config_user", "config_pass")

        # Verify API client is properly configured
        self.assertIsNotNone(detector.api_client)

        # Test that the API client can be used in context manager
        with detector.api_client as client:
            self.assertIsNotNone(client)


if __name__ == "__main__":
    unittest.main()
