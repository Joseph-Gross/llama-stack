# Reproducibility Guide for Llama Stack

This guide provides instructions and best practices for ensuring reproducible results when working with the Llama Stack framework.

## Table of Contents
- [Installation](#installation)
- [Setting Random Seeds](#setting-random-seeds)
- [Data Preprocessing](#data-preprocessing)
- [Model Training](#model-training)
- [Evaluation](#evaluation)

## Installation

### Using pip

```bash
# Clone the repository
git clone https://github.com/meta-llama/llama-stack.git
cd llama-stack

# Install the package
pip install -e .

# For development dependencies
pip install -e ".[dev]"

# For testing dependencies
pip install -e ".[test]"

# For documentation dependencies
pip install -e ".[docs]"
```

### Using conda

```bash
# Clone the repository
git clone https://github.com/meta-llama/llama-stack.git
cd llama-stack

# Create and activate conda environment
conda env create -f environment.yml
conda activate llama-stack

# Install the package in development mode
pip install -e .
```

## Setting Random Seeds

To ensure reproducible results across different runs, it's important to set random seeds for all libraries that use random number generators. The Llama Stack provides a utility function for this purpose:

```python
from llama_stack.utils import set_seed

# Set seed for reproducibility (default is 42)
set_seed(42)

# Now all random operations will be reproducible
```

This function sets seeds for:
- Python's `random` module
- NumPy's random number generator
- PyTorch's random number generators (if available)
- CUDA random number generators (if available)

### Reproducible DataLoaders

When working with PyTorch DataLoaders, you can use the `get_reproducible_dataloader` function to ensure consistent shuffling:

```python
from llama_stack.utils.reproducibility import get_reproducible_dataloader

# Create a reproducible dataloader
dataloader = get_reproducible_dataloader(
    dataset=your_dataset,
    batch_size=32,
    shuffle=True,
    seed=42
)
```

## Data Preprocessing

Consistent data preprocessing is crucial for reproducibility. Here are some best practices:

1. **Document all preprocessing steps**: Keep a record of all transformations applied to the data.
2. **Use version control for preprocessing scripts**: Track changes to preprocessing code.
3. **Save intermediate data**: Store processed data to avoid recomputing.
4. **Set random seeds**: Use the `set_seed` function before any random operations.

### Example Preprocessing Pipeline

```python
from llama_stack.utils import set_seed

# Set seed for reproducibility
set_seed(42)

def preprocess_data(raw_data_path, processed_data_path):
    """
    Preprocess raw data and save the processed data.
    
    Args:
        raw_data_path: Path to the raw data
        processed_data_path: Path to save the processed data
    """
    # Load raw data
    # Apply transformations
    # Save processed data
    pass
```

## Model Training

For reproducible model training:

1. **Set random seeds**: Use `set_seed` before training.
2. **Use deterministic algorithms**: Enable deterministic behavior in PyTorch.
3. **Fix the environment**: Document hardware, software versions, and configurations.
4. **Save model checkpoints**: Regularly save model states during training.

### Example Training Script

```python
from llama_stack.utils import set_seed

# Set seed for reproducibility
set_seed(42)

def train_model(model, dataloader, epochs=10):
    """
    Train a model with reproducible results.
    
    Args:
        model: The model to train
        dataloader: DataLoader with training data
        epochs: Number of training epochs
    """
    # Training loop
    pass
```

## Evaluation

For reproducible evaluation:

1. **Set random seeds**: Use `set_seed` before evaluation.
2. **Use consistent metrics**: Define and document evaluation metrics.
3. **Save evaluation results**: Store results for future comparison.

### Example Evaluation Script

```python
from llama_stack.utils import set_seed

# Set seed for reproducibility
set_seed(42)

def evaluate_model(model, dataloader):
    """
    Evaluate a model with reproducible results.
    
    Args:
        model: The model to evaluate
        dataloader: DataLoader with evaluation data
    
    Returns:
        Dictionary of evaluation metrics
    """
    # Evaluation logic
    pass
```

## Additional Resources

- [PyTorch Reproducibility Guide](https://pytorch.org/docs/stable/notes/randomness.html)
- [NumPy Random Generator](https://numpy.org/doc/stable/reference/random/index.html)
- [Llama Stack Documentation](https://llama-stack.readthedocs.io/)
