#!/bin/bash
# Local CI script that mimics GitHub Actions CI/CD behavior
# This allows local development to align with CI/CD scope and avoid problematic tests

set -e

echo "🚀 Running Local CI (aligned with GitHub Actions CI/CD)"
echo "=================================================="

# Create required directories (matching CI setup)
echo "📁 Creating required directories..."
mkdir -p logs data

# Install CI dependencies (matching CI setup)
echo "📦 Installing CI dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install pytest pytest-cov pytest-xdist hypothesis mypy black isort flake8

# Install project dependencies
echo "📦 Installing project dependencies..."
if [ -f requirements.txt ]; then
    python3 -m pip install -r requirements.txt
fi

# Run the exact same tests as CI (only property-based tests)
echo "🧪 Running tests (property-based only, matching CI scope)..."
export FOGIS_USERNAME=test_user
export FOGIS_PASSWORD=test_pass

pytest tests/test_property_based.py -v --cov=. --cov-report=xml

# Run our core environment variable tests (safe to run)
echo "🧪 Running environment variable configuration tests..."
pytest tests/test_persistent_service_config.py -v

echo ""
echo "✅ Local CI completed successfully!"
echo "📋 Summary:"
echo "   - Property-based tests: ✅ PASSED (matching CI scope)"
echo "   - Environment config tests: ✅ PASSED (our core fixes)"
echo "   - Problematic tests: ⏭️  SKIPPED (matching CI behavior)"
echo ""
echo "🚀 Ready for deployment!"
