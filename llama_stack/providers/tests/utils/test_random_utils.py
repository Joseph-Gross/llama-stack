# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import random
import numpy as np
import pytest

from llama_stack.utils.random_utils import (
    set_random_seed,
    get_random_generator,
    get_numpy_random_generator,
)

# Try to import torch if available
try:
    import torch
    from llama_stack.utils.random_utils import get_torch_random_generator
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


def test_set_random_seed():
    """Test that set_random_seed sets the seed for all random number generators."""
    # Set a fixed seed
    seed = 42
    set_random_seed(seed)
    
    # Get random numbers from Python's random module
    random_value1 = random.random()
    
    # Get random numbers from NumPy
    numpy_value1 = np.random.rand()
    
    # Reset the seed to the same value
    set_random_seed(seed)
    
    # Get random numbers again
    random_value2 = random.random()
    numpy_value2 = np.random.rand()
    
    # The values should be the same if the seed was set correctly
    assert random_value1 == random_value2
    assert numpy_value1 == numpy_value2


def test_get_random_generator():
    """Test that get_random_generator returns a random generator with a fixed seed."""
    # Create two random generators with the same seed
    seed = 42
    rng1 = get_random_generator(seed)
    rng2 = get_random_generator(seed)
    
    # Get random numbers from both generators
    values1 = [rng1.random() for _ in range(10)]
    values2 = [rng2.random() for _ in range(10)]
    
    # The values should be the same if the seed was set correctly
    assert values1 == values2
    
    # Create a random generator with a different seed
    rng3 = get_random_generator(seed + 1)
    values3 = [rng3.random() for _ in range(10)]
    
    # The values should be different
    assert values1 != values3


def test_get_numpy_random_generator():
    """Test that get_numpy_random_generator returns a NumPy random generator with a fixed seed."""
    # Create two NumPy random generators with the same seed
    seed = 42
    rng1 = get_numpy_random_generator(seed)
    rng2 = get_numpy_random_generator(seed)
    
    # Get random numbers from both generators
    values1 = rng1.random(10)
    values2 = rng2.random(10)
    
    # The values should be the same if the seed was set correctly
    np.testing.assert_array_equal(values1, values2)
    
    # Create a NumPy random generator with a different seed
    rng3 = get_numpy_random_generator(seed + 1)
    values3 = rng3.random(10)
    
    # The values should be different
    with pytest.raises(AssertionError):
        np.testing.assert_array_equal(values1, values3)


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
def test_get_torch_random_generator():
    """Test that get_torch_random_generator returns a PyTorch random generator with a fixed seed."""
    # Create two PyTorch random generators with the same seed
    seed = 42
    rng1 = get_torch_random_generator(seed)
    rng2 = get_torch_random_generator(seed)
    
    # Get random numbers from both generators
    values1 = torch.rand(10, generator=rng1)
    values2 = torch.rand(10, generator=rng2)
    
    # The values should be the same if the seed was set correctly
    torch.testing.assert_close(values1, values2)
    
    # Create a PyTorch random generator with a different seed
    rng3 = get_torch_random_generator(seed + 1)
    values3 = torch.rand(10, generator=rng3)
    
    # The values should be different
    with pytest.raises(AssertionError):
        torch.testing.assert_close(values1, values3)


def test_reproducibility_across_runs():
    """Test that random operations are reproducible across different runs."""
    # Set a fixed seed
    seed = 42
    set_random_seed(seed)
    
    # Generate random values
    random_values = [random.random() for _ in range(5)]
    numpy_values = np.random.rand(5).tolist()
    
    # Expected values (pre-computed with the same seed)
    expected_random_values = [0.6394267984578837, 0.025010755222666936, 0.27502931836911926, 0.22321073814882275, 0.7364712141640124]
    expected_numpy_values = [0.37454012, 0.95071431, 0.73199394, 0.59865848, 0.15601864]
    
    # Check that the values match the expected values
    assert random_values == pytest.approx(expected_random_values)
    assert numpy_values == pytest.approx(expected_numpy_values)
