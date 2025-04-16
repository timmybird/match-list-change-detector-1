#!/bin/bash

# Script to install git hooks
echo "Installing git hooks..."

# Create scripts directory if it doesn't exist
mkdir -p scripts

# Install pre-commit hooks
pre-commit install

# Install pre-push hook
cp .git/hooks/pre-push .git/hooks/pre-push.bak 2>/dev/null || true
cp scripts/pre-push .git/hooks/pre-push
chmod +x .git/hooks/pre-push

echo "Git hooks installed successfully!"
