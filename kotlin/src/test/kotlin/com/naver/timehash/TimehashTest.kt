/*
 * Timehash
 * Copyright (c) 2026-present NAVER Corp.
 * Apache-2.0
 */

package com.naver.timehash

import org.junit.Test
import org.junit.Assert.*

class TimehashTest {
    private val th = Timehash()

    @Test
    fun testGetQueryTerms() {
        // Test query term generation for 14:30
        val terms = th.getQueryTerms(1430)
        assertEquals(5, terms.size)
        assertEquals("12", terms[0])
        assertEquals("1214", terms[1])
        assertEquals("121430", terms[2])
        // Level 4 (5-minute): 14:30 is in the 5-minute block starting at 14:30, so key is 30
        assertEquals("12143030", terms[3])
        // Level 5 (1-minute): 14:30 is exactly at minute 30, so key is 30
        assertEquals("1214303030", terms[4])
    }

    @Test
    fun testGetQueryTermsInvalid() {
        // Test with invalid input (> 10000)
        val terms = th.getQueryTerms(10001)
        assertEquals(0, terms.size)
    }

    @Test
    fun testGetIndexTermsSimple() {
        // Test index term generation for 12:00 - 13:00
        val terms = th.getIndexTerms("1200", "1300")
        assertTrue("Should contain key 1212", terms.contains("1212"))
    }

    @Test
    fun testGetIndexTermsComplex() {
        // Test index term generation for 11:40 - 21:00
        val terms = th.getIndexTerms("1140", "2100")
        assertTrue("Should contain 08113040", terms.contains("08113040"))
        assertTrue("Should contain 081145", terms.contains("081145"))
        assertTrue("Should contain 12", terms.contains("12"))
        assertTrue("Should contain 16", terms.contains("16"))
        assertTrue("Should contain 2020", terms.contains("2020"))
    }

    @Test
    fun testQueryMatchesIndex() {
        // Business: 11:40 - 21:00
        val indexTerms = th.getIndexTerms("1140", "2100")
        
        // Query: 14:30 (should match)
        val queryTerms = th.getQueryTerms(1430)
        val hasMatch = queryTerms.any { indexTerms.contains(it) }
        assertTrue("Query at 14:30 should match business open 11:40-21:00", hasMatch)
        
        // Query: 10:00 (should not match)
        val queryTerms10 = th.getQueryTerms(1000)
        val hasMatch10 = queryTerms10.any { indexTerms.contains(it) }
        assertFalse("Query at 10:00 should not match business open 11:40-21:00", hasMatch10)
    }
}
