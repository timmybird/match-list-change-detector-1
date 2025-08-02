#!/usr/bin/env python3
"""
Isolated tests for the MatchListChangeDetector class.

These tests use mocking to avoid Python 3.13+ import issues.
"""

import json
import os
import tempfile
import unittest

from tests.test_utils import create_sample_match_data, setup_module_mocks, with_isolated_imports


class TestMatchListChangeDetectorIsolated(unittest.TestCase):
    """Isolated test cases for the MatchListChangeDetector class."""

    def setUp(self):
        """Set up test fixtures."""
        setup_module_mocks()
        self.sample_match = create_sample_match_data()

        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        """Clean up after each test."""
        # Clean up test directory
        os.chdir(self.old_cwd)
        import shutil

        shutil.rmtree(self.test_dir)

    @with_isolated_imports
    def test_detector_initialization(self):
        """Test MatchListChangeDetector initialization."""
        from match_list_change_detector import MatchListChangeDetector

        detector = MatchListChangeDetector("test_user", "test_pass")

        # Check that the detector has the expected attributes
        self.assertIsNotNone(detector.api_client)
        self.assertEqual(detector.previous_matches, [])
        self.assertEqual(detector.current_matches, [])
        self.assertIsNotNone(detector.rate_limiter)

    @with_isolated_imports
    def test_load_previous_matches_file_exists(self):
        """Test loading previous matches when the file exists."""
        from match_list_change_detector import PREVIOUS_MATCHES_FILE, MatchListChangeDetector

        # Create a sample previous matches file
        sample_matches = [self.sample_match]
        with open(PREVIOUS_MATCHES_FILE, "w") as f:
            json.dump(sample_matches, f)

        detector = MatchListChangeDetector("test_user", "test_pass")
        result = detector.load_previous_matches()

        # Verify the result
        self.assertTrue(result)
        self.assertEqual(len(detector.previous_matches), 1)
        self.assertEqual(detector.previous_matches[0]["matchid"], 6169105)

    @with_isolated_imports
    def test_load_previous_matches_file_not_exists(self):
        """Test loading previous matches when the file doesn't exist."""
        from match_list_change_detector import PREVIOUS_MATCHES_FILE, MatchListChangeDetector

        # Make sure the file doesn't exist
        if os.path.exists(PREVIOUS_MATCHES_FILE):
            os.remove(PREVIOUS_MATCHES_FILE)

        detector = MatchListChangeDetector("test_user", "test_pass")
        result = detector.load_previous_matches()

        # Verify the result
        self.assertFalse(result)
        self.assertEqual(len(detector.previous_matches), 0)

    @with_isolated_imports
    def test_save_current_matches(self):
        """Test saving current matches to file."""
        from match_list_change_detector import PREVIOUS_MATCHES_FILE, MatchListChangeDetector

        detector = MatchListChangeDetector("test_user", "test_pass")
        detector.current_matches = [self.sample_match]

        result = detector.save_current_matches()

        # Verify the result
        self.assertTrue(result)
        self.assertTrue(os.path.exists(PREVIOUS_MATCHES_FILE))

        # Verify the file contents
        with open(PREVIOUS_MATCHES_FILE, "r") as f:
            saved_matches = json.load(f)
        self.assertEqual(len(saved_matches), 1)
        self.assertEqual(saved_matches[0]["matchid"], 6169105)

    @with_isolated_imports
    def test_detect_changes_no_previous_matches(self):
        """Test detecting changes when there are no previous matches."""
        from match_list_change_detector import MatchListChangeDetector

        detector = MatchListChangeDetector("test_user", "test_pass")
        detector.previous_matches = []
        detector.current_matches = [self.sample_match]

        has_changes, changes = detector.detect_changes()

        # Verify the result
        self.assertTrue(has_changes)
        self.assertEqual(changes["new_matches"], 1)
        self.assertIn("message", changes)

    @with_isolated_imports
    def test_detect_changes_new_match(self):
        """Test detecting a new match."""
        from match_list_change_detector import MatchListChangeDetector

        detector = MatchListChangeDetector("test_user", "test_pass")

        # Add a previous match with a different ID
        prev_match = self.sample_match.copy()
        prev_match["matchid"] = 6169106
        detector.previous_matches = [prev_match]
        detector.current_matches = [self.sample_match]

        has_changes, changes = detector.detect_changes()

        # Verify the result
        self.assertTrue(has_changes)
        self.assertEqual(changes["new_matches"], 1)
        self.assertEqual(changes["removed_matches"], 1)
        self.assertEqual(len(changes["new_match_details"]), 1)
        self.assertEqual(len(changes["removed_match_details"]), 1)

    @with_isolated_imports
    def test_detect_changes_no_changes(self):
        """Test detecting no changes."""
        from match_list_change_detector import MatchListChangeDetector

        detector = MatchListChangeDetector("test_user", "test_pass")
        detector.previous_matches = [self.sample_match]
        detector.current_matches = [self.sample_match]

        has_changes, changes = detector.detect_changes()

        # Verify the result
        self.assertFalse(has_changes)
        self.assertEqual(changes["new_matches"], 0)
        self.assertEqual(changes["removed_matches"], 0)
        self.assertEqual(changes["changed_matches"], 0)

    @with_isolated_imports
    def test_detect_changes_time_change(self):
        """Test detecting a change in match time."""
        from match_list_change_detector import MatchListChangeDetector

        detector = MatchListChangeDetector("test_user", "test_pass")
        detector.previous_matches = [self.sample_match]

        # Create a current match with a different time
        current_match = self.sample_match.copy()
        current_match["avsparkstid"] = "15:00"
        detector.current_matches = [current_match]

        has_changes, changes = detector.detect_changes()

        # Verify the result
        self.assertTrue(has_changes)
        self.assertEqual(changes["new_matches"], 0)
        self.assertEqual(changes["removed_matches"], 0)
        self.assertEqual(changes["changed_matches"], 1)
        self.assertEqual(len(changes["changed_match_details"]), 1)


if __name__ == "__main__":
    unittest.main()
