# Installing Llama Stack

This guide provides instructions for installing Llama Stack in various environments, with a focus on supporting interdisciplinary research collaboration.

## Prerequisites

- Python 3.10 or higher
- pip (Python package installer)
- git

## Installation Options

### Standard Installation from PyPI

The simplest way to install Llama Stack is directly from PyPI:

```bash
pip install llama-stack
```

This will install the latest stable release of Llama Stack and its dependencies.

### Development Installation from Source

For development or to access the latest features, install from source:

```bash
# Clone the repository
git clone https://github.com/meta-llama/llama-stack.git
cd llama-stack

# Install dependencies and the package in development mode
pip install -r requirements.txt
pip install -e .
```

### Using the Setup Script

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

### Using Conda

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

### Using Docker

For a containerized setup:

```bash
# Clone the repository
git clone https://github.com/meta-llama/llama-stack.git
cd llama-stack

# Build and start the containers
cd docker
docker-compose up
```

## Verifying Your Installation

To verify that Llama Stack is installed correctly:

```bash
# Check the installed version
python -c "import llama_stack; print(llama_stack.__version__)"

# Run a simple test
llama --version
```

## Next Steps

After installation, you can:

1. Follow the [Quick Start Guide](index.html) to start using Llama Stack
2. Explore the [Jupyter Notebook](../getting_started.ipynb) for examples
3. Check out the [Zero-to-Hero Guide](../zero_to_hero_guide) for a comprehensive tutorial

## For Interdisciplinary Collaboration

If you're collaborating across disciplines and are new to Python or machine learning:

1. **Start with a Distribution**: Consider using one of the pre-configured distributions mentioned in the README.md, which provide a ready-to-use environment.

2. **Use the Docker Setup**: The Docker setup provides a consistent environment across different operating systems and configurations.

3. **Follow the Tutorials**: Check the documentation for tutorials and examples that demonstrate how to use Llama Stack for various research tasks.

4. **Join the Community**: The Discord community is a great place to ask questions and get help from other researchers and developers.
