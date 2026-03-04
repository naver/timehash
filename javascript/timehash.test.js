/*
 * Timehash
 * Copyright (c) 2026-present NAVER Corp.
 * Apache-2.0
 */

const Timehash = require('./timehash');

describe('Timehash', () => {
    let th;

    beforeEach(() => {
        th = new Timehash();
    });

    test('getQueryTerms generates correct keys for 14:30', () => {
        const terms = th.getQueryTerms(1430);
        expect(terms).toHaveLength(5);
        expect(terms[0]).toBe('12');
        expect(terms[1]).toBe('1214');
        expect(terms[2]).toBe('121430');
        // Level 4 (5-minute): 14:30 is in the 5-minute block starting at 14:30, so key is 30
        expect(terms[3]).toBe('12143030');
        // Level 5 (1-minute): 14:30 is exactly at minute 30, so key is 30
        expect(terms[4]).toBe('1214303030');
    });

    test('getQueryTerms returns empty array for invalid input', () => {
        const terms = th.getQueryTerms(10001); // > 10000
        expect(terms).toHaveLength(0);
    });

    test('getIndexTerms generates keys for simple range', () => {
        const terms = th.getIndexTerms('1200', '1300');
        expect(terms).toContain('1212');
    });

    test('getIndexTerms generates keys for complex range', () => {
        const terms = th.getIndexTerms('1140', '2100');
        expect(terms).toContain('08113040');
        expect(terms).toContain('081145');
        expect(terms).toContain('12');
        expect(terms).toContain('16');
        expect(terms).toContain('2020');
    });

    test('query keys match index keys correctly', () => {
        // Business: 11:40 - 21:00
        const indexTerms = th.getIndexTerms('1140', '2100');
        
        // Query: 14:30 (should match)
        const queryTerms = th.getQueryTerms(1430);
        const hasMatch = queryTerms.some(qk => indexTerms.includes(qk));
        expect(hasMatch).toBe(true);
        
        // Query: 10:00 (should not match)
        const queryTerms10 = th.getQueryTerms(1000);
        const hasMatch10 = queryTerms10.some(qk => indexTerms.includes(qk));
        expect(hasMatch10).toBe(false);
    });
});
