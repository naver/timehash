/*
 * Timehash
 * Copyright (c) 2026-present NAVER Corp.
 * Apache-2.0
 */

package com.naver.timehash.example

import com.naver.timehash.Timehash

fun main() {
    // Create Timehash instance
    val th = Timehash()
    
    println("=== Timehash Basic Usage Example ===\n")
    
    // Example 1: Generate index terms for business operating hours
    println("Example 1: Business operating hours (11:40 AM - 9:00 PM)")
    val indexKeys = th.getIndexTerms("1140", "2100")
    println("Index keys: $indexKeys")
    println("Number of keys: ${indexKeys.size}")
    val reduction = (1.0 - (indexKeys.size / 560.0)) * 100.0
    println("Compared to minute-level: 560 keys → ${indexKeys.size} keys (${String.format("%.1f", reduction)}% reduction)\n")
    
    // Example 2: Generate query terms for a specific time
    println("Example 2: Query for businesses open at 2:30 PM")
    val queryKeys = th.getQueryTerms(1430)
    println("Query keys: $queryKeys\n")
    
    // Example 3: Check if business is open at query time
    println("Example 3: Check if business is open at query time")
    val isOpen = queryKeys.any { indexKeys.contains(it) }
    println("Business open at 14:30: $isOpen")
    
    // Example 4: Simple range (12:00 PM - 1:00 PM)
    println("\nExample 4: Simple range (12:00 PM - 1:00 PM)")
    val simpleKeys = th.getIndexTerms("1200", "1300")
    println("Index keys: $simpleKeys")
    
    // Example 5: Custom measures
    println("\nExample 5: Custom measures")
    val customTh = Timehash(listOf(240, 60, 15, 5, 1))  // 4h, 1h, 15m, 5m, 1m
    val customKeys = customTh.getIndexTerms("1200", "1300")
    println("Index keys with custom measures: $customKeys")
}
