#!/usr/bin/env python3
"""
Tests for the security enhancements in the match list change detector.

Verifies that the security features work correctly.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Mock the imports that would cause issues
with patch("sys.modules", {"fogis_api_client": MagicMock()}):
    # Now import the modules to test
    try:
        from health_server import SECURITY_HEADERS, HealthServer

        HEALTH_SERVER_AVAILABLE = True
    except (ImportError, KeyError):
        # Mock for CI environments where health_server is not available
        SECURITY_HEADERS = {}

        class MockHealthServer:
            """Mock health server for CI environments."""

            def __init__(self, *args, **kwargs):
                """Initialize mock health server."""
                pass

        HealthServer = MockHealthServer
        HEALTH_SERVER_AVAILABLE = False
    from match_list_change_detector import (
        RateLimiter,
        get_executable_path,
        mask_sensitive_data,
        validate_file_path,
    )


class TestSecurityEnhancements(unittest.TestCase):
    """Test cases for the security enhancements."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        """Tear down test fixtures."""
        os.chdir(self.old_cwd)
        try:
            import shutil

            shutil.rmtree(self.test_dir)
        except Exception as e:
            print(f"Error cleaning up test directory: {e}")

    def test_validate_file_path_valid(self):
        """Test validating a valid file path."""
        # Create a test file
        test_file = os.path.join(self.test_dir, "test_file.txt")
        with open(test_file, "w") as f:
            f.write("test")

        # Validate the file path
        result = validate_file_path(test_file, must_exist=True)

        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result, Path(test_file).resolve())

    def test_validate_file_path_nonexistent(self):
        """Test validating a nonexistent file path."""
        # Validate a nonexistent file path
        result = validate_file_path("nonexistent_file.txt", must_exist=True)

        # Verify the result
        self.assertIsNone(result)

    def test_validate_file_path_create_dir(self):
        """Test validating a file path with directory creation."""
        # Validate a file path with directory creation
        test_file = os.path.join(self.test_dir, "new_dir", "test_file.txt")
        result = validate_file_path(test_file, create_dir=True)

        # Verify the result
        self.assertIsNotNone(result)
        self.assertTrue(os.path.exists(os.path.dirname(test_file)))

    def test_mask_sensitive_data(self):
        """Test masking sensitive data."""
        # Test with various inputs
        self.assertEqual(mask_sensitive_data("password123"), "********")
        self.assertEqual(mask_sensitive_data(""), "")
        self.assertEqual(mask_sensitive_data(None), None)

    @patch("match_list_change_detector.shutil.which")
    def test_get_executable_path_found(self, mock_which):
        """Test finding an executable path."""
        # Set up the mock
        mock_which.return_value = "/usr/bin/docker-compose"

        # Get the executable path
        result = get_executable_path("docker-compose")

        # Verify the result
        self.assertEqual(result, "/usr/bin/docker-compose")
        mock_which.assert_called_once_with("docker-compose")

    @patch("match_list_change_detector.shutil.which")
    def test_get_executable_path_not_found(self, mock_which):
        """Test finding an executable path that doesn't exist."""
        # Set up the mock
        mock_which.return_value = None

        # Get the executable path
        result = get_executable_path("nonexistent-command")

        # Verify the result
        self.assertIsNone(result)
        mock_which.assert_called_once_with("nonexistent-command")

    def test_rate_limiter_under_limit(self):
        """Test rate limiter when under the limit."""
        # Create a rate limiter with a high limit
        rate_limiter = RateLimiter(max_requests=10)

        # Make several requests
        for _ in range(5):
            result = rate_limiter.can_make_request()
            self.assertTrue(result)

        # Verify the number of timestamps
        self.assertEqual(len(rate_limiter.request_timestamps), 5)

    def test_rate_limiter_at_limit(self):
        """Test rate limiter when at the limit."""
        # Create a rate limiter with a low limit
        rate_limiter = RateLimiter(max_requests=3)

        # Make several requests
        for _ in range(3):
            result = rate_limiter.can_make_request()
            self.assertTrue(result)

        # Make one more request
        result = rate_limiter.can_make_request()
        self.assertFalse(result)

        # Verify the number of timestamps
        self.assertEqual(len(rate_limiter.request_timestamps), 3)

    def test_health_server_security_headers(self):
        """Test that the health server includes security headers."""
        # Verify that all required security headers are present
        required_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Content-Security-Policy",
            "Strict-Transport-Security",
            "Cache-Control",
        ]

        header_dict = dict(SECURITY_HEADERS)
        for header in required_headers:
            self.assertIn(header, header_dict)

    @patch("health_server.ssl.SSLContext")
    @patch("health_server.make_server")
    def test_health_server_https_config(self, mock_make_server, mock_ssl_context):
        """Test that the health server configures HTTPS correctly."""
        # Set up the mocks
        mock_server = MagicMock()
        mock_make_server.return_value = mock_server
        mock_context = MagicMock()
        mock_ssl_context.return_value = mock_context

        # Create a health server with HTTPS
        cert_file = os.path.join(self.test_dir, "cert.pem")
        key_file = os.path.join(self.test_dir, "key.pem")

        # Create dummy cert and key files
        with open(cert_file, "w") as f:
            f.write("dummy cert")
        with open(key_file, "w") as f:
            f.write("dummy key")

        # Create the server
        server = HealthServer(port=8000, use_https=True, cert_file=cert_file, key_file=key_file)

        # Start the server (this will run in a separate thread)
        server.start()

        # Stop the server
        server.stop()

        # Verify that HTTPS was configured
        self.assertTrue(server.use_https)


if __name__ == "__main__":
    unittest.main()
