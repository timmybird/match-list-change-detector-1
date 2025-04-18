#!/bin/bash

# Comprehensive script to update the development environment
# Run this when switching computers or after pulling updates

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

echo "🔄 Updating development environment..."

# Step 1: Update dependencies
echo "📦 Installing/updating dependencies..."
pip install -r requirements.txt
pip install pre-commit pytest pytest-cov pytest-xdist hypothesis black isort mypy flake8 sphinx sphinx-rtd-theme
echo "✅ Dependencies installed successfully!"

# Step 2: Install pre-commit hooks
echo "🔧 Installing pre-commit hooks..."
pre-commit install
echo "✅ Pre-commit hooks installed successfully!"

# Step 3: Install pre-push hooks
echo "🔧 Installing pre-push hooks..."
./scripts/install_hooks.sh
echo "✅ Pre-push hooks installed successfully!"

# Step 4: Set up post-merge hook
echo "🔧 Setting up post-merge hook..."
./scripts/setup_post_merge_hook.sh
echo "✅ Post-merge hook installed successfully!"

# Step 5: Verify local checks
echo "🔍 Verifying local environment setup..."
./scripts/verify_local_checks.sh
if [ $? -ne 0 ]; then
    echo "⚠️ Some verification checks failed. Please review the output above."
else
    echo "✅ All verification checks passed!"
fi

echo ""
echo "🎉 Environment update complete! You're ready to code!"
echo "Run this script again after pulling updates or when switching computers."
