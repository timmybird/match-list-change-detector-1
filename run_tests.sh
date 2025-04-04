#!/bin/bash

# Activate the virtual environment
source .venv/bin/activate

# Run the tests with coverage
python -m unittest discover -s tests

# Print a message
echo "Tests completed!"
