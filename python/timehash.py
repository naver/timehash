# Timehash
# Copyright (c) 2026-present NAVER Corp.
# Apache-2.0

"""
Timehash: Hierarchical time indexing for efficient business hours search.

Timehash generates hierarchical hash keys for time ranges, enabling efficient
temporal filtering in search systems with minimal index overhead.
"""

from typing import List


class Timehash:
    """
    Timehash generates hierarchical hash keys for time ranges.
    
    The default measures are [400, 100, 15, 5, 1] representing:
    - 400 minutes (4 hours)
    - 100 minutes (1 hour 40 minutes, but treated as 1 hour)
    - 15 minutes
    - 5 minutes
    - 1 minute
    """
    
    def __init__(self, measures: List[int] = None):
        """
        Initialize Timehash with optional custom measures.
        
        Args:
            measures: List of time measures in minutes. Default: [400, 100, 15, 5, 1]
        """
        self.measures = measures if measures is not None else [400, 100, 15, 5, 1]
    
    def get_query_terms(self, hhmm: int) -> List[str]:
        """
        Generate query terms for a given time.
        
        Args:
            hhmm: Time in hhmm format (e.g., 1720 for 17:20)
            
        Returns:
            List of hierarchical hash keys for the query time
        """
        terms = []
        
        if hhmm > 10000:
            return terms
        
        for measure in self.measures:
            target = hhmm
            
            if measure >= 100:
                target //= 100
                measure_val = measure // 100
            else:
                target %= 100
                measure_val = measure
            
            key = (target // measure_val) * measure_val
            term = self._two_digit_term(key)
            
            if not terms:
                terms.append(term)
            else:
                terms.append(terms[-1] + term)
        
        return terms
    
    def get_index_terms(self, from_time: str, to_time: str) -> List[str]:
        """
        Generate index terms for a time range.
        
        Args:
            from_time: Start time in hhmm format (e.g., "1140")
            to_time: End time in hhmm format (e.g., "2100")
            
        Returns:
            List of hierarchical hash keys covering the time range
        """
        terms = []
        from_int = int(from_time)
        to_int = int(to_time)
        self._cover(terms, 0, "", from_int, to_int)
        return terms
    
    def _two_digit_term(self, key: int) -> str:
        """Convert a key to two-digit string representation."""
        if key >= 100:
            key //= 100
        
        return f"{key // 10}{key % 10}"
    
    def _cover(self, terms: List[str], measure_index: int, parent_key: str, 
               from_time: int, to_time: int) -> None:
        """
        Recursively generate keys for a time range.
        
        Args:
            terms: List to append generated keys
            measure_index: Current level in the hierarchy
            parent_key: Key from parent level
            from_time: Start time (integer in hhmm format)
            to_time: End time (integer in hhmm format)
        """
        if measure_index >= len(self.measures):
            return
        
        measure = self.measures[measure_index]
        from_val = from_time
        to_val = to_time
        
        if measure < 100:
            from_val %= 100
            to_val %= 100
            if to_val == 0:
                to_val = 60
        
        for i in range(from_val // measure, (to_val // measure) + 1):
            key = measure * i
            
            if from_val <= key and key + measure <= to_val:
                terms.append(parent_key + self._two_digit_term(key))
            elif key < from_val < key + measure:
                self._cover(terms, measure_index + 1, 
                           parent_key + self._two_digit_term(key),
                           from_val, min(key + measure, to_val))
            elif key < to_val < key + measure:
                self._cover(terms, measure_index + 1,
                           parent_key + self._two_digit_term(key),
                           key, to_val)
