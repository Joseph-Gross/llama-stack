# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

"""
Utilities for ensuring reproducibility in experiments and model training.

This module provides functions to set random seeds across different libraries
and configure deterministic behavior for reproducible results.
"""

from __future__ import annotations

import random
from typing import Any, Optional

import numpy as np


def set_seed(seed: int = 42) -> None:
    """
    Set seed for reproducibility across multiple libraries.
    
    This function sets the seed for the Python random module and NumPy.
    If PyTorch is available, it also sets PyTorch seeds and configures
    deterministic behavior.
    
    Args:
        seed: Integer seed for random number generators. Default is 42.
    """
    random.seed(seed)
    np.random.seed(seed)
    
    # Try to set PyTorch seed if available
    try:
        import torch
        
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            # For deterministic behavior
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        # PyTorch not available, skip PyTorch-specific seed setting
        pass


def get_reproducible_dataloader(
    dataset: Any,
    batch_size: int,
    shuffle: bool = True,
    seed: Optional[int] = None,
    **kwargs
) -> Any:
    """
    Create a reproducible PyTorch DataLoader with consistent shuffling.
    
    When shuffle=True and seed is provided, this ensures that the data
    is shuffled in a reproducible way across different runs.
    
    Args:
        dataset: PyTorch Dataset object
        batch_size: Number of samples in each batch
        shuffle: Whether to shuffle the dataset
        seed: Random seed for the sampler. If None, no seed is set.
        **kwargs: Additional arguments to pass to DataLoader
        
    Returns:
        A PyTorch DataLoader configured for reproducibility
        
    Raises:
        ImportError: If PyTorch is not available
    """
    try:
        import torch
        from torch.utils.data import DataLoader, RandomSampler
        
        if shuffle and seed is not None:
            # Use a seeded RandomSampler for reproducible shuffling
            generator = torch.Generator()
            if seed is not None:
                generator.manual_seed(seed)
            sampler = RandomSampler(dataset, replacement=False, generator=generator)
            return DataLoader(dataset, batch_size=batch_size, sampler=sampler, **kwargs)
        else:
            # Use regular DataLoader
            return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle, **kwargs)
    except ImportError:
        raise ImportError("PyTorch is required for get_reproducible_dataloader")
