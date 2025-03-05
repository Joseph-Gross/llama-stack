# Installation Guide for Llama Stack

This document provides detailed installation instructions for the Llama Stack project, designed to support interdisciplinary research collaboration.

## Prerequisites

- Python 3.10 or higher
- pip (Python package installer)
- git

## Installation Options

### 1. Standard Installation from PyPI

The simplest way to install Llama Stack is directly from PyPI:

```bash
pip install llama-stack
```

This will install the latest stable release of Llama Stack and its dependencies.

### 2. Development Installation from Source

For development or to access the latest features, install from source:

```bash
# Clone the repository
git clone https://github.com/meta-llama/llama-stack.git
cd llama-stack

# Install dependencies and the package in development mode
pip install -r requirements.txt
pip install -e .
```

### 3. Using the Setup Script

For a more automated setup, use the provided setup script:

```bash
# Clone the repository
git clone https://github.com/meta-llama/llama-stack.git
cd llama-stack

# Make the setup script executable
chmod +x setup.sh

# Run the setup script
./setup.sh
```

This script will:
- Create a virtual environment
- Install all required dependencies
- Set up pre-commit hooks
- Install the package in development mode

### 4. Using Conda

If you prefer to use Conda for environment management:

```bash
# Clone the repository
git clone https://github.com/meta-llama/llama-stack.git
cd llama-stack

# Create a conda environment from the provided configuration
conda env create -f environment.yml

# Activate the environment
conda activate llama-stack
```

### 5. Using Docker

For a containerized setup:

```bash
# Clone the repository
git clone https://github.com/meta-llama/llama-stack.git
cd llama-stack

# Build and start the containers
cd docker
docker-compose up
```

## Installing Optional Dependencies

Llama Stack has several optional dependency groups:

### Development Dependencies

```bash
pip install -r requirements-dev.txt
```

### Testing Dependencies

```bash
pip install "llama-stack[test]"
```

### Documentation Dependencies

```bash
pip install "llama-stack[docs]"
```

## Verifying Your Installation

To verify that Llama Stack is installed correctly:

```bash
# Check the installed version
python -c "import llama_stack; print(llama_stack.__version__)"

# Run a simple test
llama --version
```

## Troubleshooting

### Common Issues

1. **Missing Dependencies**: If you encounter errors about missing dependencies, try reinstalling the requirements:
   ```bash
   pip install -r requirements.txt
   ```

2. **Import Errors**: If you encounter import errors, make sure the package is installed in development mode:
   ```bash
   pip install -e .
   ```

3. **Version Conflicts**: If you encounter version conflicts, consider using a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -e .
   ```

### Getting Help

If you encounter any issues that aren't covered here, please:
1. Check the [documentation](https://llama-stack.readthedocs.io/)
2. Open an issue on the [GitHub repository](https://github.com/meta-llama/llama-stack/issues)
3. Join the [Discord community](https://discord.gg/llama-stack) for real-time help

## For Interdisciplinary Collaboration

If you're collaborating across disciplines and are new to Python or machine learning:

1. **Start with a Distribution**: Consider using one of the pre-configured distributions mentioned in the README.md, which provide a ready-to-use environment.

2. **Use the Docker Setup**: The Docker setup provides a consistent environment across different operating systems and configurations.

3. **Follow the Tutorials**: Check the documentation for tutorials and examples that demonstrate how to use Llama Stack for various research tasks.

4. **Join the Community**: The Discord community is a great place to ask questions and get help from other researchers and developers.
