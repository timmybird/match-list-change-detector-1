#!/usr/bin/env python3

import os
import json
from datetime import datetime, timedelta
from fogis_api_client.fogis_api_client import FogisApiClient
from fogis_api_client.match_list_filter import MatchListFilter
from fogis_api_client.enums import MatchStatus, AgeCategory, Gender, FootballType

# Get credentials from environment variables
username = os.environ.get('FOGIS_USERNAME')
password = os.environ.get('FOGIS_PASSWORD')

if not username or not password:
    print("Error: FOGIS_USERNAME and FOGIS_PASSWORD environment variables must be set.")
    exit(1)

# Initialize the API client
api_client = FogisApiClient(username, password)

# Login to the API
try:
    api_client.login()
    print("Login successful!")
except Exception as e:
    print(f"Login failed: {e}")
    exit(1)

# Create a filter for upcoming matches
today = datetime.today().strftime('%Y-%m-%d')
one_month_ahead = (datetime.today() + timedelta(days=30)).strftime('%Y-%m-%d')

match_filter = MatchListFilter() \
    .start_date(today) \
    .end_date(one_month_ahead) \
    .exclude_statuses([MatchStatus.CANCELLED, MatchStatus.INTERRUPTED])

# Fetch filtered matches
try:
    matches = match_filter.fetch_filtered_matches(api_client)
    print(f"Successfully fetched {len(matches)} matches.")

    # Save matches to a file for inspection
    with open('test_matches.json', 'w') as f:
        json.dump(matches, f, indent=2)
    print(f"Matches saved to test_matches.json")

    # Print a few match details
    if matches:
        print("\nSample matches:")
        for i, match in enumerate(matches[:3]):  # Show first 3 matches
            match_date = match.get('speldatum', 'Unknown date')
            match_time = match.get('avsparkstid', 'Unknown time')
            home_team = match.get('lag1namn', 'Unknown home team')
            away_team = match.get('lag2namn', 'Unknown away team')
            venue = match.get('anlaggningnamn', 'Unknown venue')
            print(f"{i+1}. {match_date} {match_time}: {home_team} vs {away_team} at {venue}")

except Exception as e:
    print(f"Error fetching matches: {e}")
