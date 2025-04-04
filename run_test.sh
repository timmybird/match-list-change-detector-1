#!/bin/bash

# Prompt for credentials
read -p "Enter your FOGIS username: " username
read -sp "Enter your FOGIS password: " password
echo

# Create logs directory if it doesn't exist
mkdir -p ${LOG_DIR:-logs}

# Run the test with the provided credentials
source .venv/bin/activate
FOGIS_USERNAME="$username" FOGIS_PASSWORD="$password" python test_api_client.py
