#!/usr/bin/env python3

import os
import json
import subprocess
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple

from fogis_api_client import FogisApiClient, MatchListFilter
from logging_config import get_logger
from metrics import metrics
from health_server import HealthServer

# Get logger
logger = get_logger('match_list_change_detector')

# Start health server
health_server = HealthServer(port=8000)
health_server.start()

# Import configuration
from config import get_config

# Get configuration
config = get_config()

# Constants
PREVIOUS_MATCHES_FILE = config.get('PREVIOUS_MATCHES_FILE')
DOCKER_COMPOSE_FILE = config.get('DOCKER_COMPOSE_FILE')
FOGIS_USERNAME = config.get('FOGIS_USERNAME')
FOGIS_PASSWORD = config.get('FOGIS_PASSWORD')
DAYS_BACK = config.get('DAYS_BACK')
DAYS_AHEAD = config.get('DAYS_AHEAD')


class MatchListChangeDetector:
    """Detects changes in the match list and triggers actions when changes are found."""

    def __init__(self, username: str, password: str):
        """Initialize the detector with API credentials."""
        self.api_client = FogisApiClient(username, password)
        self.previous_matches: List[Dict[str, Any]] = []
        self.current_matches: List[Dict[str, Any]] = []

    def load_previous_matches(self) -> bool:
        """Load the previously saved matches from file."""
        try:
            if os.path.exists(PREVIOUS_MATCHES_FILE):
                with open(PREVIOUS_MATCHES_FILE, 'r') as f:
                    self.previous_matches = json.load(f)
                logger.info(
                    f"Loaded {len(self.previous_matches)} previous matches from "
                    f"{PREVIOUS_MATCHES_FILE}")
                return True
            else:
                logger.info(f"No previous matches file found at {PREVIOUS_MATCHES_FILE}")
                return False
        except Exception as e:
            logger.error(f"Error loading previous matches: {e}")
            return False

    def save_current_matches(self) -> bool:
        """Save the current matches to file for future comparison."""
        try:
            with open(PREVIOUS_MATCHES_FILE, 'w') as f:
                # noinspection PyTypeChecker
                json.dump(self.current_matches, f, indent=2)
            logger.info(
                f"Saved {len(self.current_matches)} current matches to {PREVIOUS_MATCHES_FILE}")
            return True
        except Exception as e:
            logger.error(f"Error saving current matches: {e}")
            return False

    def fetch_current_matches(self) -> bool:
        """Fetch the current list of matches from the API."""
        try:
            # Login to the API
            with metrics.time_api_request():
                self.api_client.login()
            logger.info("Successfully logged in to the API")

            # Create a filter for matches
            today = datetime.today()
            start_date = (today - timedelta(days=DAYS_BACK)).strftime('%Y-%m-%d')
            end_date = (today + timedelta(days=DAYS_AHEAD)).strftime('%Y-%m-%d')

            match_filter = MatchListFilter() \
                .start_date(start_date) \
                .end_date(end_date)

            # Fetch matches
            with metrics.time_api_request():
                self.current_matches = match_filter.fetch_filtered_matches(self.api_client)
            logger.info(f"Successfully fetched {len(self.current_matches)} current matches")
            return True
        except Exception as e:
            logger.error(f"Error fetching current matches: {e}")
            return False

    def detect_changes(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Detect changes between previous and current match lists.

        Returns:
            Tuple containing:
            - Boolean indicating if changes were detected
            - Dictionary with details about the changes
        """
        if not self.previous_matches:
            logger.info(
                "No previous matches to compare with, considering this as a change")
            return True, {
                "new_matches": len(self.current_matches),
                "message": "Initial match list fetch"
            }

        # Create dictionaries for easier comparison, using match ID as key
        prev_matches_dict = {match['matchid']: match
                             for match in self.previous_matches}
        curr_matches_dict = {match['matchid']: match
                             for match in self.current_matches}

        # Find new, removed, and changed matches
        new_match_ids = set(curr_matches_dict.keys()) - set(prev_matches_dict.keys())
        removed_match_ids = set(prev_matches_dict.keys()) - set(curr_matches_dict.keys())
        common_match_ids = set(curr_matches_dict.keys()) & set(prev_matches_dict.keys())

        # Check for changes in common matches
        changed_matches = []
        for match_id in common_match_ids:
            prev_match = prev_matches_dict[match_id]
            curr_match = curr_matches_dict[match_id]

            # Check for important changes (date, time, venue, referees, teams, status)
            # Compare basic match details
            basic_changes = (
                prev_match.get('speldatum') != curr_match.get('speldatum') or
                prev_match.get('avsparkstid') != curr_match.get('avsparkstid') or
                prev_match.get('anlaggningnamn') !=
                curr_match.get('anlaggningnamn') or
                prev_match.get('installd') != curr_match.get('installd') or
                prev_match.get('avbruten') != curr_match.get('avbruten') or
                prev_match.get('uppskjuten') != curr_match.get('uppskjuten') or
                prev_match.get('lag1lagid') != curr_match.get('lag1lagid') or
                prev_match.get('lag2lagid') != curr_match.get('lag2lagid')
            )

            # Compare referee assignments
            prev_referee_ids = set()
            curr_referee_ids = set()

            # Extract referee IDs from previous match
            if 'domaruppdraglista' in prev_match:
                for referee in prev_match['domaruppdraglista']:
                    prev_referee_ids.add(referee.get('domareid'))

            # Extract referee IDs from current match
            if 'domaruppdraglista' in curr_match:
                for referee in curr_match['domaruppdraglista']:
                    curr_referee_ids.add(referee.get('domareid'))

            referee_changes = prev_referee_ids != curr_referee_ids

            if basic_changes or referee_changes:

                # Create a detailed change record
                change_record = {
                    'match_id': match_id,
                    'match_nr': curr_match.get('matchnr'),
                    'previous': {
                        'date': prev_match.get('speldatum'),
                        'time': prev_match.get('avsparkstid'),
                        'home_team': {
                            'id': prev_match.get('lag1lagid'),
                            'name': prev_match.get('lag1namn')
                        },
                        'away_team': {
                            'id': prev_match.get('lag2lagid'),
                            'name': prev_match.get('lag2namn')
                        },
                        'venue': prev_match.get('anlaggningnamn'),
                        'status': {
                            'cancelled': prev_match.get('installd', False),
                            'interrupted': prev_match.get('avbruten', False),
                            'postponed': prev_match.get('uppskjuten', False)
                        },
                        'referees': []
                    },
                    'current': {
                        'date': curr_match.get('speldatum'),
                        'time': curr_match.get('avsparkstid'),
                        'home_team': {
                            'id': curr_match.get('lag1lagid'),
                            'name': curr_match.get('lag1namn')
                        },
                        'away_team': {
                            'id': curr_match.get('lag2lagid'),
                            'name': curr_match.get('lag2namn')
                        },
                        'venue': curr_match.get('anlaggningnamn'),
                        'status': {
                            'cancelled': curr_match.get('installd', False),
                            'interrupted': curr_match.get('avbruten', False),
                            'postponed': curr_match.get('uppskjuten', False)
                        },
                        'referees': []
                    },
                    'changes': {
                        'basic': basic_changes,
                        'referees': referee_changes
                    }
                }

                # Add referee details to previous match
                if 'domaruppdraglista' in prev_match:
                    for referee in prev_match['domaruppdraglista']:
                        change_record['previous']['referees'].append({
                            'id': referee.get('domareid'),
                            'name': referee.get('personnamn'),
                            'role': referee.get('domarrollnamn'),
                            'email': referee.get('epostadress'),
                            'phone': referee.get('mobiltelefon')
                        })

                # Add referee details to current match
                if 'domaruppdraglista' in curr_match:
                    for referee in curr_match['domaruppdraglista']:
                        change_record['current']['referees'].append({
                            'id': referee.get('domareid'),
                            'name': referee.get('personnamn'),
                            'role': referee.get('domarrollnamn'),
                            'email': referee.get('epostadress'),
                            'phone': referee.get('mobiltelefon')
                        })

                changed_matches.append(change_record)

        # Prepare the changes summary
        changes = {
            'new_matches': len(new_match_ids),
            'removed_matches': len(removed_match_ids),
            'changed_matches': len(changed_matches),
            'new_match_details': [
                curr_matches_dict[match_id] for match_id in new_match_ids
            ],
            'removed_match_details': [
                prev_matches_dict[match_id] for match_id in removed_match_ids
            ],
            'changed_match_details': changed_matches
        }

        # Determine if there are any changes
        has_changes = (len(new_match_ids) > 0 or
                       len(removed_match_ids) > 0 or
                       len(changed_matches) > 0)

        if has_changes:
            logger.info(
                f"Changes detected: {len(new_match_ids)} new, "
                f"{len(removed_match_ids)} removed, {len(changed_matches)} changed")
        else:
            logger.info("No changes detected in match list")

        return has_changes, changes

    # noinspection PyMethodMayBeStatic
    def trigger_docker_compose(self, changes: Dict[str, Any]) -> bool:
        """Trigger the docker-compose file with the changes as environment variables."""
        try:
            # Save changes to a file that can be read by the docker-compose services
            with open('match_changes.json', 'w') as f:
                # noinspection PyTypeChecker
                json.dump(changes, f, indent=2)

            # Run docker-compose up with a timeout
            logger.info(f"Triggering docker-compose with file: {DOCKER_COMPOSE_FILE}")
            try:
                result = subprocess.run(
                    ['docker-compose', '-f', DOCKER_COMPOSE_FILE, 'up', '-d'],
                    capture_output=True,
                    text=True,
                    timeout=30  # 30 second timeout
                )
            except subprocess.TimeoutExpired:
                logger.warning("docker-compose command timed out after 30 seconds")
                logger.warning("This is normal if the orchestrator is starting many services")
                logger.warning(
                    "The orchestrator has been triggered, but we're not waiting for it to complete")
                return True

            if result.returncode == 0:
                logger.info("Successfully triggered docker-compose")
                logger.debug(f"docker-compose output: {result.stdout}")
                return True
            else:
                logger.error(f"Error triggering docker-compose: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error triggering docker-compose: {e}")
            return False

    def run(self) -> bool:
        """Run the full change detection process."""
        start_time = time.time()
        metrics.record_run()

        try:
            # Load previous matches
            self.load_previous_matches()

            # Fetch current matches
            if not self.fetch_current_matches():
                logger.error("Failed to fetch current matches, aborting")
                metrics.record_fetch_failure()
                metrics.record_error()
                return False

            # Record match count
            metrics.record_matches(len(self.current_matches))

            # Detect changes
            has_changes, changes = self.detect_changes()

            # Record changes
            if has_changes:
                metrics.record_changes(
                    new=changes.get('new_matches', 0),
                    removed=changes.get('removed_matches', 0),
                    changed=changes.get('changed_matches', 0)
                )

            # If changes detected, trigger docker-compose
            if has_changes:
                logger.info("Changes detected, triggering docker-compose")
                metrics.record_orchestrator_trigger()
                if not self.trigger_docker_compose(changes):
                    metrics.record_orchestrator_failure()

            # Save current matches for next comparison
            self.save_current_matches()

            # Record processing time
            processing_time = time.time() - start_time
            metrics.record_processing_time(processing_time)
            logger.info(f"Change detection completed in {processing_time:.2f} seconds")

            return True

        except Exception as e:
            logger.error(f"Error in change detection process: {e}")
            metrics.record_error()
            return False


def main():
    """Main entry point for the script."""
    # Check for required configuration
    username = config.get('FOGIS_USERNAME')
    password = config.get('FOGIS_PASSWORD')

    if not username or not password:
        logger.error("FOGIS_USERNAME and FOGIS_PASSWORD must be set in configuration")
        return False

    # Create and run the detector
    detector = MatchListChangeDetector(username, password)
    success = detector.run()

    if success:
        logger.info("Match list change detection completed successfully")
    else:
        logger.error("Match list change detection failed")

    return success


if __name__ == "__main__":
    main()
