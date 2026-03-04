/*
 * Timehash
 * Copyright (c) 2026-present NAVER Corp.
 * Apache-2.0
 */

#include <iostream>
#include <vector>
#include <string>
#include <cassert>
#include <algorithm>
#include "timehash.hpp"

// Helper function to check if vector contains a value
bool contains(const std::vector<std::string>& vec, const std::string& value) {
    return std::find(vec.begin(), vec.end(), value) != vec.end();
}

// Helper function to check if any query term matches index terms
bool hasMatch(const std::vector<std::string>& queryTerms, const std::vector<std::string>& indexTerms) {
    for (const auto& qk : queryTerms) {
        if (contains(indexTerms, qk)) {
            return true;
        }
    }
    return false;
}

void testGetQueryTerms() {
    std::cout << "Testing getQueryTerms for 14:30...\n";
    Timehash th;
    std::vector<std::string> terms = th.getQueryTerms(1430);
    
    assert(terms.size() == 5);
    assert(terms[0] == "12");
    assert(terms[1] == "1214");
    assert(terms[2] == "121430");
    assert(terms[3] == "12143030");
    assert(terms[4] == "1214303030");
    
    std::cout << "  ✓ testGetQueryTerms passed\n";
}

void testGetQueryTermsInvalid() {
    std::cout << "Testing getQueryTerms with invalid input...\n";
    Timehash th;
    std::vector<std::string> terms = th.getQueryTerms(10001);
    
    assert(terms.size() == 0);
    
    std::cout << "  ✓ testGetQueryTermsInvalid passed\n";
}

void testGetIndexTermsSimple() {
    std::cout << "Testing getIndexTerms for simple range (12:00-13:00)...\n";
    Timehash th;
    std::vector<std::string> terms = th.getIndexTerms("1200", "1300");
    
    assert(contains(terms, "1212"));
    
    std::cout << "  ✓ testGetIndexTermsSimple passed\n";
}

void testGetIndexTermsComplex() {
    std::cout << "Testing getIndexTerms for complex range (11:40-21:00)...\n";
    Timehash th;
    std::vector<std::string> terms = th.getIndexTerms("1140", "2100");
    
    assert(contains(terms, "08113040"));
    assert(contains(terms, "081145"));
    assert(contains(terms, "12"));
    assert(contains(terms, "16"));
    assert(contains(terms, "2020"));
    
    std::cout << "  ✓ testGetIndexTermsComplex passed\n";
}

void testQueryMatchesIndex() {
    std::cout << "Testing query matches index...\n";
    Timehash th;
    
    // Business: 11:40 - 21:00
    std::vector<std::string> indexTerms = th.getIndexTerms("1140", "2100");
    
    // Query: 14:30 (should match)
    std::vector<std::string> queryTerms = th.getQueryTerms(1430);
    assert(hasMatch(queryTerms, indexTerms));
    
    // Query: 10:00 (should not match)
    std::vector<std::string> queryTerms10 = th.getQueryTerms(1000);
    assert(!hasMatch(queryTerms10, indexTerms));
    
    std::cout << "  ✓ testQueryMatchesIndex passed\n";
}

int main() {
    std::cout << "Running Timehash C++ tests...\n\n";
    
    try {
        testGetQueryTerms();
        testGetQueryTermsInvalid();
        testGetIndexTermsSimple();
        testGetIndexTermsComplex();
        testQueryMatchesIndex();
        
        std::cout << "\nAll tests passed! ✓\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "Test failed with exception: " << e.what() << "\n";
        return 1;
    } catch (...) {
        std::cerr << "Test failed with unknown exception\n";
        return 1;
    }
}
