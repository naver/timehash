/*
 * Timehash
 * Copyright (c) 2026-present NAVER Corp.
 * Apache-2.0
 */

package com.naver.timehash

/**
 * Timehash: Hierarchical time indexing for efficient business hours search.
 *
 * Timehash generates hierarchical hash keys for time ranges, enabling efficient
 * temporal filtering in search systems with minimal index overhead.
 */
class Timehash(
    private val measures: List<Int> = DEFAULT_MEASURES
) {
    companion object {
        /**
         * Default measures: [400, 100, 15, 5, 1] representing:
         * - 400 minutes (4 hours)
         * - 100 minutes (1 hour, treated as 60 minutes)
         * - 15 minutes
         * - 5 minutes
         * - 1 minute
         */
        private val DEFAULT_MEASURES = listOf(400, 100, 15, 5, 1)
    }

    /**
     * Generate query terms for a given time.
     *
     * @param hhmm Time in hhmm format (e.g., 1720 for 17:20)
     * @return List of hierarchical hash keys for the query time
     */
    fun getQueryTerms(hhmm: Int): List<String> {
        val terms = mutableListOf<String>()

        if (hhmm > 10000) {
            return terms
        }

        for (measure in measures) {
            var target = hhmm
            val measureVal = if (measure >= 100) {
                target /= 100
                measure / 100
            } else {
                target %= 100
                measure
            }

            val key = (target / measureVal) * measureVal
            val term = twoDigitTerm(key)

            if (terms.isEmpty()) {
                terms.add(term)
            } else {
                terms.add(terms.last() + term)
            }
        }

        return terms
    }

    /**
     * Generate index terms for a time range.
     *
     * @param fromTime Start time in hhmm format (e.g., "1140")
     * @param toTime End time in hhmm format (e.g., "2100")
     * @return List of hierarchical hash keys covering the time range
     */
    fun getIndexTerms(fromTime: String, toTime: String): List<String> {
        val fromInt = fromTime.toIntOrNull() ?: 0
        val toInt = toTime.toIntOrNull() ?: 0
        val terms = mutableListOf<String>()
        cover(terms, 0, "", fromInt, toInt)
        return terms
    }

    private fun twoDigitTerm(key: Int): String {
        var k = key
        if (k >= 100) {
            k /= 100
        }
        return "${k / 10}${k % 10}"
    }

    private fun cover(
        terms: MutableList<String>,
        measureIndex: Int,
        parentKey: String,
        from: Int,
        to: Int
    ) {
        if (measureIndex >= measures.size) {
            return
        }

        val measure = measures[measureIndex]
        var fromVal = from
        var toVal = to

        if (measure < 100) {
            fromVal %= 100
            toVal %= 100
            if (toVal == 0) {
                toVal = 60
            }
        }

        val start = fromVal / measure
        val end = toVal / measure

        for (i in start..end) {
            val key = measure * i

            when {
                fromVal <= key && key + measure <= toVal -> {
                    val term = twoDigitTerm(key)
                    terms.add(parentKey + term)
                }
                key < fromVal && fromVal < key + measure -> {
                    val term = twoDigitTerm(key)
                    val end = minOf(key + measure, toVal)
                    cover(terms, measureIndex + 1, parentKey + term, fromVal, end)
                }
                key < toVal && toVal < key + measure -> {
                    val term = twoDigitTerm(key)
                    cover(terms, measureIndex + 1, parentKey + term, key, toVal)
                }
            }
        }
    }
}
