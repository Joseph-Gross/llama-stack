# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

"""
Utilities for random number generation with seed setting for reproducibility.
"""

import random
import os
from typing import Optional, Union, Any

import numpy as np

# Try to import torch if available
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


def set_random_seed(seed: Optional[int] = None, deterministic: bool = True) -> int:
    """
    Set random seed for Python's random module, NumPy, and PyTorch (if available).
    
    This function ensures reproducibility across different runs by setting the same
    seed for all random number generators used in the codebase.
    
    Args:
        seed: The random seed to use. If None, a random seed will be generated.
        deterministic: If True, sets PyTorch to use deterministic algorithms.
            This may impact performance but ensures reproducibility.
    
    Returns:
        The seed that was set.
    """
    if seed is None:
        # Generate a random seed if none is provided
        seed = int.from_bytes(os.urandom(4), byteorder="little")
    
    # Set seed for Python's random module
    random.seed(seed)
    
    # Set seed for NumPy
    np.random.seed(seed)
    
    # Set seed for PyTorch if available
    if TORCH_AVAILABLE:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)  # For multi-GPU setups
        
        if deterministic:
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    
    return seed


def get_random_generator(seed: Optional[int] = None) -> random.Random:
    """
    Get a random number generator with a specific seed.
    
    This function creates a new instance of Python's random.Random class
    with the specified seed, allowing for isolated random number generation
    that doesn't affect the global random state.
    
    Args:
        seed: The random seed to use. If None, a random seed will be generated.
    
    Returns:
        A random number generator instance.
    """
    if seed is None:
        # Generate a random seed if none is provided
        seed = int.from_bytes(os.urandom(4), byteorder="little")
    
    return random.Random(seed)


def get_numpy_random_generator(seed: Optional[int] = None) -> np.random.Generator:
    """
    Get a NumPy random number generator with a specific seed.
    
    This function creates a new instance of NumPy's random Generator class
    with the specified seed, allowing for isolated random number generation
    that doesn't affect the global NumPy random state.
    
    Args:
        seed: The random seed to use. If None, a random seed will be generated.
    
    Returns:
        A NumPy random generator instance.
    """
    if seed is None:
        # Generate a random seed if none is provided
        seed = int.from_bytes(os.urandom(4), byteorder="little")
    
    return np.random.Generator(np.random.PCG64(seed))


if TORCH_AVAILABLE:
    def get_torch_random_generator(seed: Optional[int] = None) -> torch.Generator:
        """
        Get a PyTorch random number generator with a specific seed.
        
        This function creates a new instance of PyTorch's Generator class
        with the specified seed, allowing for isolated random number generation
        that doesn't affect the global PyTorch random state.
        
        Args:
            seed: The random seed to use. If None, a random seed will be generated.
        
        Returns:
            A PyTorch random generator instance.
        """
        if seed is None:
            # Generate a random seed if none is provided
            seed = int.from_bytes(os.urandom(4), byteorder="little")
        
        generator = torch.Generator()
        generator.manual_seed(seed)
        return generator
