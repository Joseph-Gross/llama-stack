# Setting Up the Llama Stack Development Environment

This guide provides instructions for setting up the development environment for Llama Stack, with a focus on supporting interdisciplinary research collaboration.

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

## Using Docker

For a containerized development environment:

```bash
# Navigate to the docker directory
cd docker

# Build and start the containers
docker-compose up
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

## For Interdisciplinary Collaboration

If you're collaborating across disciplines and are new to Python or machine learning:

1. **Use the Setup Script**: The setup script provides a simple way to set up the development environment.

2. **Use the Docker Setup**: The Docker setup provides a consistent environment across different operating systems and configurations.

3. **Start with the Examples**: Check the documentation for examples that demonstrate how to use Llama Stack for various research tasks.

4. **Join the Community**: The Discord community is a great place to ask questions and get help from other researchers and developers.
