# Unit Tests for Llama Stack

This directory contains unit tests for the Llama Stack APIs. The tests are organized to mirror the structure of the API modules.

## Test Structure

- `tests/unit/apis/`: Unit tests for API modules
  - `batch_inference/`: Tests for batch inference API
  - `models/`: Tests for models API
  - `tools/`: Tests for tools API
  - `safety/`: Tests for safety API
  - ... (other API modules)

## Running Tests

To run the unit tests, use pytest:

```bash
# Run all unit tests
pytest tests/unit/

# Run tests for a specific module
pytest tests/unit/apis/models/

# Run a specific test file
pytest tests/unit/apis/models/test_models.py
```

## Test Fixtures

Common test fixtures are defined in the test files. These fixtures provide sample data and mock objects for testing.

## Test Coverage

To run tests with coverage reporting:

```bash
# Run tests with coverage
pytest --cov=llama_stack tests/unit/

# Generate HTML coverage report
pytest --cov=llama_stack --cov-report=html tests/unit/
```

## Writing New Tests

When writing new tests:

1. Follow the existing structure and naming conventions
2. Use pytest fixtures for common test data
3. Use unittest.mock for mocking dependencies
4. Include docstrings for test classes and methods
5. Test both success and error cases
