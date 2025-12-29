#!/usr/bin/env python3
"""
Wrapper script for WhisperX that patches PyTorch 2.8+ compatibility issues.

PyTorch 2.8+ changed torch.load() to use weights_only=True by default, which
prevents loading models with omegaconf. This wrapper patches torch and pickle
before importing whisperx.
"""

import sys
import os
import pickle

# Set environment variables to disable weights_only checks
os.environ['TORCH_FORCE_WEIGHTS_ONLY'] = '0'
os.environ['PICKLE_DISABLE_WEIGHTS_ONLY'] = '1'

# Patch torch loading functions for PyTorch 2.8+ compatibility
try:
    import torch
    import torch.serialization
    from torch.serialization import _load as torch_load_impl

    # Register safe globals for omegaconf BEFORE any model loading
    try:
        import omegaconf
        from omegaconf import ListConfig, DictConfig
        if hasattr(torch.serialization, 'add_safe_globals'):
            torch.serialization.add_safe_globals([ListConfig, DictConfig])
    except (ImportError, AttributeError):
        pass

    # Strategy 1: Patch torch.serialization._load to remove weights_only from kwargs
    # before it reaches the Unpickler
    original_load = getattr(torch.serialization, '_load', None)
    if original_load:
        def patched_load(f, *args, **kwargs):
            # Remove weights_only before calling original function
            # This prevents it from being passed to Unpickler
            kwargs.pop('weights_only', None)
            return original_load(f, *args, **kwargs)
        torch.serialization._load = patched_load

    # Strategy 2: Patch torch.load as well
    original_torch_load = torch.load
    def patched_torch_load(f, *args, **kwargs):
        # Force weights_only=False
        kwargs['weights_only'] = False
        try:
            return original_torch_load(f, *args, **kwargs)
        except TypeError as e:
            # If we still get TypeError about weights_only, try without it
            if 'weights_only' in str(e):
                kwargs.pop('weights_only', None)
                return original_torch_load(f, *args, **kwargs)
            raise

    torch.load = patched_torch_load

    # Strategy 3: Patch pickle.Unpickler to ignore weights_only
    import pickle as pickle_module
    original_unpickler_init = pickle_module.Unpickler.__init__

    def patched_unpickler_init(self, *args, **kwargs):
        # Remove weights_only from kwargs if present
        kwargs.pop('weights_only', None)
        # Call original without weights_only
        original_unpickler_init(self, *args, **kwargs)

    pickle_module.Unpickler.__init__ = patched_unpickler_init

except (ImportError, AttributeError, TypeError) as e:
    # If patching fails, continue anyway
    pass

# Now import and run whisperx
from whisperx.__main__ import cli

if __name__ == "__main__":
    sys.exit(cli())
