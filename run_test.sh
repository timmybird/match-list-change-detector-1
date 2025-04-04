#!/bin/bash

# Prompt for credentials
read -p "Enter your FOGIS username: " username
read -sp "Enter your FOGIS password: " password
echo

# Run the test with the provided credentials
source .venv/bin/activate
FOGIS_USERNAME="$username" FOGIS_PASSWORD="$password" python test_api_client.py
