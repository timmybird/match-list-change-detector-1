#!/usr/bin/env python3
"""
Test script for the Fogis API client.

Allows manual testing of the API client functionality.
"""

import json
from datetime import datetime, timedelta

from fogis_api_client import FogisApiClient, MatchListFilter, MatchStatus

from config import get_config
from logging_config import get_logger

# Get logger
logger = get_logger("test_api_client")

config = get_config()

# Get credentials from configuration
username = config.get("FOGIS_USERNAME")
password = config.get("FOGIS_PASSWORD")

if not username or not password:
    logger.error("FOGIS_USERNAME and FOGIS_PASSWORD must be set in configuration.")
    exit(1)

# Initialize the API client
api_client = FogisApiClient(username, password)

# Login to the API
try:
    api_client.login()
    logger.info("Login successful!")
except Exception as e:
    logger.error(f"Login failed: {e}")
    exit(1)

# Create a filter for upcoming matches
today = datetime.today().strftime("%Y-%m-%d")
one_month_ahead = (datetime.today() + timedelta(days=30)).strftime("%Y-%m-%d")

match_filter = (
    MatchListFilter()
    .start_date(today)
    .end_date(one_month_ahead)
    .exclude_statuses({MatchStatus.CANCELLED, MatchStatus.INTERRUPTED})
)

# Fetch filtered matches
try:
    matches = match_filter.fetch_filtered_matches(api_client)
    logger.info(f"Successfully fetched {len(matches)} matches.")

    # Save matches to a file for inspection
    with open("test_matches.json", "w") as f:
        # noinspection PyTypeChecker
        json.dump(matches, f, indent=2)
    logger.info(f"Matches saved to test_matches.json")

    # Log a few match details
    if matches:
        logger.info("Sample matches:")
        for i, match in enumerate(matches[:3]):  # Show first 3 matches
            match_date = match.get("speldatum", "Unknown date")
            match_time = match.get("avsparkstid", "Unknown time")
            home_team = match.get("lag1namn", "Unknown home team")
            away_team = match.get("lag2namn", "Unknown away team")
            venue = match.get("anlaggningnamn", "Unknown venue")
            logger.info(f"{i+1}. {match_date} {match_time}: {home_team} vs {away_team} at {venue}")

except Exception as e:
    logger.error(f"Error fetching matches: {e}")
