"""Composite filter for combining multiple filters"""

from enum import Enum
from typing import List, TypeVar, Generic, Optional, Dict, Any

from filters.base_filter import BaseFilter, FilterResult

T = TypeVar('T')


class FilterMode(Enum):
    """Filter combination mode"""
    AND = "and"  # All filters must pass
    OR = "or"    # At least one filter must pass
    XOR = "xor"  # Exactly one filter must pass


class CompositeFilter(BaseFilter[T], Generic[T]):
    """Combines multiple filters with configurable logic"""
    
    def __init__(self, filters: List[BaseFilter[T]], 
                 mode: FilterMode = FilterMode.AND,
                 name: Optional[str] = None):
        """
        Initialize composite filter
        
        Args:
            filters: List of filters to combine
            mode: How to combine filter results
            name: Optional filter name
        """
        super().__init__(name)
        
        if not filters:
            raise ValueError("At least one filter must be specified")
        
        self.filters = filters
        self.mode = mode
    
    def apply(self, item: T) -> FilterResult:
        """Apply all filters and combine results"""
        results = []
        reasons = []
        
        for filter_obj in self.filters:
            result = filter_obj.apply(item)
            results.append(result)
            if not result.passed and result.reason:
                reasons.append(f"{filter_obj.name}: {result.reason}")
        
        # Combine based on mode
        if self.mode == FilterMode.AND:
            passed = all(r.passed for r in results)
            if not passed:
                reason = "Not all filters passed: " + "; ".join(reasons)
            else:
                reason = "All filters passed"
                
        elif self.mode == FilterMode.OR:
            passed = any(r.passed for r in results)
            if not passed:
                reason = "No filters passed: " + "; ".join(reasons)
            else:
                reason = f"{sum(r.passed for r in results)} filter(s) passed"
                
        elif self.mode == FilterMode.XOR:
            passed_count = sum(r.passed for r in results)
            passed = passed_count == 1
            if passed_count == 0:
                reason = "No filters passed"
            elif passed_count > 1:
                reason = f"Multiple filters passed ({passed_count}), expected exactly 1"
            else:
                reason = "Exactly one filter passed"
        
        return FilterResult(
            passed=passed,
            reason=reason,
            metadata={
                'mode': self.mode.value,
                'filter_count': len(self.filters),
                'passed_count': sum(r.passed for r in results)
            }
        )
    
    def add_filter(self, filter_obj: BaseFilter[T]):
        """Add a filter to the composite"""
        self.filters.append(filter_obj)
    
    def remove_filter(self, filter_obj: BaseFilter[T]):
        """Remove a filter from the composite"""
        self.filters.remove(filter_obj)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get combined statistics from all filters"""
        stats = super().get_stats()
        
        # Add individual filter stats
        stats['filters'] = {}
        for filter_obj in self.filters:
            stats['filters'][filter_obj.name] = filter_obj.get_stats()
        
        return stats
    
    def reset_stats(self):
        """Reset statistics for all filters"""
        super().reset_stats()
        for filter_obj in self.filters:
            filter_obj.reset_stats()
    
    def __repr__(self) -> str:
        filter_names = [f.name for f in self.filters]
        return f"CompositeFilter(mode={self.mode.value}, filters={filter_names})"