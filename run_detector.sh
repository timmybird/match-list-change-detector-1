#!/bin/bash

# Load environment variables from .env file
if [ -f .env ]; then
    # Export all variables from .env file
    export $(grep -v '^#' .env | xargs)

    # Print the credentials (without showing the actual password)
    echo "Using username: $FOGIS_USERNAME"
    echo "Using password: ********"
else
    echo "Warning: .env file not found, using default configuration"
fi

# Create logs directory if it doesn't exist
mkdir -p ${LOG_DIR:-logs}

# Run the match list change detector
source .venv/bin/activate
python match_list_change_detector.py
