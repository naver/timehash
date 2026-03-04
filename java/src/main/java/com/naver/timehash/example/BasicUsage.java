/*
 * Timehash
 * Copyright (c) 2026-present NAVER Corp.
 * Apache-2.0
 */

package com.naver.timehash.example;

import com.naver.timehash.Timehash;
import java.util.List;

public class BasicUsage {
    public static void main(String[] args) {
        // Create Timehash instance
        Timehash th = new Timehash();
        
        System.out.println("=== Timehash Basic Usage Example ===\n");
        
        // Example 1: Generate index terms for business operating hours
        System.out.println("Example 1: Business operating hours (11:40 AM - 9:00 PM)");
        List<String> indexKeys = th.getIndexTerms("1140", "2100");
        System.out.println("Index keys: " + indexKeys);
        System.out.println("Number of keys: " + indexKeys.size());
        System.out.printf("Compared to minute-level: 560 keys → %d keys (%.1f%% reduction)\n\n",
                indexKeys.size(), (1 - indexKeys.size() / 560.0) * 100);
        
        // Example 2: Generate query terms for a specific time
        System.out.println("Example 2: Query for businesses open at 2:30 PM");
        List<String> queryKeys = th.getQueryTerms(1430);
        System.out.println("Query keys: " + queryKeys + "\n");
        
        // Example 3: Check if business is open at query time
        System.out.println("Example 3: Check if business is open at query time");
        boolean isOpen = queryKeys.stream().anyMatch(indexKeys::contains);
        System.out.println("Business open at 14:30: " + isOpen);
        
        // Example 4: Simple range (12:00 PM - 1:00 PM)
        System.out.println("\nExample 4: Simple range (12:00 PM - 1:00 PM)");
        List<String> simpleKeys = th.getIndexTerms("1200", "1300");
        System.out.println("Index keys: " + simpleKeys);
    }
}
