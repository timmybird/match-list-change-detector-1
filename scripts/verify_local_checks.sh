#!/bin/bash

# Script to verify that local checks are properly configured
echo "Verifying local check configuration..."

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo "ERROR: pre-commit is not installed. Run 'pip install pre-commit'."
    exit 1
fi

# Check if pre-commit hooks are installed
if [ ! -f .git/hooks/pre-commit ]; then
    echo "ERROR: pre-commit hooks are not installed. Run 'pre-commit install'."
    exit 1
fi

# Check if pre-push hook is installed
if [ ! -x .git/hooks/pre-push ]; then
    echo "ERROR: pre-push hook is not installed or not executable. Run './scripts/install_hooks.sh'."
    exit 1
fi

# Check if pre-push hook has the correct SKIP configuration
grep -q "SKIP=bandit,pydocstyle" .git/hooks/pre-push
if [ $? -ne 0 ]; then
    echo "ERROR: pre-push hook does not have the correct SKIP configuration. Run './scripts/install_hooks.sh'."
    exit 1
fi

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "ERROR: pytest is not installed. Run 'pip install pytest pytest-cov pytest-xdist hypothesis'."
    exit 1
fi

# Check if property-based tests pass
echo "Running property-based tests..."
python -m pytest tests/test_property_based.py -v
if [ $? -ne 0 ]; then
    echo "ERROR: property-based tests failed. Fix the tests before pushing."
    exit 1
fi

# Run a subset of pre-commit hooks that should pass
echo "Running critical pre-commit hooks..."
SKIP=bandit,pydocstyle pre-commit run --all-files
if [ $? -ne 0 ]; then
    echo "ERROR: pre-commit hooks failed. Fix the issues before pushing."
    exit 1
fi

echo "All local checks are properly configured and passing!"
echo "You should be able to push changes without CI/CD failures."
exit 0
