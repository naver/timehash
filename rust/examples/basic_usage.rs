// Timehash
// Copyright (c) 2026-present NAVER Corp.
// Apache-2.0

use timehash::Timehash;

fn main() {
    // Create Timehash instance
    let th = Timehash::new();
    
    println!("=== Timehash Basic Usage Example ===\n");
    
    // Example 1: Generate index terms for business operating hours
    println!("Example 1: Business operating hours (11:40 AM - 9:00 PM)");
    let index_keys = th.get_index_terms("1140", "2100");
    println!("Index keys: {:?}", index_keys);
    println!("Number of keys: {}", index_keys.len());
    let reduction = (1.0 - (index_keys.len() as f64 / 560.0)) * 100.0;
    println!("Compared to minute-level: 560 keys → {} keys ({:.1}% reduction)\n",
             index_keys.len(), reduction);
    
    // Example 2: Generate query terms for a specific time
    println!("Example 2: Query for businesses open at 2:30 PM");
    let query_keys = th.get_query_terms(1430);
    println!("Query keys: {:?}\n", query_keys);
    
    // Example 3: Check if business is open at query time
    println!("Example 3: Check if business is open at query time");
    let is_open = query_keys.iter().any(|qk| index_keys.contains(qk));
    println!("Business open at 14:30: {}\n", is_open);
    
    // Example 4: Simple range (12:00 PM - 1:00 PM)
    println!("Example 4: Simple range (12:00 PM - 1:00 PM)");
    let simple_keys = th.get_index_terms("1200", "1300");
    println!("Index keys: {:?}\n", simple_keys);
    
    // Example 5: Custom measures
    println!("Example 5: Custom measures");
    let custom_th = Timehash::with_measures(&[240, 60, 15, 5, 1]);
    let custom_keys = custom_th.get_index_terms("1200", "1300");
    println!("Index keys with custom measures: {:?}", custom_keys);
}
