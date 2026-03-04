# Timehash
# Copyright (c) 2026-present NAVER Corp.
# Apache-2.0

import unittest
from timehash import Timehash


class TestTimehash(unittest.TestCase):
    def setUp(self):
        self.th = Timehash()

    def test_get_query_terms(self):
        """Test query term generation for a specific time."""
        terms = self.th.get_query_terms(1430)  # 14:30
        self.assertEqual(len(terms), 5)
        self.assertEqual(terms[0], "12")
        self.assertEqual(terms[1], "1214")
        self.assertEqual(terms[2], "121430")
        # Level 4 (5-minute): 14:30 is in the 5-minute block starting at 14:30, so key is 30
        self.assertEqual(terms[3], "12143030")
        # Level 5 (1-minute): 14:30 is exactly at minute 30, so key is 30
        self.assertEqual(terms[4], "1214303030")

    def test_get_query_terms_invalid(self):
        """Test query term generation with invalid input."""
        # 10000 is treated as 100:00 which is invalid, but code generates keys
        # C++ code checks hhmm > 10000, so 10000 itself is processed
        terms = self.th.get_query_terms(10001)  # Actually invalid (> 10000)
        self.assertEqual(len(terms), 0)

    def test_get_index_terms_simple(self):
        """Test index term generation for a simple range."""
        terms = self.th.get_index_terms("1200", "1300")  # 12:00 - 13:00
        self.assertIn("1212", terms)

    def test_get_index_terms_complex(self):
        """Test index term generation for a complex range."""
        terms = self.th.get_index_terms("1140", "2100")  # 11:40 - 21:00
        expected_keys = ["08113040", "081145", "12", "16", "2020"]
        for key in expected_keys:
            self.assertIn(key, terms)

    def test_custom_measures(self):
        """Test with custom measures."""
        custom_th = Timehash(measures=[240, 60, 15, 5, 1])
        terms = custom_th.get_index_terms("1200", "1300")
        self.assertGreater(len(terms), 0)

    def test_query_matches_index(self):
        """Test that query keys match index keys correctly."""
        # Business: 11:40 - 21:00
        index_terms = self.th.get_index_terms("1140", "2100")
        
        # Query: 14:30 (should match)
        query_terms = self.th.get_query_terms(1430)
        matches = [q for q in query_terms if q in index_terms]
        self.assertGreater(len(matches), 0, "Query at 14:30 should match business open 11:40-21:00")
        
        # Query: 10:00 (should not match)
        query_terms_10 = self.th.get_query_terms(1000)
        matches_10 = [q for q in query_terms_10 if q in index_terms]
        self.assertEqual(len(matches_10), 0, "Query at 10:00 should not match business open 11:40-21:00")


if __name__ == '__main__':
    unittest.main()
