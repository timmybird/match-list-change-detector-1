#!/usr/bin/env python3
"""
Test script for the match list change detector.

Allows manual testing of the change detector functionality.
"""

import json

from config import get_config
from logging_config import get_logger
from match_list_change_detector import MatchListChangeDetector

# Get logger
logger = get_logger("test_change_detector")

config = get_config()

# Get credentials from configuration
username = config.get("FOGIS_USERNAME")
password = config.get("FOGIS_PASSWORD")

if not username or not password:
    logger.error("FOGIS_USERNAME and FOGIS_PASSWORD must be set in configuration")
    exit(1)

# Create a test detector
detector = MatchListChangeDetector(username, password)

# Test fetching matches
logger.info("Testing match fetching...")
if detector.fetch_current_matches():
    logger.info(f"Successfully fetched {len(detector.current_matches)} matches")

    # Save a sample of the matches for inspection
    sample_matches = (
        detector.current_matches[:3]
        if len(detector.current_matches) >= 3
        else detector.current_matches
    )
    with open("sample_matches.json", "w") as f:
        json.dump(sample_matches, f, indent=2)
    logger.info("Saved sample matches to sample_matches.json")

    # Print sample match details
    for i, match in enumerate(sample_matches):
        match_date = match.get("matchdatum", "Unknown date")
        match_time = match.get("matchtid", "Unknown time")
        home_team = match.get("hemmalag", "Unknown home team")
        away_team = match.get("bortalag", "Unknown away team")
        arena = match.get("arena", "Unknown arena")
        logger.info(
            f"Match {i+1}: {match_date} {match_time} - {home_team} vs {away_team} at {arena}"
        )
else:
    logger.error("Failed to fetch matches")
    exit(1)

# Test change detection
logger.info("Testing change detection...")

# First, save current matches as previous matches
with open("previous_matches_test.json", "w") as f:
    json.dump(detector.current_matches, f, indent=2)
logger.info("Saved current matches as previous matches")

# Modify one match to simulate a change
if detector.current_matches:
    # Make a deep copy of the current matches
    modified_matches = json.loads(json.dumps(detector.current_matches))

    # Modify the first match
    if modified_matches:
        modified_matches[0]["avsparkstid"] = "19:30"  # Change the match time
        logger.info(f"Modified match time for match ID: {modified_matches[0]['matchid']}")

    # Save the previous matches
    detector.previous_matches = detector.current_matches

    # Set the current matches to the modified list
    detector.current_matches = modified_matches

    # Detect changes
    has_changes, changes = detector.detect_changes()

    if has_changes:
        logger.info("Changes detected successfully!")
        logger.info(f"Changes: {json.dumps(changes, indent=2)}")
    else:
        logger.error("Failed to detect changes")
else:
    logger.warning("No matches to modify for change detection test")

logger.info("Test completed")
