/*
 * Timehash
 * Copyright (c) 2026-present NAVER Corp.
 * Apache-2.0
 */

#include <iostream>
#include <vector>
#include <string>
#include <algorithm>
#include "../timehash.hpp"

// Helper function to check if vector contains a value
bool contains(const std::vector<std::string>& vec, const std::string& value) {
    return std::find(vec.begin(), vec.end(), value) != vec.end();
}

int main() {
    // Create Timehash instance
    Timehash th;
    
    std::cout << "=== Timehash Basic Usage Example ===\n\n";
    
    // Example 1: Generate index terms for business operating hours
    std::cout << "Example 1: Business operating hours (11:40 AM - 9:00 PM)\n";
    std::vector<std::string> indexKeys = th.getIndexTerms("1140", "2100");
    std::cout << "Index keys: ";
    for (size_t i = 0; i < indexKeys.size(); i++) {
        std::cout << indexKeys[i];
        if (i < indexKeys.size() - 1) std::cout << " ";
    }
    std::cout << "\n";
    std::cout << "Number of keys: " << indexKeys.size() << "\n";
    double reduction = (1.0 - static_cast<double>(indexKeys.size()) / 560.0) * 100.0;
    std::cout << "Compared to minute-level: 560 keys → " << indexKeys.size() 
              << " keys (" << reduction << "% reduction)\n\n";
    
    // Example 2: Generate query terms for a specific time
    std::cout << "Example 2: Query for businesses open at 2:30 PM\n";
    std::vector<std::string> queryKeys = th.getQueryTerms(1430);
    std::cout << "Query keys: ";
    for (size_t i = 0; i < queryKeys.size(); i++) {
        std::cout << queryKeys[i];
        if (i < queryKeys.size() - 1) std::cout << " ";
    }
    std::cout << "\n\n";
    
    // Example 3: Check if business is open at query time
    std::cout << "Example 3: Check if business is open at query time\n";
    bool isOpen = false;
    for (const auto& qk : queryKeys) {
        if (contains(indexKeys, qk)) {
            isOpen = true;
            break;
        }
    }
    std::cout << "Business open at 14:30: " << (isOpen ? "true" : "false") << "\n";
    
    // Example 4: Simple range (12:00 PM - 1:00 PM)
    std::cout << "\nExample 4: Simple range (12:00 PM - 1:00 PM)\n";
    std::vector<std::string> simpleKeys = th.getIndexTerms("1200", "1300");
    std::cout << "Index keys: ";
    for (size_t i = 0; i < simpleKeys.size(); i++) {
        std::cout << simpleKeys[i];
        if (i < simpleKeys.size() - 1) std::cout << " ";
    }
    std::cout << "\n";
    
    // Example 5: Custom measures
    std::cout << "\nExample 5: Custom measures\n";
    std::vector<int> customMeasures = {240, 60, 15, 5, 1};  // 4h, 1h, 15m, 5m, 1m
    th.setMeasures(customMeasures);
    std::vector<std::string> customKeys = th.getIndexTerms("1200", "1300");
    std::cout << "Index keys with custom measures: ";
    for (size_t i = 0; i < customKeys.size(); i++) {
        std::cout << customKeys[i];
        if (i < customKeys.size() - 1) std::cout << " ";
    }
    std::cout << "\n";
    
    return 0;
}
