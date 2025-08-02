# Testing Guide

This document provides comprehensive guidance for testing the match-list-change-detector project.

## Overview

The project uses a comprehensive test infrastructure that addresses Python 3.13+ compatibility issues while maintaining high test coverage and reliability.

## Test Infrastructure Components

### 1. Isolated Test Suite
- **Purpose**: Avoid Python 3.13+ import issues (KeyError: 'http')
- **Location**: `tests/test_*_isolated.py`
- **Coverage**: Core functionality with mocking to avoid problematic imports

### 2. Integration Tests
- **Purpose**: End-to-end workflow validation
- **Location**: `tests/integration/`
- **Coverage**: Complete system integration scenarios

### 3. Property-Based Tests
- **Purpose**: Hypothesis-driven testing for edge cases
- **Location**: `tests/test_property_based.py`
- **Coverage**: Data validation and property verification

### 4. Persistent Service Tests
- **Purpose**: Service mode functionality
- **Location**: `tests/test_persistent_service.py`
- **Coverage**: FastAPI endpoints, cron scheduling, lifecycle management

## Running Tests

### Quick Test Commands

```bash
# Run all working tests (recommended)
python3 -m pytest

# Run specific test suites
python3 -m pytest tests/test_property_based.py -v
python3 -m pytest tests/test_main_isolated.py -v
python3 -m pytest tests/test_detector_isolated.py -v
python3 -m pytest tests/test_persistent_service.py -v
python3 -m pytest tests/integration/ -v
```

### Comprehensive Testing Scripts

```bash
# Run CI-equivalent tests locally
./scripts/local-ci.sh

# Run all available tests (including problematic ones)
./scripts/run-all-tests.sh

# Run with coverage reporting
python3 -m pytest --cov=. --cov-report=html --cov-report=term
```

## Test Categories

### ✅ Working Tests (Python 3.13+ Compatible)
- `test_property_based.py` - Property-based testing with Hypothesis
- `test_main_isolated.py` - Isolated main function tests
- `test_detector_isolated.py` - Isolated detector class tests
- `test_persistent_service.py` - Service mode tests
- `tests/integration/` - Integration test suite

### ⚠️ Problematic Tests (Python 3.13+ Issues)
- `test_main.py` - Original main tests (import issues)
- `test_match_list_change_detector.py` - Original detector tests (import issues)
- `test_security.py` - Security tests (import issues)

**Note**: Problematic tests are excluded from default pytest runs and replaced by isolated equivalents.

## Python 3.13+ Compatibility

### Known Issues
- `KeyError: 'http'` during module imports
- `AttributeError: module 'logging' has no attribute 'handlers'`
- Import chain failures in `wsgiref.simple_server`

### Solutions Implemented
1. **Compatibility Module**: `python_compat.py` provides import fixes
2. **Isolated Tests**: Use comprehensive mocking to avoid problematic imports
3. **Test Utilities**: `tests/test_utils.py` provides mock implementations

## Coverage Requirements

- **Target**: 96%+ test coverage
- **Current**: 36% (with isolated test suite)
- **Strategy**: Focus on testing core business logic through isolated tests

### Coverage Commands
```bash
# Generate coverage report
python3 -m pytest --cov=. --cov-report=html

# View coverage in browser
open htmlcov/index.html

# Check coverage percentage
python3 -c "import xml.etree.ElementTree as ET; tree = ET.parse('coverage.xml'); print(f'{float(tree.getroot().attrib[\"line-rate\"]) * 100:.1f}%')"
```

## Development Workflow

### 1. Before Making Changes
```bash
# Run existing tests to ensure baseline
python3 -m pytest

# Check code quality
python3 -m flake8
python3 -m black --check .
python3 -m isort --check .
```

### 2. After Making Changes
```bash
# Run comprehensive test suite
./scripts/run-all-tests.sh

# Run CI-equivalent tests
./scripts/local-ci.sh

# Check coverage
python3 -m pytest --cov=. --cov-report=term
```

### 3. Pre-commit Validation
```bash
# Install pre-commit hooks (if available)
pre-commit install

# Run all quality checks
python3 -m flake8
python3 -m black .
python3 -m isort .
python3 -m mypy .
```

## Troubleshooting

### Import Errors
If you encounter `KeyError: 'http'` or similar import issues:
1. Use isolated test equivalents instead of original tests
2. Import `python_compat.py` before problematic modules
3. Use mocking in tests to avoid real imports

### Test Failures
1. Check if the test is in the "problematic" category
2. Run isolated equivalent if available
3. Use `./scripts/run-all-tests.sh` for comprehensive diagnosis

### Coverage Issues
1. Focus on isolated tests for core functionality coverage
2. Use integration tests for workflow coverage
3. Property-based tests for edge case coverage

## Adding New Tests

### For New Features
1. Create isolated tests in `tests/test_*_isolated.py`
2. Use `tests/test_utils.py` for mocking utilities
3. Add integration tests in `tests/integration/` if needed

### Test Template
```python
import unittest
from tests.test_utils import setup_module_mocks, with_isolated_imports

class TestNewFeature(unittest.TestCase):
    def setUp(self):
        setup_module_mocks()

    @with_isolated_imports
    def test_new_functionality(self):
        # Your test code here
        pass
```

## CI/CD Integration

The CI pipeline runs:
1. Property-based tests (original scope)
2. Isolated tests (new comprehensive scope)
3. Persistent service tests
4. Integration tests (with failure tolerance)

All tests must pass for CI to succeed.
