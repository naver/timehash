/*
 * Timehash
 * Copyright (c) 2026-present NAVER Corp.
 * Apache-2.0
 */

package com.naver.timehash;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * Timehash: Hierarchical time indexing for efficient business hours search.
 * 
 * Timehash generates hierarchical hash keys for time ranges, enabling efficient
 * temporal filtering in search systems with minimal index overhead.
 */
public class Timehash {
    private List<Integer> measures;
    
    /**
     * Default measures: [400, 100, 15, 5, 1] representing:
     * - 400 minutes (4 hours)
     * - 100 minutes (1 hour, treated as 60 minutes)
     * - 15 minutes
     * - 5 minutes
     * - 1 minute
     */
    private static final List<Integer> DEFAULT_MEASURES = 
        Arrays.asList(400, 100, 15, 5, 1);
    
    /**
     * Initialize Timehash with default measures.
     */
    public Timehash() {
        this.measures = new ArrayList<>(DEFAULT_MEASURES);
    }
    
    /**
     * Initialize Timehash with custom measures.
     * 
     * @param measures List of time measures in minutes
     */
    public Timehash(List<Integer> measures) {
        this.measures = new ArrayList<>(measures);
    }
    
    /**
     * Generate query terms for a given time.
     * 
     * @param hhmm Time in hhmm format (e.g., 1720 for 17:20)
     * @return List of hierarchical hash keys for the query time
     */
    public List<String> getQueryTerms(int hhmm) {
        List<String> terms = new ArrayList<>();
        
        if (hhmm > 10000) {
            return terms;
        }
        
        for (int measure : measures) {
            int target = hhmm;
            int measureVal;
            
            if (measure >= 100) {
                target /= 100;
                measureVal = measure / 100;
            } else {
                target %= 100;
                measureVal = measure;
            }
            
            int key = (target / measureVal) * measureVal;
            String term = twoDigitTerm(key);
            
            if (terms.isEmpty()) {
                terms.add(term);
            } else {
                terms.add(terms.get(terms.size() - 1) + term);
            }
        }
        
        return terms;
    }
    
    /**
     * Generate index terms for a time range.
     * 
     * @param fromTime Start time in hhmm format (e.g., "1140")
     * @param toTime End time in hhmm format (e.g., "2100")
     * @return List of hierarchical hash keys covering the time range
     */
    public List<String> getIndexTerms(String fromTime, String toTime) {
        List<String> terms = new ArrayList<>();
        int fromInt = Integer.parseInt(fromTime);
        int toInt = Integer.parseInt(toTime);
        cover(terms, 0, "", fromInt, toInt);
        return terms;
    }
    
    /**
     * Convert a key to two-digit string representation.
     * 
     * @param key Key value
     * @return Two-digit string representation
     */
    private String twoDigitTerm(int key) {
        if (key >= 100) {
            key /= 100;
        }
        return String.format("%d%d", key / 10, key % 10);
    }
    
    /**
     * Recursively generate keys for a time range.
     * 
     * @param terms List to append generated keys
     * @param measureIndex Current level in the hierarchy
     * @param parentKey Key from parent level
     * @param fromTime Start time (integer in hhmm format)
     * @param toTime End time (integer in hhmm format)
     */
    private void cover(List<String> terms, int measureIndex, String parentKey,
                      int fromTime, int toTime) {
        if (measureIndex >= measures.size()) {
            return;
        }
        
        int measure = measures.get(measureIndex);
        int fromVal = fromTime;
        int toVal = toTime;
        
        if (measure < 100) {
            fromVal %= 100;
            toVal %= 100;
            if (toVal == 0) {
                toVal = 60;
            }
        }
        
        for (int i = fromVal / measure; i <= (toVal / measure); i++) {
            int key = measure * i;
            
            if (fromVal <= key && key + measure <= toVal) {
                terms.add(parentKey + twoDigitTerm(key));
            } else if (key < fromVal && fromVal < key + measure) {
                int end = Math.min(key + measure, toVal);
                cover(terms, measureIndex + 1,
                     parentKey + twoDigitTerm(key),
                     fromVal, end);
            } else if (key < toVal && toVal < key + measure) {
                cover(terms, measureIndex + 1,
                     parentKey + twoDigitTerm(key),
                     key, toVal);
            }
        }
    }
}
