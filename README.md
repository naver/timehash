# Timehash

Hierarchical time indexing for efficient business hours search.

Timehash generates hierarchical hash keys for time ranges, enabling efficient temporal filtering in search systems with minimal index overhead. It achieves O(log T) space complexity compared to O(T) in naive minute-level indexing while maintaining 100% precision and recall.

## Features

- **Hierarchical Multi-Resolution**: Decomposes time ranges into hierarchical buckets at multiple resolutions
- **Minimal Index Size**: Reduces index terms by 97% compared to minute-level indexing
- **100% Precision & Recall**: Guarantees zero false positives and zero false negatives
- **Human-Readable Keys**: Numeric encoding that directly represents time values (e.g., "0809" = 8:09 AM)
- **Flexible Configuration**: Supports customizable hierarchical levels for different applications

## Quick Start

### Python

```python
from timehash import Timehash

th = Timehash()
keys = th.get_index_terms("1140", "2100")  # 11:40 AM - 9:00 PM
# Returns: ['08113040', '081145', '12', '16', '2020']
```

### Java

```java
import com.naver.timehash.Timehash;

Timehash th = new Timehash();
List<String> keys = th.getIndexTerms("1140", "2100");
```

### Go

```go
import "github.com/naver/timehash"

th := timehash.New()
keys, _ := th.GetIndexTerms("1140", "2100")
```

### JavaScript

```javascript
const th = new Timehash();
const keys = th.getIndexTerms('1140', '2100');
```

### C++

```cpp
#include "timehash.hpp"

Timehash th;
std::vector<std::string> keys = th.getIndexTerms("1140", "2100");
```

### Rust

```rust
use timehash::Timehash;

let th = Timehash::new();
let keys = th.get_index_terms("1140", "2100");
```

### Kotlin

```kotlin
import com.naver.timehash.Timehash

val th = Timehash()
val keys = th.getIndexTerms("1140", "2100")
```

### Scala

```scala
import com.naver.timehash.Timehash

val th = Timehash()
val keys = th.getIndexTerms("1140", "2100")
```

## Algorithm Overview

Timehash uses a five-level hierarchy (4h, 1h, 15m, 5m, 1m) to decompose time ranges:

- **Level 1 (4-hour blocks)**: Covers large contiguous time blocks efficiently
- **Level 2 (1-hour blocks)**: Matches natural business hour boundaries
- **Level 3 (15-minute blocks)**: Provides quarter-hour precision
- **Level 4 (5-minute blocks)**: Fine-grained precision for edge cases
- **Level 5 (1-minute blocks)**: Maximum precision for exact time matching

For a restaurant operating 11:40 AM - 9:00 PM, Timehash generates 5 keys:
`{08113040, 081145, 12, 16, 2020}` instead of 560 keys for minute-level indexing.

### How It Works

1. **Index Term Generation**: For a time range `[start, end]`, Timehash recursively decomposes it at each level, selecting the largest possible block that fits within the remaining range.

2. **Query Term Generation**: For a query time `t`, Timehash generates keys at all hierarchy levels, creating a path from coarse to fine granularity (e.g., `["12", "1214", "121430", "12143030", "1214303030"]` for 14:30).

3. **Matching**: A document matches a query if any query key appears in the document's index key set. This ensures 100% recall (no false negatives) and 100% precision (no false positives).

### Complexity

- **Space Complexity**: O(log T) where T is the range length in minutes
- **Time Complexity**: O(log T) for both index and query term generation
- **Comparison**: Naive minute-level indexing requires O(T) space

For details, proofs, and experiments, see the accompanying paper.

## Documentation

- [Python](python/README.md)
- [Java](java/README.md)
- [Go](go/README.md)
- [JavaScript](javascript/README.md)
- [C++](cpp/README.md)
- [Rust](rust/README.md)
- [Kotlin](kotlin/README.md)
- [Scala](scala/README.md)

## Language Support

- ✅ C++ (Reference implementation)
- ✅ Python
- ✅ Java
- ✅ Go
- ✅ JavaScript/TypeScript
- ✅ Rust
- ✅ Kotlin
- ✅ Scala

## Performance

- **Index Size**: 97% reduction (from 350 to 10 terms per document on average)
- **Query Latency**: Efficient term-based retrieval with O(log T) query keys
- **Precision**: 100% (zero false positives)
- **Recall**: 100% (zero false negatives)

See [`benchmarks/`](benchmarks/) for reproducible scripts that generate
the synthetic POI distribution, run the in-memory and PostgreSQL GiST
comparisons, the within-Elasticsearch BKD comparison, and the Yelp
Open Dataset cross-dataset validation.

## Use Cases

- Business hours search ("find restaurants open now")
- Resource booking systems
- Shift-based operations
- Any application requiring efficient time range filtering

## License

Apache License 2.0 - see [LICENSE](LICENSE).

```
Copyright (c) 2026-present NAVER Corp.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
