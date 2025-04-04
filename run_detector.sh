#!/bin/bash

# Load environment variables from .env file
if [ -f .env ]; then
    # Read username and password directly
    FOGIS_USERNAME=$(grep -E '^FOGIS_USERNAME=' .env | cut -d '=' -f2- | sed 's/^"\(.*\)"$/\1/')
    FOGIS_PASSWORD=$(grep -E '^FOGIS_PASSWORD=' .env | cut -d '=' -f2- | sed 's/^"\(.*\)"$/\1/')

    # Load other environment variables
    export DAYS_BACK=$(grep -E '^DAYS_BACK=' .env | cut -d '=' -f2)
    export DAYS_AHEAD=$(grep -E '^DAYS_AHEAD=' .env | cut -d '=' -f2)
    export ORCHESTRATOR_DOCKER_COMPOSE_PATH=$(grep -E '^ORCHESTRATOR_DOCKER_COMPOSE_PATH=' .env | cut -d '=' -f2)
    export CONTAINER_NETWORK=$(grep -E '^CONTAINER_NETWORK=' .env | cut -d '=' -f2)
    export TZ=$(grep -E '^TZ=' .env | cut -d '=' -f2)
else
    echo "Error: .env file not found"
    exit 1
fi

# Print the credentials (without showing the actual password)
echo "Using username: $FOGIS_USERNAME"
echo "Using password: ********"

# Run the match list change detector
source .venv/bin/activate
FOGIS_USERNAME="$FOGIS_USERNAME" FOGIS_PASSWORD="$FOGIS_PASSWORD" python match_list_change_detector.py
