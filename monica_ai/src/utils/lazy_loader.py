"""
Lazy Module Loader for Monica AI
Properly defers heavy module imports until first use while maintaining full functionality.

This implementation is based on the MLflow/wandb LazyLoader pattern which:
1. Creates a proxy module that looks like the real module
2. Only imports the actual module when an attribute is first accessed
3. Caches the module after first load for subsequent accesses
4. Updates sys.modules and parent namespace for proper Python import semantics

This allows Monica to start quickly while still having access to all features
like MediaPipe, TensorFlow, DeepFace, etc. when they are actually needed.

Author: Monica AI
Date: December 2025
"""

import importlib
import sys
import types
from typing import Any, Dict, Optional


class LazyLoader(types.ModuleType):
    """
    Lazy module loader that defers import until first attribute access.
    
    This class creates a proxy module that:
    - Appears as a normal module to Python
    - Only imports the actual module when first accessed
    - Caches the loaded module for efficiency
    - Properly updates sys.modules and parent namespace
    
    Usage:
        # Instead of: import heavy_module
        heavy_module = LazyLoader('heavy_module', globals(), 'heavy_module')
        
        # The module is NOT loaded yet
        # It will be loaded on first access:
        result = heavy_module.some_function()  # Module loads here
    """
    
    def __init__(
        self,
        local_name: str,
        parent_module_globals: Dict[str, Any],
        name: str,
        on_load_callback: Optional[callable] = None
    ):
        """
        Initialize the lazy loader.
        
        Args:
            local_name: The name used to reference this module in the parent
            parent_module_globals: The globals() dict of the importing module
            name: The full module path (e.g., 'mediapipe' or 'tensorflow.keras')
            on_load_callback: Optional callback to run after module loads
        """
        self._local_name = local_name
        self._parent_module_globals = parent_module_globals
        self._module: Optional[types.ModuleType] = None
        self._on_load_callback = on_load_callback
        self._load_error: Optional[Exception] = None
        super().__init__(str(name))
    
    def _load(self) -> types.ModuleType:
        """
        Load the actual module and update caches.
        
        Returns:
            The loaded module
            
        Raises:
            ImportError: If the module cannot be imported
        """
        # Return cached module if already loaded
        if self._module is not None:
            return self._module
        
        # Re-raise previous error if import already failed
        if self._load_error is not None:
            raise self._load_error
        
        try:
            # Import the actual module
            print(f"[LAZY] Loading {self.__name__}...")
            module = importlib.import_module(self.__name__)
            
            # Update parent module's namespace
            self._parent_module_globals[self._local_name] = module
            
            # Update sys.modules for proper caching
            sys.modules[self._local_name] = module
            
            # Update this proxy's __dict__ for efficient subsequent lookups
            self.__dict__.update(module.__dict__)
            
            # Cache the module
            self._module = module
            
            # Run callback if provided
            if self._on_load_callback:
                self._on_load_callback(module)
            
            print(f"[LAZY] {self.__name__} loaded successfully")
            return module
            
        except Exception as e:
            self._load_error = e
            print(f"[LAZY] Failed to load {self.__name__}: {e}")
            raise
    
    def __getattr__(self, item: str) -> Any:
        """
        Load module on first attribute access.
        
        Args:
            item: The attribute name being accessed
            
        Returns:
            The attribute from the loaded module
        """
        module = self._load()
        return getattr(module, item)
    
    def __dir__(self):
        """Return directory of the loaded module."""
        module = self._load()
        return dir(module)
    
    def __repr__(self):
        """Return string representation."""
        if self._module is None:
            return f"<LazyLoader '{self.__name__}' (not loaded yet)>"
        return repr(self._module)
    
    @property
    def is_loaded(self) -> bool:
        """Check if the module has been loaded."""
        return self._module is not None


def lazy_import(
    module_name: str,
    parent_globals: Dict[str, Any],
    local_name: Optional[str] = None,
    on_load: Optional[callable] = None
) -> LazyLoader:
    """
    Convenience function to create a lazy import.
    
    Args:
        module_name: Full module path (e.g., 'mediapipe')
        parent_globals: Pass globals() from the importing module
        local_name: Local name to use (defaults to module_name)
        on_load: Optional callback when module loads
        
    Returns:
        LazyLoader proxy for the module
        
    Example:
        # In your module:
        mp = lazy_import('mediapipe', globals())
        
        # Later, when you actually use it:
        hands = mp.solutions.hands.Hands()  # Module loads here
    """
    if local_name is None:
        # Use the last part of the module name
        local_name = module_name.split('.')[-1]
    
    return LazyLoader(local_name, parent_globals, module_name, on_load)


def lazy_import_from(
    module_name: str,
    attribute: str,
    parent_globals: Dict[str, Any],
    local_name: Optional[str] = None
) -> 'LazyAttribute':
    """
    Lazy import a specific attribute from a module.
    
    Args:
        module_name: Full module path
        attribute: Attribute to import from the module
        parent_globals: Pass globals() from the importing module
        local_name: Local name to use (defaults to attribute name)
        
    Returns:
        LazyAttribute proxy
        
    Example:
        # Instead of: from mediapipe.solutions import hands
        hands = lazy_import_from('mediapipe.solutions', 'hands', globals())
    """
    if local_name is None:
        local_name = attribute
    
    return LazyAttribute(module_name, attribute, parent_globals, local_name)


class LazyAttribute:
    """
    Lazy loader for a specific attribute from a module.
    
    This is useful for 'from X import Y' style imports.
    """
    
    def __init__(
        self,
        module_name: str,
        attribute: str,
        parent_globals: Dict[str, Any],
        local_name: str
    ):
        self._module_name = module_name
        self._attribute = attribute
        self._parent_globals = parent_globals
        self._local_name = local_name
        self._loaded_attr = None
        self._load_error = None
    
    def _load(self):
        """Load the attribute from the module."""
        if self._loaded_attr is not None:
            return self._loaded_attr
        
        if self._load_error is not None:
            raise self._load_error
        
        try:
            print(f"[LAZY] Loading {self._attribute} from {self._module_name}...")
            module = importlib.import_module(self._module_name)
            attr = getattr(module, self._attribute)
            
            # Update parent namespace
            self._parent_globals[self._local_name] = attr
            
            self._loaded_attr = attr
            return attr
            
        except Exception as e:
            self._load_error = e
            raise
    
    def __getattr__(self, item: str) -> Any:
        """Load and get attribute."""
        loaded = self._load()
        return getattr(loaded, item)
    
    def __call__(self, *args, **kwargs):
        """Allow calling if the attribute is callable."""
        loaded = self._load()
        return loaded(*args, **kwargs)
    
    def __repr__(self):
        if self._loaded_attr is None:
            return f"<LazyAttribute '{self._attribute}' from '{self._module_name}' (not loaded)>"
        return repr(self._loaded_attr)


# Pre-defined lazy loaders for common heavy modules
def get_lazy_mediapipe(parent_globals: Dict[str, Any]) -> LazyLoader:
    """Get lazy loader for MediaPipe."""
    return lazy_import('mediapipe', parent_globals, 'mp')


def get_lazy_tensorflow(parent_globals: Dict[str, Any]) -> LazyLoader:
    """Get lazy loader for TensorFlow."""
    return lazy_import('tensorflow', parent_globals, 'tf')


def get_lazy_torch(parent_globals: Dict[str, Any]) -> LazyLoader:
    """Get lazy loader for PyTorch."""
    return lazy_import('torch', parent_globals)


def get_lazy_deepface(parent_globals: Dict[str, Any]) -> LazyLoader:
    """Get lazy loader for DeepFace."""
    return lazy_import('deepface', parent_globals)


# Test
if __name__ == "__main__":
    import time
    
    print("Testing LazyLoader...")
    print()
    
    # Create lazy loader for numpy (as a test)
    start = time.perf_counter()
    np = lazy_import('numpy', globals())
    print(f"LazyLoader created in {time.perf_counter() - start:.4f}s")
    print(f"Module loaded: {np.is_loaded}")
    print()
    
    # Access an attribute - this triggers the load
    print("Accessing np.array...")
    start = time.perf_counter()
    arr = np.array([1, 2, 3])
    print(f"First access took {time.perf_counter() - start:.4f}s")
    print(f"Result: {arr}")
    print(f"Module loaded: {np.is_loaded}")
    print()
    
    # Subsequent access should be fast
    print("Second access...")
    start = time.perf_counter()
    arr2 = np.zeros(5)
    print(f"Second access took {time.perf_counter() - start:.6f}s")
    print(f"Result: {arr2}")
    
    print()
    print("[OK] LazyLoader test complete!")
