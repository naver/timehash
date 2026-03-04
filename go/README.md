# Timehash Go

Go implementation of Timehash for hierarchical time indexing.

## Installation

```bash
go get github.com/naver/timehash
```

## Usage

```go
import "github.com/naver/timehash"

// Create Timehash instance with default measures
th := timehash.New()

// Generate query terms for a specific time
queryTerms := th.GetQueryTerms(1430) // 14:30
// Returns: ["12", "1214", "121430", "12143000", "1214300000"]

// Generate index terms for a time range
indexTerms, err := th.GetIndexTerms("1140", "2100") // 11:40 - 21:00
// Returns: ["08113040", "081145", "12", "16", "2020"], nil

// Custom measures
customMeasures := []int{240, 60, 15, 5, 1}
customTh := timehash.NewWithMeasures(customMeasures)
```

## Example

```go
package main

import (
	"fmt"
	"github.com/naver/timehash"
)

func main() {
	th := timehash.New()

	// Business operating hours: 11:40 AM - 9:00 PM
	keys, _ := th.GetIndexTerms("1140", "2100")
	fmt.Printf("Index keys: %v\n", keys)
	// Output: [08113040 081145 12 16 2020]

	// Query: Is business open at 2:30 PM?
	queryKeys := th.GetQueryTerms(1430)
	fmt.Printf("Query keys: %v\n", queryKeys)
	// Output: [12 1214 121430 12143000 1214300000]

	// Check if any query key matches any index key
	isOpen := false
	for _, qk := range queryKeys {
		for _, ik := range keys {
			if qk == ik {
				isOpen = true
				break
			}
		}
		if isOpen {
			break
		}
	}
	fmt.Printf("Business is open: %v\n", isOpen)
}
```
