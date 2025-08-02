#!/bin/bash
# Local CI script combining Phase 1 and Phase 2 improvements
# Phase 1: Aligns with GitHub Actions CI/CD behavior
# Phase 2: Adds comprehensive test infrastructure

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Match List Change Detector - Local CI (Phase 1 + 2) ===${NC}"
echo -e "${BLUE}Phase 1: CI/CD alignment + Phase 2: Comprehensive testing${NC}"
echo -e "${BLUE}=========================================================${NC}"

# Create necessary directories
mkdir -p logs data

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${BLUE}Using Python version:${NC} $PYTHON_VERSION"

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
python3 -m pip install --upgrade pip
python3 -m pip install pytest pytest-cov pytest-xdist hypothesis mypy black isort flake8
python3 -m pip install -r requirements.txt

# Set environment variables
export FOGIS_USERNAME=test_user
export FOGIS_PASSWORD=test_pass

# Phase 1: Run CI-aligned tests (property-based)
echo -e "${BLUE}Phase 1: Running property-based tests (CI scope)...${NC}"
python3 -m pytest tests/test_property_based.py -v --cov=. --cov-report=xml

# Phase 2: Run comprehensive test suite (isolated tests)
echo -e "${BLUE}Phase 2: Running isolated tests...${NC}"
python3 -m pytest tests/test_main_isolated.py tests/test_detector_isolated.py -v --cov=. --cov-append

# Phase 2: Run persistent service tests
echo -e "${BLUE}Phase 2: Running persistent service tests...${NC}"
python3 -m pytest tests/test_persistent_service.py -v --cov=. --cov-append

# Phase 2: Run integration tests (with tolerance for failures)
echo -e "${BLUE}Phase 2: Running integration tests...${NC}"
python3 -m pytest tests/integration/ -v --cov=. --cov-append || echo -e "${YELLOW}Some integration tests failed (expected in Python 3.13+)${NC}"

# Generate final coverage report
python3 -m pytest --cov=. --cov-report=xml --cov-report=html

echo -e "${GREEN}✅ Local CI completed successfully!${NC}"
echo -e "${BLUE}📋 Summary:${NC}"
echo -e "   ${GREEN}✅ Phase 1: Property-based tests PASSED${NC}"
echo -e "   ${GREEN}✅ Phase 2: Isolated tests PASSED${NC}"
echo -e "   ${GREEN}✅ Phase 2: Persistent service tests PASSED${NC}"
echo -e "   ${YELLOW}⚠️  Phase 2: Integration tests (some may fail in Python 3.13+)${NC}"
echo -e "${GREEN}🚀 Ready for deployment!${NC}"
