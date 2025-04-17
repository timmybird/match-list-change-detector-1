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
