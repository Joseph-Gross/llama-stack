# Setting Up the Llama Stack Environment

This document provides instructions for setting up the development environment for the Llama Stack project.

## Prerequisites

- Python 3.10 or higher
- pip (Python package installer)
- git

## Quick Setup

For a quick setup, you can use the provided setup script:

```bash
# Clone the repository (if you haven't already)
git clone https://github.com/meta-llama/llama-stack.git
cd llama-stack

# Make the setup script executable
chmod +x setup.sh

# Run the setup script
./setup.sh
```

This script will:
1. Create a virtual environment
2. Install all required dependencies
3. Set up pre-commit hooks
4. Install the package in development mode

## Manual Setup

If you prefer to set up the environment manually, follow these steps:

### 1. Create a Virtual Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On Unix or MacOS:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install base dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Install the package in development mode
pip install -e .
```

### 3. Set Up Pre-commit Hooks

```bash
pre-commit install
```

## Using Conda

If you prefer to use Conda for environment management, you can use the provided `environment.yml` file:

```bash
# Create a conda environment
conda env create -f environment.yml

# Activate the environment
conda activate llama-stack
```

## Running Tests

To run the tests, use:

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=llama_stack

# Run specific test files
pytest llama_stack/providers/tests/vector_io/test_sqlite_vec_error_handling.py
pytest llama_stack/providers/tests/agents/test_agent_instance_error_handling.py
```

## Running Linting

To run linting checks, use:

```bash
# Run ruff
ruff check .

# Run black
black --check .

# Run mypy
mypy .
```

## Troubleshooting

### Common Issues

1. **Missing Dependencies**: If you encounter errors about missing dependencies, try reinstalling the requirements:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

2. **Import Errors**: If you encounter import errors, make sure the package is installed in development mode:
   ```bash
   pip install -e .
   ```

3. **Test Failures**: If tests are failing, check that you have all the required dependencies and that your environment is properly set up.

### Getting Help

If you encounter any issues that aren't covered here, please open an issue on the GitHub repository.
