#!/usr/bin/env python3
"""
Tests for the main function of the match list change detector.

Verifies that the main function works correctly under various conditions.
"""

import unittest
from unittest.mock import MagicMock, patch

# Mock the imports that would cause issues
with patch("sys.modules", {"fogis_api_client": MagicMock()}):
    # Mock health_server to prevent import issues in CI
    with patch("match_list_change_detector.HealthServer", MagicMock()):
        # Now import the main function
        from match_list_change_detector import main


class TestMain(unittest.TestCase):
    """Test cases for the main function."""

    @patch("match_list_change_detector.config.get")
    @patch("match_list_change_detector.MatchListChangeDetector")
    def test_main_success(self, mock_detector_class, mock_config_get):
        """Test the main function with successful execution."""
        # Set up the config mock
        mock_config_get.side_effect = lambda key, default=None: {
            "FOGIS_USERNAME": "test_user",
            "FOGIS_PASSWORD": "test_pass",
        }.get(key, default)
        # Set up the mock
        mock_detector = MagicMock()
        mock_detector_class.return_value = mock_detector
        mock_detector.run.return_value = True

        # Run the main function
        result = main()

        # Verify the result
        self.assertTrue(result)
        mock_detector_class.assert_called_once_with("test_user", "test_pass")
        mock_detector.run.assert_called_once()

    @patch("match_list_change_detector.config.get")
    @patch("match_list_change_detector.MatchListChangeDetector")
    def test_main_failure(self, mock_detector_class, mock_config_get):
        """Test the main function with a failure."""
        # Set up the config mock
        mock_config_get.side_effect = lambda key, default=None: {
            "FOGIS_USERNAME": "test_user",
            "FOGIS_PASSWORD": "test_pass",
        }.get(key, default)
        # Set up the mock
        mock_detector = MagicMock()
        mock_detector_class.return_value = mock_detector
        mock_detector.run.return_value = False

        # Run the main function
        result = main()

        # Verify the result
        self.assertFalse(result)

    @patch("match_list_change_detector.config.get")
    def test_main_missing_credentials(self, mock_config_get):
        """Test the main function with missing credentials."""
        # Set up the config mock to return empty credentials
        mock_config_get.side_effect = lambda key, default=None: {
            "FOGIS_USERNAME": "",
            "FOGIS_PASSWORD": "",
        }.get(key, default)
        # Run the main function
        result = main()

        # Verify the result
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
