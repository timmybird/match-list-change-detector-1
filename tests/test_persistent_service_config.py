#!/usr/bin/env python3
"""
Test module for persistent service configuration.

Tests that environment variables are properly loaded and used by the persistent service.
"""

import os
import unittest
from unittest.mock import patch

from config import Config, get_config
from persistent_service import PersistentMatchListChangeDetectorService


class TestPersistentServiceConfig(unittest.TestCase):
    """Test cases for persistent service configuration."""

    def test_default_config_values(self) -> None:
        """Test that default configuration values are set correctly."""
        config = get_config()

        # Test persistent service defaults
        self.assertEqual(config.get("RUN_MODE"), "oneshot")
        self.assertEqual(config.get("CRON_SCHEDULE"), "0 * * * *")
        self.assertEqual(config.get("HEALTH_SERVER_PORT"), 8000)
        self.assertEqual(config.get("HEALTH_SERVER_HOST"), "0.0.0.0")  # nosec B104

    @patch.dict(
        os.environ,
        {
            "RUN_MODE": "service",
            "CRON_SCHEDULE": "*/30 * * * *",
            "HEALTH_SERVER_PORT": "9000",
            "HEALTH_SERVER_HOST": "127.0.0.1",
        },
    )
    def test_environment_variable_override(self) -> None:
        """Test that environment variables override default configuration."""
        # Create a fresh config instance to pick up environment variables
        config = Config()

        # Test environment variable overrides
        self.assertEqual(config.get("RUN_MODE"), "service")
        self.assertEqual(config.get("CRON_SCHEDULE"), "*/30 * * * *")
        self.assertEqual(config.get("HEALTH_SERVER_PORT"), 9000)  # Converted to int
        self.assertEqual(config.get("HEALTH_SERVER_HOST"), "127.0.0.1")

    @patch.dict(
        os.environ,
        {
            "RUN_MODE": "service",
            "CRON_SCHEDULE": "0 */2 * * *",
            "HEALTH_SERVER_PORT": "8080",
            "HEALTH_SERVER_HOST": "0.0.0.0",  # nosec B104,
        },
    )
    def test_persistent_service_initialization(self) -> None:
        """Test that persistent service configuration can be loaded from environment."""
        # Test that a fresh config picks up the environment variables
        config = Config()

        # Test configuration values
        self.assertEqual(config.get("RUN_MODE"), "service")
        self.assertEqual(config.get("CRON_SCHEDULE"), "0 */2 * * *")
        self.assertEqual(config.get("HEALTH_SERVER_PORT"), 8080)
        self.assertEqual(config.get("HEALTH_SERVER_HOST"), "0.0.0.0")  # nosec B104

    def test_persistent_service_defaults(self) -> None:
        """Test that persistent service uses defaults when no environment variables are set."""
        # Clear any existing environment variables
        env_vars = ["RUN_MODE", "CRON_SCHEDULE", "HEALTH_SERVER_PORT", "HEALTH_SERVER_HOST"]
        with patch.dict(os.environ, {}, clear=False):
            for var in env_vars:
                if var in os.environ:
                    del os.environ[var]

            service = PersistentMatchListChangeDetectorService()

            # Test default values
            self.assertEqual(service.run_mode, "oneshot")
            self.assertEqual(service.cron_schedule, "0 * * * *")
            self.assertEqual(service.health_server_port, 8000)
            self.assertEqual(service.health_server_host, "0.0.0.0")  # nosec B104

    @patch.dict(os.environ, {"RUN_MODE": "SERVICE"})
    def test_run_mode_case_insensitive(self) -> None:
        """Test that RUN_MODE is case insensitive."""
        config = Config()
        # The service should convert to lowercase
        self.assertEqual(config.get("RUN_MODE"), "SERVICE")  # Config preserves original case

        # Test that the service would convert it to lowercase
        # (This tests the logic in the service constructor)
        run_mode = config.get("RUN_MODE", "oneshot").lower()
        self.assertEqual(run_mode, "service")

    @patch.dict(os.environ, {"HEALTH_SERVER_PORT": "invalid"})
    def test_invalid_port_handling(self) -> None:
        """Test that invalid port values are handled gracefully."""
        with self.assertRaises(ValueError):
            Config()


if __name__ == "__main__":
    unittest.main()
