/*
 * Timehash
 * Copyright (c) 2026-present NAVER Corp.
 * Apache-2.0
 */

/**
 * Timehash: Hierarchical time indexing for efficient business hours search.
 * 
 * Timehash generates hierarchical hash keys for time ranges, enabling efficient
 * temporal filtering in search systems with minimal index overhead.
 */

class Timehash {
    /**
     * Default measures: [400, 100, 15, 5, 1] representing:
     * - 400 minutes (4 hours)
     * - 100 minutes (1 hour, treated as 60 minutes)
     * - 15 minutes
     * - 5 minutes
     * - 1 minute
     */
    static DEFAULT_MEASURES = [400, 100, 15, 5, 1];

    /**
     * Initialize Timehash with optional custom measures.
     * 
     * @param {number[]} measures - List of time measures in minutes. Default: [400, 100, 15, 5, 1]
     */
    constructor(measures = null) {
        this.measures = measures || [...Timehash.DEFAULT_MEASURES];
    }

    /**
     * Generate query terms for a given time.
     * 
     * @param {number} hhmm - Time in hhmm format (e.g., 1720 for 17:20)
     * @returns {string[]} List of hierarchical hash keys for the query time
     */
    getQueryTerms(hhmm) {
        const terms = [];

        if (hhmm > 10000) {
            return terms;
        }

        for (const measure of this.measures) {
            let target = hhmm;
            let measureVal;

            if (measure >= 100) {
                target = Math.floor(target / 100);
                measureVal = Math.floor(measure / 100);
            } else {
                target = target % 100;
                measureVal = measure;
            }

            const key = Math.floor(target / measureVal) * measureVal;
            const term = this._twoDigitTerm(key);

            if (terms.length === 0) {
                terms.push(term);
            } else {
                terms.push(terms[terms.length - 1] + term);
            }
        }

        return terms;
    }

    /**
     * Generate index terms for a time range.
     * 
     * @param {string} fromTime - Start time in hhmm format (e.g., "1140")
     * @param {string} toTime - End time in hhmm format (e.g., "2100")
     * @returns {string[]} List of hierarchical hash keys covering the time range
     */
    getIndexTerms(fromTime, toTime) {
        const terms = [];
        const fromInt = parseInt(fromTime, 10);
        const toInt = parseInt(toTime, 10);
        this._cover(terms, 0, "", fromInt, toInt);
        return terms;
    }

    /**
     * Convert a key to two-digit string representation.
     * 
     * @param {number} key - Key value
     * @returns {string} Two-digit string representation
     * @private
     */
    _twoDigitTerm(key) {
        let k = key;
        if (k >= 100) {
            k = Math.floor(k / 100);
        }
        return `${Math.floor(k / 10)}${k % 10}`;
    }

    /**
     * Recursively generate keys for a time range.
     * 
     * @param {string[]} terms - List to append generated keys
     * @param {number} measureIndex - Current level in the hierarchy
     * @param {string} parentKey - Key from parent level
     * @param {number} fromTime - Start time (integer in hhmm format)
     * @param {number} toTime - End time (integer in hhmm format)
     * @private
     */
    _cover(terms, measureIndex, parentKey, fromTime, toTime) {
        if (measureIndex >= this.measures.length) {
            return;
        }

        const measure = this.measures[measureIndex];
        let fromVal = fromTime;
        let toVal = toTime;

        if (measure < 100) {
            fromVal = fromVal % 100;
            toVal = toVal % 100;
            if (toVal === 0) {
                toVal = 60;
            }
        }

        for (let i = Math.floor(fromVal / measure); i <= Math.floor(toVal / measure); i++) {
            const key = measure * i;

            if (fromVal <= key && key + measure <= toVal) {
                terms.push(parentKey + this._twoDigitTerm(key));
            } else if (key < fromVal && fromVal < key + measure) {
                const end = Math.min(key + measure, toVal);
                this._cover(terms, measureIndex + 1,
                    parentKey + this._twoDigitTerm(key),
                    fromVal, end);
            } else if (key < toVal && toVal < key + measure) {
                this._cover(terms, measureIndex + 1,
                    parentKey + this._twoDigitTerm(key),
                    key, toVal);
            }
        }
    }
}

// Export for Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Timehash;
}

// Export for ES6 modules
if (typeof window !== 'undefined') {
    window.Timehash = Timehash;
}
