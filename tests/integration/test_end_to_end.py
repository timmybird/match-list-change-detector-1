#!/usr/bin/env python3
"""
End-to-end integration tests for the match list change detector.

These tests verify the complete workflow from API calls to file operations.
"""

import os
import tempfile
import unittest
from unittest.mock import patch

from tests.test_utils import create_sample_match_data, setup_module_mocks, with_isolated_imports


class TestEndToEndIntegration(unittest.TestCase):
    """End-to-end integration test cases."""

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
    def test_complete_change_detection_workflow(self):
        """Test the complete change detection workflow."""
        from match_list_change_detector import PREVIOUS_MATCHES_FILE, MatchListChangeDetector

        # Create detector
        detector = MatchListChangeDetector("test_user", "test_pass")

        # Mock the API client to return sample matches
        detector.api_client.fetch_matches_list_json.return_value = [self.sample_match]

        # Step 1: First run (no previous matches)
        detector.load_previous_matches()  # Should return False (no file)
        self.assertEqual(len(detector.previous_matches), 0)

        # Mock fetch_current_matches to succeed
        with patch.object(detector, "fetch_current_matches", return_value=True):
            detector.current_matches = [self.sample_match]

            # Detect changes
            has_changes, changes = detector.detect_changes()
            self.assertTrue(has_changes)
            self.assertEqual(changes["new_matches"], 1)

            # Save current matches
            result = detector.save_current_matches()
            self.assertTrue(result)
            self.assertTrue(os.path.exists(PREVIOUS_MATCHES_FILE))

        # Step 2: Second run (with previous matches, no changes)
        detector2 = MatchListChangeDetector("test_user", "test_pass")
        detector2.api_client.fetch_matches_list_json.return_value = [self.sample_match]

        detector2.load_previous_matches()  # Should return True (file exists)
        self.assertEqual(len(detector2.previous_matches), 1)

        with patch.object(detector2, "fetch_current_matches", return_value=True):
            detector2.current_matches = [self.sample_match]

            # Detect changes
            has_changes, changes = detector2.detect_changes()
            self.assertFalse(has_changes)
            self.assertEqual(changes["new_matches"], 0)
            self.assertEqual(changes["changed_matches"], 0)

    @with_isolated_imports
    def test_match_time_change_detection(self):
        """Test detection of match time changes."""
        from match_list_change_detector import MatchListChangeDetector

        detector = MatchListChangeDetector("test_user", "test_pass")

        # Set up previous match
        detector.previous_matches = [self.sample_match]

        # Create current match with different time
        current_match = self.sample_match.copy()
        current_match["avsparkstid"] = "15:00"  # Changed from 14:00
        detector.current_matches = [current_match]

        # Detect changes
        has_changes, changes = detector.detect_changes()

        # Verify time change was detected
        self.assertTrue(has_changes)
        self.assertEqual(changes["changed_matches"], 1)
        self.assertEqual(len(changes["changed_match_details"]), 1)

        change_detail = changes["changed_match_details"][0]
        self.assertEqual(change_detail["previous"]["time"], "14:00")
        self.assertEqual(change_detail["current"]["time"], "15:00")
        self.assertTrue(change_detail["changes"]["basic"])

    @with_isolated_imports
    def test_match_venue_change_detection(self):
        """Test detection of match venue changes."""
        from match_list_change_detector import MatchListChangeDetector

        detector = MatchListChangeDetector("test_user", "test_pass")

        # Set up previous match
        detector.previous_matches = [self.sample_match]

        # Create current match with different venue
        current_match = self.sample_match.copy()
        current_match["anlaggningnamn"] = "New Stadium"
        detector.current_matches = [current_match]

        # Detect changes
        has_changes, changes = detector.detect_changes()

        # Verify venue change was detected
        self.assertTrue(has_changes)
        self.assertEqual(changes["changed_matches"], 1)

        change_detail = changes["changed_match_details"][0]
        self.assertEqual(change_detail["previous"]["venue"], "Kongevi 1 Konstgräs")
        self.assertEqual(change_detail["current"]["venue"], "New Stadium")

    @with_isolated_imports
    def test_referee_assignment_change_detection(self):
        """Test detection of referee assignment changes."""
        from match_list_change_detector import MatchListChangeDetector

        detector = MatchListChangeDetector("test_user", "test_pass")

        # Set up previous match
        detector.previous_matches = [self.sample_match]

        # Create current match with different referee
        current_match = self.sample_match.copy()
        current_match["domaruppdraglista"] = [
            {
                "domareid": 7700,  # Different referee ID
                "personnamn": "Another Referee",
                "domarrollnamn": "Huvuddomare",
                "epostadress": "another@example.com",
                "mobiltelefon": "1234567890",
            }
        ]
        detector.current_matches = [current_match]

        # Detect changes
        has_changes, changes = detector.detect_changes()

        # Verify referee change was detected
        self.assertTrue(has_changes)
        self.assertEqual(changes["changed_matches"], 1)

        change_detail = changes["changed_match_details"][0]
        self.assertTrue(change_detail["changes"]["referees"])

    @with_isolated_imports
    def test_multiple_matches_with_mixed_changes(self):
        """Test handling of multiple matches with various types of changes."""
        from match_list_change_detector import MatchListChangeDetector

        detector = MatchListChangeDetector("test_user", "test_pass")

        # Create multiple previous matches
        match1 = self.sample_match.copy()
        match2 = self.sample_match.copy()
        match2["matchid"] = 6169106
        match2["matchnr"] = "000024033"

        detector.previous_matches = [match1, match2]

        # Create current matches with changes
        current_match1 = match1.copy()
        current_match1["avsparkstid"] = "15:00"  # Time change

        # match2 is removed (not in current matches)

        # New match added
        new_match = self.sample_match.copy()
        new_match["matchid"] = 6169107
        new_match["matchnr"] = "000024034"

        detector.current_matches = [current_match1, new_match]

        # Detect changes
        has_changes, changes = detector.detect_changes()

        # Verify all types of changes were detected
        self.assertTrue(has_changes)
        self.assertEqual(changes["new_matches"], 1)  # new_match added
        self.assertEqual(changes["removed_matches"], 1)  # match2 removed
        self.assertEqual(changes["changed_matches"], 1)  # match1 time changed


if __name__ == "__main__":
    unittest.main()
