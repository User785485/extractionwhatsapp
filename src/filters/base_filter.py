"""Base filter interface"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, Dict, Any
from dataclasses import dataclass

T = TypeVar('T')


@dataclass
class FilterResult:
    """Result of filter application"""
    passed: bool
    reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseFilter(ABC, Generic[T]):
    """Abstract base class for filters"""
    
    def __init__(self, name: Optional[str] = None):
        """
        Initialize filter
        
        Args:
            name: Optional filter name for logging
        """
        self.name = name or self.__class__.__name__
        self._stats = {
            'total_evaluated': 0,
            'passed': 0,
            'failed': 0
        }
    
    @abstractmethod
    def apply(self, item: T) -> FilterResult:
        """
        Apply filter to an item
        
        Args:
            item: Item to filter
            
        Returns:
            FilterResult indicating if item passed filter
        """
        pass
    
    def filter(self, item: T) -> bool:
        """
        Simple boolean filter interface
        
        Args:
            item: Item to filter
            
        Returns:
            True if item passes filter
        """
        result = self.apply(item)
        self._update_stats(result)
        return result.passed
    
    def filter_many(self, items: list[T]) -> list[T]:
        """
        Filter a list of items
        
        Args:
            items: List of items to filter
            
        Returns:
            List of items that passed the filter
        """
        return [item for item in items if self.filter(item)]
    
    def _update_stats(self, result: FilterResult):
        """Update filter statistics"""
        self._stats['total_evaluated'] += 1
        if result.passed:
            self._stats['passed'] += 1
        else:
            self._stats['failed'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get filter statistics"""
        stats = self._stats.copy()
        if stats['total_evaluated'] > 0:
            stats['pass_rate'] = stats['passed'] / stats['total_evaluated']
        else:
            stats['pass_rate'] = 0.0
        return stats
    
    def reset_stats(self):
        """Reset filter statistics"""
        self._stats = {
            'total_evaluated': 0,
            'passed': 0,
            'failed': 0
        }
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"