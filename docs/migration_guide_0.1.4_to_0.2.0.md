# Llama Stack Migration Guide: 0.1.4 to 0.2.0

## Overview

This guide outlines the steps to upgrade Llama Stack from version 0.1.4 to 0.2.0. This release focuses on security improvements, code quality enhancements, test coverage improvements, and dependency updates.

## Breaking Changes

### Security Improvements

- **Server Binding**: The server now binds to `localhost` by default instead of `0.0.0.0`. This change improves security by not exposing the server to all network interfaces by default.
- **Subprocess Calls**: All subprocess calls now require explicit `shell=False` parameter to prevent shell injection vulnerabilities.
- **Temporary Directory Usage**: Hardcoded temporary directory paths have been replaced with more secure alternatives.
- **Assert Statements**: Assert statements in production code have been replaced with proper runtime checks.

### Code Quality Improvements

- **Type Checking**: Fixed type checking issues in server.py related to exception handling.
- **Error Handling**: Improved error handling consistency in server.py.
- **Try-Except-Continue Patterns**: Replaced with more specific exception handling.

### Dependency Updates

- Updated dependencies:
  - beautifulsoup4: 4.12.3 → 4.13.3
  - numpy: 2.2.3 → 2.2.4
  - pytz: 2025.1 → 2025.2
  - setuptools: 75.8.0 → 76.0.0
  - huggingface-hub: 0.29.0 → 0.30.1

## Upgrade Steps

### 1. Update Dependencies

```bash
# Using pip
pip install --upgrade llama-stack==0.2.0

# Using uv
uv pip install --upgrade llama-stack==0.2.0
```

### 2. Update Server Configuration

If you were binding to all interfaces (0.0.0.0), you now need to explicitly specify the host:

```bash
# Command line
llama --host 0.0.0.0 ...

# Environment variable
export LLAMA_STACK_HOST=0.0.0.0
```

### 3. Update Subprocess Calls

If you were using subprocess calls in your code, ensure they have `shell=False`:

```python
# Before
subprocess.run(command, shell=True)

# After
subprocess.run(command, shell=False)
```

If your command was a string that relied on shell features, convert it to a list:

```python
# Before
subprocess.run("grep 'pattern' file.txt | wc -l", shell=True)

# After
import shlex
command = shlex.split("grep 'pattern' file.txt")
result = subprocess.run(command, shell=False, capture_output=True)
# Process the output separately
```

### 4. Update Temporary Directory Usage

Replace hardcoded temporary directory paths with Python's `tempfile` module:

```python
# Before
config = SqliteKVStoreConfig(db_path="/tmp/test_registry.db")

# After
import tempfile
import os

temp_dir = tempfile.gettempdir()
db_path = os.path.join(temp_dir, "test_registry.db")
config = SqliteKVStoreConfig(db_path=db_path)
```

### 5. Replace Assert Statements

Replace assert statements with proper runtime checks:

```python
# Before
assert method_name in self.routes, f"Unknown endpoint: {method_name}"

# After
if method_name not in self.routes:
    raise ValueError(f"Unknown endpoint: {method_name}")
```

## Verification

### 1. Run Tests

Run the test suite to verify the upgrade:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=llama_stack
```

### 2. Verify Server Binding

Start the server and verify it's binding to the correct interface:

```bash
# Start server with default settings (localhost)
llama --template tgi

# Check binding
netstat -tuln | grep 8321
```

### 3. Verify API Functionality

Test the API endpoints to ensure they're working correctly:

```bash
# Test inference endpoint
curl -X POST http://localhost:8321/v1/inference/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, world!", "max_tokens": 10}'
```

## Troubleshooting

### Server Not Accessible from Other Machines

If you need to access the server from other machines, explicitly set the host:

```bash
llama --host 0.0.0.0 --template tgi
```

### Subprocess Errors

If you encounter errors with subprocess calls after upgrading:

1. Check if your command relies on shell features (pipes, redirects, etc.)
2. Convert string commands to lists using `shlex.split()`
3. For complex shell commands, consider using a shell script file and executing it with `subprocess.run(["sh", "script.sh"], shell=False)`

## Additional Resources

- [Full Changelog](https://github.com/meta-llama/llama-stack/releases/tag/v0.2.0)
- [Security Best Practices](https://github.com/meta-llama/llama-stack/blob/main/SECURITY.md)
- [API Documentation](https://github.com/meta-llama/llama-stack/blob/main/docs/api/README.md)
