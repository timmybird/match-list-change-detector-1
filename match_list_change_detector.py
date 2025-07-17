#!/usr/bin/env python3
"""
Match list change detector for the Fogis API.

Detects changes in match lists and triggers actions when changes are found.
"""

import json
import shutil
import subprocess  # nosec B404
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, TypedDict, Union

from fogis_api_client import MatchListFilter

from centralized_api_client import CentralizedFogisApiClient
from config import get_config
from logging_config import get_logger

# Conditional import for health_server to handle CI environment issues
try:
    from health_server import HealthServer

    HEALTH_SERVER_AVAILABLE = True
except (ImportError, KeyError) as e:
    # Fallback for CI environments where http.server module may not be available
    import logging

    logging.getLogger(__name__).warning(f"Health server not available: {e}")

    class MockHealthServer:
        """Mock health server for environments where wsgiref is not available."""

        def __init__(self, *args, **kwargs):
            """Initialize mock health server."""
            pass

        def start(self):
            """Start mock health server (no-op)."""
            pass

        def stop(self):
            """Stop mock health server (no-op)."""
            pass

    HealthServer = MockHealthServer
    HEALTH_SERVER_AVAILABLE = False

# Conditional import for metrics to handle CI environment issues
try:
    from metrics import metrics

    METRICS_AVAILABLE = True
except (ImportError, KeyError) as e:
    # Fallback for CI environments where prometheus_client may not be available
    import logging

    logging.getLogger(__name__).warning(f"Metrics not available: {e}")

    class MockMetrics:
        """Mock metrics for environments where prometheus_client is not available."""

        def __getattr__(self, name):
            """Return a mock object that does nothing for any attribute access."""
            # Return a mock object that does nothing
            return lambda *args, **kwargs: None

    metrics = MockMetrics()
    METRICS_AVAILABLE = False


class MatchChangeRecord(TypedDict):
    """Type definition for a match change record."""

    match_id: str
    match_nr: str
    previous: Dict[str, Any]
    current: Dict[str, Any]
    changes: Dict[str, bool]


class ChangesSummary(TypedDict):
    """Type definition for the changes summary dictionary."""

    new_matches: int
    removed_matches: int
    changed_matches: int
    new_match_details: List[Dict[str, Any]]
    removed_match_details: List[Dict[str, Any]]
    changed_match_details: List[MatchChangeRecord]


# Get configuration
config = get_config()

# Get logger
logger = get_logger("match_list_change_detector")

# Start health server with HTTPS if configured
use_https = config.get("USE_HTTPS", False)
health_server_port = config.get("HEALTH_SERVER_PORT", 8000)
ssl_cert_file = config.get("SSL_CERT_FILE") if use_https else None
ssl_key_file = config.get("SSL_KEY_FILE") if use_https else None

health_server = HealthServer(
    port=health_server_port, use_https=use_https, cert_file=ssl_cert_file, key_file=ssl_key_file
)
health_server.start()

if not HEALTH_SERVER_AVAILABLE:
    logger.warning("Health server functionality not available in this environment")

# Constants
PREVIOUS_MATCHES_FILE = config.get("PREVIOUS_MATCHES_FILE")
DOCKER_COMPOSE_FILE = config.get("DOCKER_COMPOSE_FILE")
FOGIS_USERNAME = config.get("FOGIS_USERNAME")
FOGIS_PASSWORD = config.get("FOGIS_PASSWORD")
DAYS_BACK = config.get("DAYS_BACK")
DAYS_AHEAD = config.get("DAYS_AHEAD")


def get_executable_path(executable: str) -> Optional[str]:
    """Find the absolute path of an executable.

    Args:
        executable: Name of the executable to find

    Returns:
        Absolute path to the executable or None if not found

    """
    executable_path = shutil.which(executable)
    if executable_path is None:
        logger.error(f"Could not find executable: {executable}")
        return None
    return executable_path


class RateLimiter:
    """Rate limiter for API requests."""

    def __init__(self, max_requests: int, time_window: int = 60):
        """
        Initialize the rate limiter.

        Args:
            max_requests: Maximum number of requests allowed in the time window
            time_window: Time window in seconds (default: 60 seconds)

        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.request_timestamps: List[float] = []

    def can_make_request(self) -> bool:
        """
        Check if a request can be made without exceeding the rate limit.

        Returns:
            True if the request can be made, False otherwise

        """
        current_time = time.time()

        # Remove timestamps older than the time window
        self.request_timestamps = [
            ts for ts in self.request_timestamps if current_time - ts < self.time_window
        ]

        # Check if we've reached the limit
        if len(self.request_timestamps) < self.max_requests:
            self.request_timestamps.append(current_time)
            return True

        return False

    def wait_for_next_request(self) -> float:
        """
        Wait until a request can be made without exceeding the rate limit.

        Returns:
            Time waited in seconds

        """
        if self.can_make_request():
            return 0.0

        # Calculate how long to wait
        current_time = time.time()
        oldest_timestamp = self.request_timestamps[0]
        wait_time = self.time_window - (current_time - oldest_timestamp) + 0.1  # Add a small buffer

        logger.info(f"Rate limit reached. Waiting {wait_time: .2f} seconds before next request.")
        time.sleep(wait_time)

        # Add the new timestamp and remove the oldest one
        self.request_timestamps.pop(0)
        self.request_timestamps.append(time.time())

        return float(wait_time)


def validate_file_path(
    file_path: str, must_exist: bool = False, create_dir: bool = False
) -> Optional[Path]:
    """Validate a file path to prevent directory traversal attacks.

    Args:
        file_path: Path to validate
        must_exist: Whether the file must already exist
        create_dir: Whether to create the parent directory if it doesn't exist

    Returns:
        Validated Path object or None if validation fails

    """
    try:
        # Convert to Path object and resolve to absolute path
        path = Path(file_path).resolve()

        # Check if the file must exist
        if must_exist and not path.exists():
            logger.error(f"Required file does not exist: {path}")
            return None

        # Create parent directory if needed
        if create_dir and not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {path.parent}")

        return path
    except (ValueError, OSError) as e:
        logger.error(f"Invalid file path '{file_path}': {e}")
        return None


class MatchListChangeDetector:
    """Detects changes in the match list and triggers actions when changes are found."""

    api_client: CentralizedFogisApiClient
    previous_matches: List[Dict[str, Any]]
    current_matches: List[Dict[str, Any]]
    rate_limiter: RateLimiter

    def __init__(self, username: str, password: str):
        """Initialize the detector with API credentials."""
        # Use centralized API client if URL is provided, otherwise use direct API
        api_client_url = config.get("FOGIS_API_CLIENT_URL")
        self.api_client = CentralizedFogisApiClient(
            api_client_url=api_client_url, username=username, password=password
        )
        self.previous_matches = []
        self.current_matches = []

        # Initialize rate limiter
        max_requests = config.get("API_RATE_LIMIT", 10)
        self.rate_limiter = RateLimiter(max_requests=max_requests)

    def load_previous_matches(self) -> bool:
        """Load the previously saved matches from file."""
        try:
            # Validate the file path
            file_path = validate_file_path(PREVIOUS_MATCHES_FILE, must_exist=False)
            if not file_path:
                logger.error(f"Invalid previous matches file path: {PREVIOUS_MATCHES_FILE}")
                return False

            if file_path.exists():
                with open(file_path, "r") as f:
                    self.previous_matches = json.load(f)
                logger.info(
                    f"Loaded {len(self.previous_matches)} previous matches from " f"{file_path}"
                )
                return True
            else:
                logger.info(f"No previous matches file found at {file_path}")
                return False
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing previous matches file: {e}")
            return False
        except Exception as e:
            logger.error(f"Error loading previous matches: {e}")
            return False

    def save_current_matches(self) -> bool:
        """Save the current matches to file for future comparison."""
        try:
            # Validate the file path
            file_path = validate_file_path(PREVIOUS_MATCHES_FILE, create_dir=True)
            if not file_path:
                logger.error(f"Invalid previous matches file path: {PREVIOUS_MATCHES_FILE}")
                return False

            with open(file_path, "w") as f:
                # noinspection PyTypeChecker
                json.dump(self.current_matches, f, indent=2)
            logger.info(f"Saved {len(self.current_matches)} current matches to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving current matches: {e}")
            return False

    def fetch_current_matches(self) -> bool:
        """Fetch the current list of matches from the API."""
        try:
            # Apply rate limiting before login
            self.rate_limiter.wait_for_next_request()

            # Login to the API
            with metrics.time_api_request():
                self.api_client.login()
            logger.info("Successfully logged in to the API")

            # Create a filter for matches
            today = datetime.today()
            start_date = (today - timedelta(days=DAYS_BACK)).strftime("%Y-%m-%d")
            end_date = (today + timedelta(days=DAYS_AHEAD)).strftime("%Y-%m-%d")

            match_filter = MatchListFilter().start_date(start_date).end_date(end_date)

            # Apply rate limiting before fetching matches
            self.rate_limiter.wait_for_next_request()

            # Fetch matches using direct API call (PyPI v0.5.3 compatibility)
            with metrics.time_api_request():
                payload = match_filter.build_payload()
                api_response = self.api_client.fetch_matches_list_json(filter_params=payload)

                # Handle different response structures from PyPI package
                if isinstance(api_response, dict) and "matches" in api_response:
                    self.current_matches = api_response["matches"]
                elif isinstance(api_response, list):
                    self.current_matches = api_response
                else:
                    logger.error(f"Unexpected API response structure: {type(api_response)}")
                    logger.debug(f"Response content: {api_response}")
                    self.current_matches = []
            logger.info(f"Successfully fetched {len(self.current_matches)} current matches")
            return True
        except Exception as e:
            logger.error(f"Error fetching current matches: {e}")
            return False

    def detect_changes(self) -> Tuple[bool, Union[ChangesSummary, Dict[str, Any]]]:
        """
        Detect changes between previous and current match lists.

        Returns:
            Tuple containing:
            - Boolean indicating if changes were detected
            - Dictionary with details about the changes
        """
        if not self.previous_matches:
            logger.info("No previous matches to compare with, considering this as a change")
            return True, {
                "new_matches": len(self.current_matches),
                "message": "Initial match list fetch",
            }

        # Create dictionaries for easier comparison, using match ID as key
        prev_matches_dict = {match["matchid"]: match for match in self.previous_matches}
        curr_matches_dict = {match["matchid"]: match for match in self.current_matches}

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
                prev_match.get("speldatum") != curr_match.get("speldatum")
                or prev_match.get("avsparkstid") != curr_match.get("avsparkstid")
                or prev_match.get("anlaggningnamn") != curr_match.get("anlaggningnamn")
                or prev_match.get("installd") != curr_match.get("installd")
                or prev_match.get("avbruten") != curr_match.get("avbruten")
                or prev_match.get("uppskjuten") != curr_match.get("uppskjuten")
                or prev_match.get("lag1lagid") != curr_match.get("lag1lagid")
                or prev_match.get("lag2lagid") != curr_match.get("lag2lagid")
            )

            # Compare referee assignments
            prev_referee_ids = set()
            curr_referee_ids = set()

            # Extract referee IDs from previous match
            if "domaruppdraglista" in prev_match:
                for referee in prev_match["domaruppdraglista"]:
                    prev_referee_ids.add(referee.get("domareid"))

            # Extract referee IDs from current match
            if "domaruppdraglista" in curr_match:
                for referee in curr_match["domaruppdraglista"]:
                    curr_referee_ids.add(referee.get("domareid"))

            referee_changes = prev_referee_ids != curr_referee_ids

            if basic_changes or referee_changes:
                # Create a detailed change record
                change_record = {
                    "match_id": match_id,
                    "match_nr": curr_match.get("matchnr"),
                    "previous": {
                        "date": prev_match.get("speldatum"),
                        "time": prev_match.get("avsparkstid"),
                        "home_team": {
                            "id": prev_match.get("lag1lagid"),
                            "name": prev_match.get("lag1namn"),
                        },
                        "away_team": {
                            "id": prev_match.get("lag2lagid"),
                            "name": prev_match.get("lag2namn"),
                        },
                        "venue": prev_match.get("anlaggningnamn"),
                        "status": {
                            "cancelled": prev_match.get("installd", False),
                            "interrupted": prev_match.get("avbruten", False),
                            "postponed": prev_match.get("uppskjuten", False),
                        },
                        "referees": [],
                    },
                    "current": {
                        "date": curr_match.get("speldatum"),
                        "time": curr_match.get("avsparkstid"),
                        "home_team": {
                            "id": curr_match.get("lag1lagid"),
                            "name": curr_match.get("lag1namn"),
                        },
                        "away_team": {
                            "id": curr_match.get("lag2lagid"),
                            "name": curr_match.get("lag2namn"),
                        },
                        "venue": curr_match.get("anlaggningnamn"),
                        "status": {
                            "cancelled": curr_match.get("installd", False),
                            "interrupted": curr_match.get("avbruten", False),
                            "postponed": curr_match.get("uppskjuten", False),
                        },
                        "referees": [],
                    },
                    "changes": {"basic": basic_changes, "referees": referee_changes},
                }

                # Add referee details to previous match
                if "domaruppdraglista" in prev_match:
                    for referee in prev_match["domaruppdraglista"]:
                        change_record["previous"]["referees"].append(
                            {
                                "id": referee.get("domareid"),
                                "name": referee.get("personnamn"),
                                "role": referee.get("domarrollnamn"),
                                "email": referee.get("epostadress"),
                                "phone": referee.get("mobiltelefon"),
                            }
                        )

                # Add referee details to current match
                if "domaruppdraglista" in curr_match:
                    for referee in curr_match["domaruppdraglista"]:
                        change_record["current"]["referees"].append(
                            {
                                "id": referee.get("domareid"),
                                "name": referee.get("personnamn"),
                                "role": referee.get("domarrollnamn"),
                                "email": referee.get("epostadress"),
                                "phone": referee.get("mobiltelefon"),
                            }
                        )

                changed_matches.append(change_record)

        # Prepare the changes summary
        changes = {
            "new_matches": len(new_match_ids),
            "removed_matches": len(removed_match_ids),
            "changed_matches": len(changed_matches),
            "new_match_details": [curr_matches_dict[match_id] for match_id in new_match_ids],
            "removed_match_details": [
                prev_matches_dict[match_id] for match_id in removed_match_ids
            ],
            "changed_match_details": changed_matches,
        }

        # Determine if there are any changes
        has_changes = (
            len(new_match_ids) > 0 or len(removed_match_ids) > 0 or len(changed_matches) > 0
        )

        if has_changes:
            logger.info(
                f"Changes detected: {len(new_match_ids)} new, "
                f"{len(removed_match_ids)} removed, {len(changed_matches)} changed"
            )
        else:
            logger.info("No changes detected in match list")

        return has_changes, changes

    # noinspection PyMethodMayBeStatic
    def trigger_docker_compose(self, changes: Union[ChangesSummary, Dict[str, Any]]) -> bool:
        """Trigger the docker-compose file with the changes as environment variables."""
        try:
            # Validate docker-compose file path
            if not DOCKER_COMPOSE_FILE:
                logger.error("DOCKER_COMPOSE_FILE is not set in configuration")
                return False

            compose_file_path = Path(DOCKER_COMPOSE_FILE)
            if not compose_file_path.is_file():
                logger.error(f"Docker compose file not found: {compose_file_path}")
                return False

            # Find docker-compose executable
            docker_compose_path = get_executable_path("docker-compose")
            if not docker_compose_path:
                logger.error("docker-compose executable not found in PATH")
                return False

            # Save changes to a file that can be read by the docker-compose services
            changes_file_path = validate_file_path("match_changes.json", create_dir=True)
            if not changes_file_path:
                logger.error("Invalid changes file path")
                return False

            with open(changes_file_path, "w") as f:
                # noinspection PyTypeChecker
                json.dump(changes, f, indent=2)

            # Run docker-compose up with a timeout
            logger.info(f"Triggering docker-compose with file: {compose_file_path}")
            try:
                # We're using absolute paths and validating all inputs before this call
                result = subprocess.run(  # nosec B603
                    [docker_compose_path, "-f", str(compose_file_path.absolute()), "up", "-d"],
                    capture_output=True,
                    text=True,
                    timeout=30,  # 30 second timeout
                    check=False,  # We'll handle the return code ourselves
                )
            except subprocess.TimeoutExpired:
                logger.warning("docker-compose command timed out after 30 seconds")
                logger.warning("This is normal if the orchestrator is starting many services")
                logger.warning(
                    "The orchestrator has been triggered, but we're not waiting for it to complete"
                )
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
                    new=changes.get("new_matches", 0),
                    removed=changes.get("removed_matches", 0),
                    changed=changes.get("changed_matches", 0),
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
            logger.info(f"Change detection completed in {processing_time: .2f} seconds")

            return True

        except Exception as e:
            logger.error(f"Error in change detection process: {e}")
            metrics.record_error()
            return False


def mask_sensitive_data(data: str) -> str:
    """Mask sensitive data like passwords in logs.

    Args:
        data: String that might contain sensitive data

    Returns:
        String with sensitive data masked

    """
    if not data:
        return data
    return "*" * 8  # Return fixed-length mask regardless of input length


def main() -> bool:
    """Run the match list change detection process."""
    # Check for required configuration
    username = config.get("FOGIS_USERNAME")
    password = config.get("FOGIS_PASSWORD")

    if not username or not password:
        logger.error("FOGIS_USERNAME and FOGIS_PASSWORD must be set in configuration")
        return False

    # Log username only, never log password even if masked
    logger.info(f"Using FOGIS account: {username}")
    logger.debug("Password provided: [REDACTED]")

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
