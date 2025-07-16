#!/usr/bin/env python3
"""
Configuration module for the match list change detector.

Provides functions to load and access configuration from environment variables.
"""

import os
from typing import Any, Dict

# Default configuration
DEFAULT_CONFIG = {
    # API credentials
    "FOGIS_USERNAME": "",
    "FOGIS_PASSWORD": "",
    # Match list configuration
    "DAYS_BACK": 7,
    "DAYS_AHEAD": 365,
    # File paths
    "PREVIOUS_MATCHES_FILE": "previous_matches.json",
    "DOCKER_COMPOSE_FILE": "../MatchListProcessor/docker-compose.yml",
    # Logging configuration
    "LOG_LEVEL": "INFO",
    "LOG_DIR": "logs",
    "LOG_FILE": "match_list_change_detector.log",
    # Docker configuration
    "CONTAINER_NETWORK": "fogis-network",
    # Timezone
    "TZ": "Europe/Stockholm",
    # Security configuration
    "USE_HTTPS": False,
    "SSL_CERT_FILE": "certs/server.crt",
    "SSL_KEY_FILE": "certs/server.key",
    "HEALTH_SERVER_PORT": 8000,
    "HEALTH_SERVER_HOST": "0.0.0.0",  # nosec B104
    "METRICS_SERVER_PORT": 8001,
    # Rate limiting
    "API_RATE_LIMIT": 10,  # Maximum number of API requests per minute
    # Persistent service mode configuration
    "RUN_MODE": "oneshot",
    "CRON_SCHEDULE": "0 * * * *",
    "WEBHOOK_URL": "",
}


class Config:
    """Configuration manager for the application."""

    def __init__(self, env_prefix: str = ""):
        """
        Initialize the configuration manager.

        Args:
            env_prefix: Prefix for environment variables
        """
        self.env_prefix = env_prefix
        self._config = DEFAULT_CONFIG.copy()
        self._load_from_env()

    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        for key in self._config:
            env_key = f"{self.env_prefix}{key}" if self.env_prefix else key
            env_value = os.environ.get(env_key)

            if env_value is not None:
                # Convert to the appropriate type based on the default value
                default_value = self._config[key]
                if isinstance(default_value, bool):
                    self._config[key] = env_value.lower() in ("true", "yes", "1")
                elif isinstance(default_value, int):
                    self._config[key] = int(env_value)
                elif isinstance(default_value, float):
                    self._config[key] = float(env_value)
                else:
                    self._config[key] = env_value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key is not found

        Returns:
            Configuration value
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            key: Configuration key
            value: Configuration value
        """
        self._config[key] = value

    def as_dict(self) -> Dict[str, Any]:
        """
        Get the configuration as a dictionary.

        Returns:
            Configuration dictionary
        """
        return self._config.copy()


# Create a global configuration instance
config = Config()


def get_config() -> Config:
    """
    Get the global configuration instance.

    Returns:
        Configuration instance
    """
    return config
