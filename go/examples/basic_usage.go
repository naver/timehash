// Timehash
// Copyright (c) 2026-present NAVER Corp.
// Apache-2.0

package main

import (
	"fmt"
	"github.com/naver/timehash"
)

func main() {
	// Create Timehash instance
	th := timehash.New()

	fmt.Println("=== Timehash Basic Usage Example ===\n")

	// Example 1: Generate index terms for business operating hours
	fmt.Println("Example 1: Business operating hours (11:40 AM - 9:00 PM)")
	indexKeys, _ := th.GetIndexTerms("1140", "2100")
	fmt.Printf("Index keys: %v\n", indexKeys)
	fmt.Printf("Number of keys: %d\n", len(indexKeys))
	fmt.Printf("Compared to minute-level: 560 keys → %d keys (%.1f%% reduction)\n\n",
		len(indexKeys), (1-float64(len(indexKeys))/560)*100)

	// Example 2: Generate query terms for a specific time
	fmt.Println("Example 2: Query for businesses open at 2:30 PM")
	queryKeys := th.GetQueryTerms(1430)
	fmt.Printf("Query keys: %v\n\n", queryKeys)

	// Example 3: Check if business is open at query time
	fmt.Println("Example 3: Check if business is open at query time")
	isOpen := false
	for _, qk := range queryKeys {
		for _, ik := range indexKeys {
			if qk == ik {
				isOpen = true
				break
			}
		}
		if isOpen {
			break
		}
	}
	fmt.Printf("Business open at 14:30: %v\n", isOpen)

	// Example 4: Simple range (12:00 PM - 1:00 PM)
	fmt.Println("\nExample 4: Simple range (12:00 PM - 1:00 PM)")
	simpleKeys, _ := th.GetIndexTerms("1200", "1300")
	fmt.Printf("Index keys: %v\n", simpleKeys)
}
