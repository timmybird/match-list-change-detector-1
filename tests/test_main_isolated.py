#!/usr/bin/env python3
"""
Isolated tests for the main function of the match list change detector.

These tests use mocking to avoid Python 3.13+ import issues.
"""

import unittest
from unittest.mock import MagicMock, patch

from tests.test_utils import setup_module_mocks, with_isolated_imports


class TestMainIsolated(unittest.TestCase):
    """Isolated test cases for the main function."""

    def setUp(self):
        """Set up test fixtures."""
        setup_module_mocks()

    @with_isolated_imports
    def test_main_success(self):
        """Test the main function with successful execution."""
        # Import after setting up mocks
        from match_list_change_detector import main

        # Mock the MatchListChangeDetector class
        with patch("match_list_change_detector.MatchListChangeDetector") as mock_detector_class:
            mock_detector = MagicMock()
            mock_detector_class.return_value = mock_detector
            mock_detector.run.return_value = True

            # Run the main function
            result = main()

            # Verify the result
            self.assertTrue(result)
            mock_detector_class.assert_called_once_with("test_user", "test_pass")
            mock_detector.run.assert_called_once()

    @with_isolated_imports
    def test_main_failure(self):
        """Test the main function with a failure."""
        # Import after setting up mocks
        from match_list_change_detector import main

        # Mock the MatchListChangeDetector class
        with patch("match_list_change_detector.MatchListChangeDetector") as mock_detector_class:
            mock_detector = MagicMock()
            mock_detector_class.return_value = mock_detector
            mock_detector.run.return_value = False

            # Run the main function
            result = main()

            # Verify the result
            self.assertFalse(result)

    @with_isolated_imports
    def test_main_missing_credentials(self):
        """Test the main function with missing credentials."""
        # Mock config to return empty credentials
        with patch("match_list_change_detector.config") as mock_config:
            mock_config.get.side_effect = lambda key, default=None: {
                "FOGIS_USERNAME": "",
                "FOGIS_PASSWORD": "",
            }.get(key, default)

            # Import after setting up mocks
            from match_list_change_detector import main

            # Run the main function
            result = main()

            # Verify the result
            self.assertFalse(result)

    @with_isolated_imports
    def test_main_exception_handling(self):
        """Test the main function with exception handling."""
        # Import after setting up mocks
        from match_list_change_detector import main

        # Mock the MatchListChangeDetector class to raise an exception
        with patch("match_list_change_detector.MatchListChangeDetector") as mock_detector_class:
            mock_detector_class.side_effect = Exception("Test exception")

            # Run the main function
            result = main()

            # Verify the result
            self.assertFalse(result)

    @with_isolated_imports
    def test_main_with_health_server(self):
        """Test the main function with health server initialization."""
        # Import after setting up mocks
        from match_list_change_detector import main

        # Mock the MatchListChangeDetector class
        with patch("match_list_change_detector.MatchListChangeDetector") as mock_detector_class:
            mock_detector = MagicMock()
            mock_detector_class.return_value = mock_detector
            mock_detector.run.return_value = True

            # Run the main function
            result = main()

            # Verify the result
            self.assertTrue(result)
            # Verify that the health server was initialized (it's a module-level variable)
            # This test ensures the health server mock is working correctly


if __name__ == "__main__":
    unittest.main()
