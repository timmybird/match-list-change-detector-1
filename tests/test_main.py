#!/usr/bin/env python3

import unittest
from unittest.mock import patch, MagicMock

# Import the main function
from match_list_change_detector import main


class TestMain(unittest.TestCase):
    """Test cases for the main function."""

    @patch('match_list_change_detector.FOGIS_USERNAME', 'test_user')
    @patch('match_list_change_detector.FOGIS_PASSWORD', 'test_pass')
    @patch('match_list_change_detector.MatchListChangeDetector')
    def test_main_success(self, mock_detector_class):
        """Test the main function with successful execution."""
        # Set up the mock
        mock_detector = MagicMock()
        mock_detector_class.return_value = mock_detector
        mock_detector.run.return_value = True

        # Run the main function
        result = main()

        # Verify the result
        self.assertTrue(result)
        mock_detector_class.assert_called_once_with('test_user', 'test_pass')
        mock_detector.run.assert_called_once()

    @patch('match_list_change_detector.FOGIS_USERNAME', 'test_user')
    @patch('match_list_change_detector.FOGIS_PASSWORD', 'test_pass')
    @patch('match_list_change_detector.MatchListChangeDetector')
    def test_main_failure(self, mock_detector_class):
        """Test the main function with a failure."""
        # Set up the mock
        mock_detector = MagicMock()
        mock_detector_class.return_value = mock_detector
        mock_detector.run.return_value = False

        # Run the main function
        result = main()

        # Verify the result
        self.assertFalse(result)

    @patch('match_list_change_detector.FOGIS_USERNAME', '')
    @patch('match_list_change_detector.FOGIS_PASSWORD', '')
    def test_main_missing_credentials(self):
        """Test the main function with missing credentials."""
        # Run the main function
        result = main()

        # Verify the result
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
