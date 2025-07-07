#!/usr/bin/env python3
"""
Centralized API client for accessing FOGIS data through the centralized service.

This module provides a wrapper around the centralized FOGIS API client service,
allowing services to use either the centralized service or direct API access.
"""

import logging
from typing import Any, Dict, Optional

import requests
from fogis_api_client import FogisApiClient

logger = logging.getLogger(__name__)


class CentralizedFogisApiClient:
    """Centralized FOGIS API client.

    Can use either the centralized service or direct API access based on configuration.
    """

    def __init__(
        self,
        api_client_url: Optional[str] = None,
        username: str = "",
        password: str = "",  # nosec B107
    ):
        """
        Initialize the centralized API client.

        Args:
            api_client_url: URL of the centralized FOGIS API client service
            username: FOGIS username (used for direct API access)
            password: FOGIS password (used for direct API access)
        """
        self.api_client_url = api_client_url
        self.username = username
        self.password = password
        self._direct_client: Optional[FogisApiClient] = None

        # Determine which mode to use
        self.use_centralized = bool(api_client_url and api_client_url.strip())

        if self.use_centralized:
            logger.info(f"Using centralized FOGIS API client at: {self.api_client_url}")
        else:
            logger.info("Using direct FOGIS API client")
            if username and password:
                self._direct_client = FogisApiClient(username, password)
            else:
                logger.warning("No username/password provided for direct API access")

    def login(self) -> bool:
        """
        Login to FOGIS API.

        Returns:
            True if login successful, False otherwise
        """
        if self.use_centralized:
            # For centralized service, login is handled by the service itself
            try:
                response = requests.get(f"{self.api_client_url}/health", timeout=10)
                return response.status_code == 200
            except requests.RequestException as e:
                logger.error(f"Failed to connect to centralized API client: {e}")
                return False
        else:
            if self._direct_client:
                try:
                    return self._direct_client.login()
                except Exception as e:
                    logger.error(f"Direct API login failed: {e}")
                    return False
            return False

    def fetch_matches_list_json(
        self, filter_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Fetch matches list as JSON.

        Args:
            filter_params: Filter parameters for the matches

        Returns:
            JSON response containing matches data
        """
        if self.use_centralized:
            return self._fetch_from_centralized_service(filter_params)
        else:
            return self._fetch_from_direct_api(filter_params)

    def _fetch_from_centralized_service(
        self, filter_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Fetch matches from the centralized service.

        Args:
            filter_params: Filter parameters for the matches

        Returns:
            JSON response containing matches data
        """
        try:
            url = f"{self.api_client_url}/matches"

            # Add filter parameters as query parameters if provided
            params = {}
            if filter_params:
                # Convert filter_params to query parameters
                for key, value in filter_params.items():
                    if value is not None:
                        params[key] = value

            logger.info(f"Fetching matches from centralized service: {url}")
            if params:
                logger.info(f"Using filter parameters: {params}")

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            matches_data = response.json()
            logger.info(
                f"Successfully fetched {len(matches_data)} matches from centralized service"
            )

            # Return in the expected format
            return {"matches": matches_data, "total": len(matches_data), "status": "success"}

        except requests.RequestException as e:
            logger.error(f"Failed to fetch matches from centralized service: {e}")
            return {"matches": [], "total": 0, "status": "error", "error": str(e)}

    def _fetch_from_direct_api(
        self, filter_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Fetch matches from the direct FOGIS API.

        Args:
            filter_params: Filter parameters for the matches

        Returns:
            JSON response containing matches data
        """
        if not self._direct_client:
            logger.error("Direct API client not initialized")
            return {
                "matches": [],
                "total": 0,
                "status": "error",
                "error": "Direct API client not initialized",
            }

        try:
            logger.info("Fetching matches from direct FOGIS API")
            return self._direct_client.fetch_matches_list_json(filter_params=filter_params)

        except Exception as e:
            logger.error(f"Failed to fetch matches from direct API: {e}")
            return {"matches": [], "total": 0, "status": "error", "error": str(e)}
