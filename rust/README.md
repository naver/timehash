# Timehash Rust

Rust implementation of Timehash for hierarchical time indexing.

## Installation

Add this to your `Cargo.toml`:

```toml
[dependencies]
timehash = { path = "../rust" }
```

Or from crates.io (when published):

```toml
[dependencies]
timehash = "0.1.0"
```

## Usage

```rust
use timehash::Timehash;

// Create Timehash instance with default measures
let th = Timehash::new();

// Generate query terms for a specific time
let query_terms = th.get_query_terms(1430); // 14:30
// Returns: vec!["12", "1214", "121430", "12143030", "1214303030"]

// Generate index terms for a time range
let index_terms = th.get_index_terms("1140", "2100"); // 11:40 - 21:00
// Returns: vec!["08113040", "081145", "12", "16", "2020"]

// Custom measures
let custom_th = Timehash::with_measures(&[240, 60, 15, 5, 1]);
```

## Example

```rust
use timehash::Timehash;

fn main() {
    let th = Timehash::new();
    
    // Business operating hours: 11:40 AM - 9:00 PM
    let keys = th.get_index_terms("1140", "2100");
    println!("Index keys: {:?}", keys);
    // Output: ["08113040", "081145", "12", "16", "2020"]
    
    // Query: Is business open at 2:30 PM?
    let query_keys = th.get_query_terms(1430);
    println!("Query keys: {:?}", query_keys);
    // Output: ["12", "1214", "121430", "12143030", "1214303030"]
    
    // Check if any query key matches any index key
    let is_open = query_keys.iter().any(|qk| keys.contains(qk));
    println!("Business is open: {}", is_open);
}
```

## Running Examples

```bash
cd rust
cargo run --example basic_usage
```

## Running Tests

```bash
cd rust
cargo test
```

## API Reference

### `Timehash::new()`
Creates a Timehash instance with default measures `[400, 100, 15, 5, 1]` (4h, 1h, 15m, 5m, 1m).

### `Timehash::with_measures(measures: &[i32])`
Creates a Timehash instance with custom precision measures.

### `get_query_terms(&self, hhmm: i32) -> Vec<String>`
Generates query terms for a specific time.
- **Parameters**: `hhmm` - Time in hhmm format (e.g., 1430 for 14:30)
- **Returns**: Vector of hierarchical hash keys

### `get_index_terms(&self, from_time: &str, to_time: &str) -> Vec<String>`
Generates index terms for a time range.
- **Parameters**: 
  - `from_time` - Start time in hhmm format string (e.g., "1140")
  - `to_time` - End time in hhmm format string (e.g., "2100")
- **Returns**: Vector of hierarchical hash keys covering the time range
