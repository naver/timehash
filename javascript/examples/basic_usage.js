/**
 * Basic usage example for Timehash.
 */

/*
 * Timehash
 * Copyright (c) 2026-present NAVER Corp.
 * Apache-2.0
 */

const Timehash = require('../timehash');

function main() {
    // Create Timehash instance
    const th = new Timehash();
    
    console.log('=== Timehash Basic Usage Example ===\n');
    
    // Example 1: Generate index terms for business operating hours
    console.log('Example 1: Business operating hours (11:40 AM - 9:00 PM)');
    const indexKeys = th.getIndexTerms('1140', '2100');
    console.log(`Index keys: [${indexKeys.join(', ')}]`);
    console.log(`Number of keys: ${indexKeys.length}`);
    console.log(`Compared to minute-level: 560 keys → ${indexKeys.length} keys ` +
                `(${((1 - indexKeys.length/560)*100).toFixed(1)}% reduction)\n`);
    
    // Example 2: Generate query terms for a specific time
    console.log('Example 2: Query for businesses open at 2:30 PM');
    const queryKeys = th.getQueryTerms(1430);
    console.log(`Query keys: [${queryKeys.join(', ')}]\n`);
    
    // Example 3: Check if business is open at query time
    console.log('Example 3: Check if business is open at query time');
    const isOpen = queryKeys.some(qk => indexKeys.includes(qk));
    console.log(`Business open at 14:30: ${isOpen}`);
    
    // Example 4: Simple range (12:00 PM - 1:00 PM)
    console.log('\nExample 4: Simple range (12:00 PM - 1:00 PM)');
    const simpleKeys = th.getIndexTerms('1200', '1300');
    console.log(`Index keys: [${simpleKeys.join(', ')}]`);
}

if (require.main === module) {
    main();
}
