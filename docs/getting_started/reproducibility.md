# Ensuring Reproducibility in Llama Stack

This guide explains how to ensure reproducibility of random operations in Llama Stack, which is essential for research and development.

## Why Reproducibility Matters

Reproducibility is a cornerstone of scientific research and reliable software development. In machine learning and AI applications, random operations are common and can lead to different results across runs if not properly controlled. Llama Stack provides utilities to ensure that random operations produce consistent results, enabling:

- Reproducible research experiments
- Reliable testing
- Consistent behavior across different environments
- Easier debugging and troubleshooting

## Using Random Seed Utilities

Llama Stack provides utilities for setting random seeds and creating isolated random number generators in the `llama_stack.utils.random_utils` module.

### Setting Global Random Seeds

To ensure reproducibility across all random operations, set a global random seed at the beginning of your script or application:

```python
from llama_stack.utils.random_utils import set_random_seed

# Set a fixed seed for reproducibility
set_random_seed(42)

# Now all random operations will be reproducible
```

This function sets the seed for:
- Python's `random` module
- NumPy's random number generator
- PyTorch's random number generator (if available)

### Using Isolated Random Generators

For more fine-grained control, you can create isolated random number generators with specific seeds:

```python
from llama_stack.utils.random_utils import (
    get_random_generator,
    get_numpy_random_generator,
)

# Create a Python random generator with a fixed seed
rng = get_random_generator(42)
random_values = [rng.random() for _ in range(5)]

# Create a NumPy random generator with a fixed seed
numpy_rng = get_numpy_random_generator(42)
numpy_values = numpy_rng.random(5)
```

If PyTorch is available, you can also create a PyTorch random generator:

```python
from llama_stack.utils.random_utils import get_torch_random_generator
import torch

# Create a PyTorch random generator with a fixed seed
torch_rng = get_torch_random_generator(42)
torch_values = torch.rand(5, generator=torch_rng)
```

## Best Practices for Reproducibility

1. **Set a global seed at the start of your application**:
   ```python
   from llama_stack.utils.random_utils import set_random_seed
   set_random_seed(42)
   ```

2. **Use isolated random generators for specific components**:
   ```python
   from llama_stack.utils.random_utils import get_random_generator
   
   class MyComponent:
       def __init__(self, seed=None):
           self.rng = get_random_generator(seed)
   ```

3. **Document the seed values used in your experiments**:
   ```python
   # Experiment with seed 42
   SEED = 42
   set_random_seed(SEED)
   
   # Log the seed value
   print(f"Running experiment with seed: {SEED}")
   ```

4. **Allow seed configuration in your applications**:
   ```python
   import argparse
   from llama_stack.utils.random_utils import set_random_seed
   
   parser = argparse.ArgumentParser()
   parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
   args = parser.parse_args()
   
   seed = set_random_seed(args.seed)
   print(f"Using seed: {seed}")
   ```

5. **For distributed applications, ensure consistent seed handling**:
   ```python
   def get_worker_seed(base_seed, worker_id):
       """Get a unique seed for each worker based on a base seed."""
       return base_seed + worker_id
   ```

## Example: Reproducible Vector Database Operations

Here's an example of using random seed utilities for vector database operations:

```python
from llama_stack.utils.random_utils import get_numpy_random_generator
import numpy as np

# Create a random generator with a fixed seed
rng = get_numpy_random_generator(42)

# Generate reproducible embeddings
embedding_dimension = 384
embeddings = np.array([rng.random(embedding_dimension).astype(np.float32) for _ in range(10)])

# Use these embeddings for vector database operations
```

## Testing Reproducibility

To verify that your code is reproducible, run the same code multiple times with the same seed and check that the results are identical:

```python
from llama_stack.utils.random_utils import set_random_seed
import numpy as np

def run_experiment(seed):
    set_random_seed(seed)
    return np.random.rand(5)

# Run the experiment twice with the same seed
results1 = run_experiment(42)
results2 = run_experiment(42)

# Check that the results are identical
np.testing.assert_array_equal(results1, results2)
```

By following these guidelines, you can ensure that your research and applications built with Llama Stack are reproducible and reliable.
