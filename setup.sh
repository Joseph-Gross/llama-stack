#!/bin/bash
# Setup script for llama-stack
# This script sets up the development environment for llama-stack

set -e  # Exit on error

# Print header
echo "====================================="
echo "Setting up llama-stack environment"
echo "====================================="

# Check Python version
python_version=$(python --version)
echo "Using $python_version"
if [[ $python_version != *"Python 3.10"* ]]; then
    echo "Warning: llama-stack is tested with Python 3.10. Your version may not be compatible."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Install development dependencies
echo "Installing development dependencies..."
pip install -r requirements-dev.txt

# Install the package in development mode
echo "Installing llama-stack in development mode..."
pip install -e .

# Set up pre-commit hooks
echo "Setting up pre-commit hooks..."
pre-commit install

echo "====================================="
echo "Setup complete!"
echo "====================================="
echo "To activate the environment, run:"
echo "  source venv/bin/activate"
echo
echo "To run tests, use:"
echo "  pytest"
echo
echo "To run linting, use:"
echo "  ruff check ."
echo "  black --check ."
echo "  mypy ."
echo "====================================="
