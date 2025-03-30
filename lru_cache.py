from collections import OrderedDict
from typing import Any, Optional, TypeVar, Generic

T = TypeVar('T')  # Generic type for stored models

class LRUCache(Generic[T]):
    """
    Least Recently Used (LRU) Cache implementation using OrderedDict.
    Automatically manages model instances by keeping most recently used ones
    and discarding least recently used ones when capacity is reached.
    """
    
    def __init__(self, capacity: int):
        """
        Initialize a new LRU Cache with specified capacity.
        
        Args:
            capacity: Maximum number of models to store in the cache
        """
        self.capacity = max(1, capacity)  # Ensure capacity is at least 1
        self.cache = OrderedDict()  # Ordered dictionary to track usage order
    
    def get(self, key: str) -> Optional[T]:
        """
        Retrieve a model from the cache and mark it as recently used.
        
        Args:
            key: Identifier for the model
            
        Returns:
            The model if found, None otherwise
        """
        if key not in self.cache:
            return None
            
        # Move this item to the end (most recently used)
        value = self.cache.pop(key)
        self.cache[key] = value
        return value
    
    def put(self, key: str, value: T) -> None:
        """
        Add or update a model in the cache.
        
        Args:
            key: Identifier for the model
            value: The model to store
        """
        # If key exists, remove it first to update its position
        if key in self.cache:
            self.cache.pop(key)
        # If we're at capacity, remove the least recently used item (first item)
        elif len(self.cache) >= self.capacity:
            self.cache.popitem(last=False)
        # Add the new item as most recently used
        self.cache[key] = value
    
    def __len__(self) -> int:
        """Return the number of items in the cache."""
        return len(self.cache)
    
    def clear(self) -> None:
        """Clear all items from the cache."""
        self.cache.clear()
    
    def keys(self):
        """Return all keys in the cache, ordered from least to most recently used."""
        return self.cache.keys()
    
    def values(self):
        """Return all values in the cache, ordered from least to most recently used."""
        return self.cache.values()
    
    def items(self):
        """Return all (key, value) pairs in the cache, ordered from least to most recently used."""
        return self.cache.items()
