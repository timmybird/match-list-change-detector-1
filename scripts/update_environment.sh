#!/bin/bash

# Comprehensive script to update the development environment
# Run this when switching computers or after pulling updates

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
