#!/usr/bin/env python3
"""
Test utilities for the match list change detector tests.

Provides common mocking utilities and test fixtures to avoid import issues.
"""

import sys
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock


class MockFogisApiClient:
    """Mock implementation of FogisApiClient for testing."""

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.logged_in = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def login(self):
        """Mock login method."""
        self.logged_in = True

    def fetch_matches_list_json(self) -> List[Dict[str, Any]]:
        """Mock fetch matches method."""
        return []


class MockHealthServer:
    """Mock implementation of HealthServer for testing."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8000,
        use_https: bool = False,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
    ):
        self.host = host
        self.port = port
        self.use_https = use_https
        self.cert_file = cert_file
        self.key_file = key_file
        self.running = False

    def start(self):
        """Mock start method."""
        self.running = True

    def stop(self):
        """Mock stop method."""
        self.running = False


class MockMetrics:
    """Mock implementation of metrics for testing."""

    def time_api_request(self, operation: str):
        """Mock time_api_request context manager."""
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_cm)
        mock_cm.__exit__ = MagicMock(return_value=None)
        return mock_cm


def setup_module_mocks():
    """Set up module-level mocks to avoid import issues."""
    # Mock fogis_api_client module
    mock_fogis_module = MagicMock()
    mock_fogis_module.FogisApiClient = MockFogisApiClient
    mock_fogis_module.MatchListFilter = MagicMock()
    sys.modules["fogis_api_client"] = mock_fogis_module

    # Mock health_server module
    mock_health_module = MagicMock()
    mock_health_module.HealthServer = MockHealthServer
    sys.modules["health_server"] = mock_health_module

    # Mock metrics module
    mock_metrics_module = MagicMock()
    mock_metrics_module.metrics = MockMetrics()
    sys.modules["metrics"] = mock_metrics_module

    # Mock logging_config module
    mock_logging_config = MagicMock()
    mock_logger = MagicMock()
    mock_logging_config.get_logger.return_value = mock_logger
    sys.modules["logging_config"] = mock_logging_config

    # Mock config module
    mock_config_module = MagicMock()
    mock_config = MagicMock()
    mock_config.get.side_effect = lambda key, default=None: {
        "FOGIS_USERNAME": "test_user",
        "FOGIS_PASSWORD": "test_pass",
        "PREVIOUS_MATCHES_FILE": "previous_matches.json",
        "DOCKER_COMPOSE_FILE": "docker-compose.yml",
        "DAYS_BACK": 7,
        "DAYS_AHEAD": 30,
        "API_RATE_LIMIT": 10,
        "HEALTH_SERVER_PORT": 8000,
        "USE_HTTPS": False,
    }.get(key, default)
    mock_config_module.get_config.return_value = mock_config
    sys.modules["config"] = mock_config_module


def create_sample_match_data() -> Dict[str, Any]:
    """Create sample match data for testing."""
    return {
        "matchid": 6169105,
        "matchnr": "000024032",
        "speldatum": "2025-04-26",
        "avsparkstid": "14:00",
        "lag1lagid": 25650,
        "lag1namn": "IK Kongahälla",
        "lag2lagid": 25529,
        "lag2namn": "Motala AIF FK",
        "anlaggningnamn": "Kongevi 1 Konstgräs",
        "installd": False,
        "avbruten": False,
        "uppskjuten": False,
        "domaruppdraglista": [
            {
                "domareid": 6600,
                "personnamn": "Bartek Svaberg",
                "domarrollnamn": "Huvuddomare",
                "epostadress": "bartek.svaberg@gmail.com",
                "mobiltelefon": "0709423055",
            }
        ],
    }


class IsolatedTestCase:
    """Base class for isolated test cases that avoid problematic imports."""

    def setUp(self):
        """Set up test fixtures."""
        setup_module_mocks()
        self.sample_match = create_sample_match_data()

    def tearDown(self):
        """Clean up after tests."""
        # Remove mocked modules
        modules_to_remove = [
            "fogis_api_client",
            "health_server",
            "metrics",
            "logging_config",
            "config",
        ]
        for module in modules_to_remove:
            if module in sys.modules:
                del sys.modules[module]


def with_isolated_imports(test_func):
    """Decorator to run tests with isolated imports."""

    def wrapper(*args, **kwargs):
        setup_module_mocks()
        try:
            return test_func(*args, **kwargs)
        finally:
            # Clean up mocked modules
            modules_to_remove = [
                "fogis_api_client",
                "health_server",
                "metrics",
                "logging_config",
                "config",
            ]
            for module in modules_to_remove:
                if module in sys.modules:
                    del sys.modules[module]

    return wrapper
