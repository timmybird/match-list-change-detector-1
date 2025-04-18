#!/bin/bash

# Script to install git hooks

# Version tracking
SCRIPT_VERSION="1.0"
REQUIRED_VERSION="1.0"

# This version will be updated to 2.0 after issues #3, #4, and #5 are complete
# See issue #6: https://github.com/timmybird/match-list-change-detector/issues/6

# Version check
if [ "$SCRIPT_VERSION" != "$REQUIRED_VERSION" ]; then
    echo "⚠️  WARNING: This script (version $SCRIPT_VERSION) may be outdated! ⚠️"
    echo "The required version is $REQUIRED_VERSION."
    echo "Please check for updates in the repository."
    echo "See issue #6: https://github.com/timmybird/match-list-change-detector/issues/6"
    echo ""
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting. Please update the script first."
        exit 1
    fi
    echo "Continuing with the current version..."
fi

echo "Installing git hooks..."

# Create scripts directory if it doesn't exist
mkdir -p scripts

# Install pre-commit hooks
pre-commit install

# Install pre-push hook
cp .git/hooks/pre-push .git/hooks/pre-push.bak 2>/dev/null || true
cp scripts/pre-push .git/hooks/pre-push
chmod +x .git/hooks/pre-push

# Verify the hook was installed correctly
echo "Verifying pre-push hook installation..."
if [ -x .git/hooks/pre-push ]; then
    echo "Pre-push hook installed successfully!"
    grep -q "SKIP=bandit,pydocstyle" .git/hooks/pre-push
    if [ $? -eq 0 ]; then
        echo "Pre-push hook contains correct SKIP configuration."
    else
        echo "WARNING: Pre-push hook does not contain correct SKIP configuration."
    fi
else
    echo "ERROR: Pre-push hook not installed correctly!"
fi

echo "Git hooks installed successfully!"
