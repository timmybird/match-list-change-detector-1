#!/usr/bin/env python3
"""
Tests for the main function of the match list change detector.

Verifies that the main function works correctly under various conditions.
"""

import unittest
from unittest.mock import MagicMock, patch

# Mock the imports that would cause issues
# Create a proper mock for fogis_api_client that supports context manager protocol
mock_fogis_api_client = MagicMock()
mock_client_instance = MagicMock()
mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
mock_client_instance.__exit__ = MagicMock(return_value=None)
mock_fogis_api_client.FogisApiClient.return_value = mock_client_instance

with patch("sys.modules", {"fogis_api_client": mock_fogis_api_client}):
    # Mock health_server to prevent import issues in CI
    with patch("match_list_change_detector.HealthServer", MagicMock()):
        # Now import the main function and module
        import match_list_change_detector
        from match_list_change_detector import main


class TestMain(unittest.TestCase):
    """Test cases for the main function."""

    def test_main_success(self):
        """Test the main function with successful execution."""
        # Set up the config mock by patching the config object directly
        with patch.object(match_list_change_detector, "config") as mock_config:
            mock_config.get.side_effect = lambda key, default=None: {
                "FOGIS_USERNAME": "test_user",
                "FOGIS_PASSWORD": "test_pass",
            }.get(key, default)

            # Set up the MatchListChangeDetector mock by patching it in the module
            with patch.object(
                match_list_change_detector, "MatchListChangeDetector"
            ) as mock_detector_class:
                mock_detector = MagicMock()
                mock_detector_class.return_value = mock_detector
                mock_detector.run.return_value = True

                # Run the main function
                result = main()

                # Verify the result
                self.assertTrue(result)
                mock_detector_class.assert_called_once_with("test_user", "test_pass")
                mock_detector.run.assert_called_once()

    def test_main_failure(self):
        """Test the main function with a failure."""
        # Set up the config mock by patching the config object directly
        with patch.object(match_list_change_detector, "config") as mock_config:
            mock_config.get.side_effect = lambda key, default=None: {
                "FOGIS_USERNAME": "test_user",
                "FOGIS_PASSWORD": "test_pass",
            }.get(key, default)

            # Set up the MatchListChangeDetector mock by patching it in the module
            with patch.object(
                match_list_change_detector, "MatchListChangeDetector"
            ) as mock_detector_class:
                mock_detector = MagicMock()
                mock_detector_class.return_value = mock_detector
                mock_detector.run.return_value = False

                # Run the main function
                result = main()

                # Verify the result
                self.assertFalse(result)

    def test_main_missing_credentials(self):
        """Test the main function with missing credentials."""
        # Set up the config mock to return empty credentials
        with patch.object(match_list_change_detector, "config") as mock_config:
            mock_config.get.side_effect = lambda key, default=None: {
                "FOGIS_USERNAME": "",
                "FOGIS_PASSWORD": "",
            }.get(key, default)

            # Run the main function
            result = main()

            # Verify the result
            self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
