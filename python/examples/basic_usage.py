#!/usr/bin/env python3
# Timehash
# Copyright (c) 2026-present NAVER Corp.
# Apache-2.0

"""
Basic usage example for Timehash.
"""

from timehash import Timehash


def main():
    # Create Timehash instance
    th = Timehash()
    
    print("=== Timehash Basic Usage Example ===\n")
    
    # Example 1: Generate index terms for business operating hours
    print("Example 1: Business operating hours (11:40 AM - 9:00 PM)")
    index_keys = th.get_index_terms("1140", "2100")
    print(f"Index keys: {index_keys}")
    print(f"Number of keys: {len(index_keys)}")
    print(f"Compared to minute-level: 560 keys → {len(index_keys)} keys "
          f"({(1 - len(index_keys)/560)*100:.1f}% reduction)\n")
    
    # Example 2: Generate query terms for a specific time
    print("Example 2: Query for businesses open at 2:30 PM")
    query_keys = th.get_query_terms(1430)
    print(f"Query keys: {query_keys}\n")
    
    # Example 3: Check if business is open at query time
    print("Example 3: Check if business is open at query time")
    is_open = any(key in index_keys for key in query_keys)
    print(f"Business open at 14:30: {is_open}")
    
    # Example 4: Simple range (12:00 PM - 1:00 PM)
    print("\nExample 4: Simple range (12:00 PM - 1:00 PM)")
    simple_keys = th.get_index_terms("1200", "1300")
    print(f"Index keys: {simple_keys}")
    
    # Example 5: Custom measures
    print("\nExample 5: Custom measures")
    custom_th = Timehash(measures=[240, 60, 15, 5, 1])  # 4h, 1h, 15m, 5m, 1m
    custom_keys = custom_th.get_index_terms("1200", "1300")
    print(f"Index keys with custom measures: {custom_keys}")


if __name__ == "__main__":
    main()
