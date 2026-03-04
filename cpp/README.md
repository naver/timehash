# Timehash C++

C++ reference implementation of Timehash for hierarchical time indexing.

## Installation

Simply include the header file:

```cpp
#include "timehash.hpp"
```

## Requirements

- C++11 or later
- Standard library support for `<vector>`, `<string>`, `<cstdio>`

## Usage

```cpp
#include "timehash.hpp"
#include <iostream>
#include <vector>

int main() {
    // Create Timehash instance with default measures
    Timehash th;
    
    // Generate query terms for a specific time
    std::vector<std::string> queryTerms = th.getQueryTerms(1430); // 14:30
    // Returns: {"12", "1214", "121430", "12143030", "1214303030"}
    
    // Generate index terms for a time range
    std::vector<std::string> indexTerms = th.getIndexTerms("1140", "2100"); // 11:40 - 21:00
    // Returns: {"08113040", "081145", "12", "16", "2020"}
    
    // Custom measures
    std::vector<int> customMeasures = {240, 60, 15, 5, 1};
    th.setMeasures(customMeasures);
    
    return 0;
}
```

## Example

```cpp
#include "timehash.hpp"
#include <iostream>
#include <vector>
#include <algorithm>

int main() {
    Timehash th;
    
    // Business operating hours: 11:40 AM - 9:00 PM
    std::vector<std::string> keys = th.getIndexTerms("1140", "2100");
    std::cout << "Index keys: ";
    for (const auto& key : keys) {
        std::cout << key << " ";
    }
    std::cout << std::endl;
    // Output: 08113040 081145 12 16 2020
    
    // Query: Is business open at 2:30 PM?
    std::vector<std::string> queryKeys = th.getQueryTerms(1430);
    std::cout << "Query keys: ";
    for (const auto& key : queryKeys) {
        std::cout << key << " ";
    }
    std::cout << std::endl;
    // Output: 12 1214 121430 12143030 1214303030
    
    // Check if any query key matches any index key
    bool isOpen = false;
    for (const auto& qk : queryKeys) {
        if (std::find(keys.begin(), keys.end(), qk) != keys.end()) {
            isOpen = true;
            break;
        }
    }
    std::cout << "Business is open: " << (isOpen ? "true" : "false") << std::endl;
    
    return 0;
}
```

## Running Examples

```bash
# Compile the example
cd cpp/examples
g++ -std=c++11 -I.. -o basic_usage basic_usage.cpp

# Run the example
./basic_usage
```

## Running Tests

```bash
# Compile the test
cd cpp
g++ -std=c++11 -I. -o test_timehash test_timehash.cpp

# Run the test
./test_timehash
```

## API Reference

### `Timehash()`
Creates a Timehash instance with default measures `{400, 100, 15, 5, 1}` (4h, 1h, 15m, 5m, 1m).

### `void setMeasures(std::vector<int> measures)`
Sets custom precision measures for time decomposition.

### `std::vector<std::string> getQueryTerms(int hhmm)`
Generates query terms for a specific time.
- **Parameters**: `hhmm` - Time in hhmm format (e.g., 1430 for 14:30)
- **Returns**: Vector of hierarchical hash keys

### `std::vector<std::string> getIndexTerms(std::string from, std::string to)`
Generates index terms for a time range.
- **Parameters**: 
  - `from` - Start time in hhmm format string (e.g., "1140")
  - `to` - End time in hhmm format string (e.g., "2100")
- **Returns**: Vector of hierarchical hash keys covering the time range
