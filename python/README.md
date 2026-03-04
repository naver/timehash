# Timehash Python

Python implementation of Timehash for hierarchical time indexing.

## Installation

```bash
pip install timehash
```

## Usage

```python
from timehash import Timehash

# Create Timehash instance with default measures
th = Timehash()

# Generate query terms for a specific time
query_terms = th.get_query_terms(1430)  # 14:30
# Returns: ['12', '1214', '121430', '12143000', '1214300000']

# Generate index terms for a time range
index_terms = th.get_index_terms("1140", "2100")  # 11:40 - 21:00
# Returns: ['08113040', '081145', '12', '16', '2020']

# Custom measures
custom_th = Timehash(measures=[240, 60, 15, 5, 1])  # 4h, 1h, 15m, 5m, 1m
```

## Example

```python
from timehash import Timehash

th = Timehash()

# Business operating hours: 11:40 AM - 9:00 PM
keys = th.get_index_terms("1140", "2100")
print(f"Index keys: {keys}")
# Output: ['08113040', '081145', '12', '16', '2020']

# Query: Is business open at 2:30 PM?
query_keys = th.get_query_terms(1430)
print(f"Query keys: {query_keys}")
# Output: ['12', '1214', '121430', '12143000', '1214300000']

# Check if any query key matches any index key
is_open = any(key in keys for key in query_keys)
print(f"Business is open: {is_open}")
```
