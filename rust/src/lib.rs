// Timehash
// Copyright (c) 2026-present NAVER Corp.
// Apache-2.0

/// Timehash: Hierarchical time indexing for efficient business hours search.
///
/// Timehash generates hierarchical hash keys for time ranges, enabling efficient
/// temporal filtering in search systems with minimal index overhead.

/// Default measures: [400, 100, 15, 5, 1] representing:
/// - 400 minutes (4 hours)
/// - 100 minutes (1 hour, treated as 60 minutes)
/// - 15 minutes
/// - 5 minutes
/// - 1 minute
const DEFAULT_MEASURES: &[i32] = &[400, 100, 15, 5, 1];

/// Timehash generates hierarchical hash keys for time ranges.
pub struct Timehash {
    measures: Vec<i32>,
}

impl Timehash {
    /// Create a new Timehash instance with default measures.
    pub fn new() -> Self {
        Timehash {
            measures: DEFAULT_MEASURES.to_vec(),
        }
    }

    /// Create a new Timehash instance with custom measures.
    pub fn with_measures(measures: &[i32]) -> Self {
        Timehash {
            measures: measures.to_vec(),
        }
    }

    /// Generate query terms for a given time.
    ///
    /// # Arguments
    ///
    /// * `hhmm` - Time in hhmm format (e.g., 1720 for 17:20)
    ///
    /// # Returns
    ///
    /// Vector of hierarchical hash keys for the query time
    pub fn get_query_terms(&self, hhmm: i32) -> Vec<String> {
        let mut terms = Vec::new();

        if hhmm > 10000 {
            return terms;
        }

        for &measure in &self.measures {
            let mut target = hhmm;
            let measure_val = if measure >= 100 {
                target /= 100;
                measure / 100
            } else {
                target %= 100;
                measure
            };

            let key = (target / measure_val) * measure_val;
            let term = self.two_digit_term(key);

            if terms.is_empty() {
                terms.push(term);
            } else {
                let last_term = terms.last().unwrap().clone();
                terms.push(format!("{}{}", last_term, term));
            }
        }

        terms
    }

    /// Generate index terms for a time range.
    ///
    /// # Arguments
    ///
    /// * `from_time` - Start time in hhmm format (e.g., "1140")
    /// * `to_time` - End time in hhmm format (e.g., "2100")
    ///
    /// # Returns
    ///
    /// Vector of hierarchical hash keys covering the time range
    pub fn get_index_terms(&self, from_time: &str, to_time: &str) -> Vec<String> {
        let from_int: i32 = from_time.parse().unwrap_or(0);
        let to_int: i32 = to_time.parse().unwrap_or(0);
        let mut terms = Vec::new();
        self.cover(&mut terms, 0, "", from_int, to_int);
        terms
    }

    fn two_digit_term(&self, mut key: i32) -> String {
        if key >= 100 {
            key /= 100;
        }
        format!("{}{}", key / 10, key % 10)
    }

    fn cover(&self, terms: &mut Vec<String>, measure_index: usize, parent_key: &str, from: i32, to: i32) {
        if measure_index >= self.measures.len() {
            return;
        }

        let measure = self.measures[measure_index];
        let mut from_val = from;
        let mut to_val = to;

        if measure < 100 {
            from_val %= 100;
            to_val %= 100;
            if to_val == 0 {
                to_val = 60;
            }
        }

        let start = from_val / measure;
        let end = to_val / measure;

        for i in start..=end {
            let key = measure * i;

            if from_val <= key && key + measure <= to_val {
                let term = self.two_digit_term(key);
                terms.push(format!("{}{}", parent_key, term));
            } else if key < from_val && from_val < key + measure {
                let term = self.two_digit_term(key);
                let end = std::cmp::min(key + measure, to_val);
                self.cover(terms, measure_index + 1, &format!("{}{}", parent_key, term), from_val, end);
            } else if key < to_val && to_val < key + measure {
                let term = self.two_digit_term(key);
                self.cover(terms, measure_index + 1, &format!("{}{}", parent_key, term), key, to_val);
            }
        }
    }
}

impl Default for Timehash {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_get_query_terms() {
        let th = Timehash::new();
        let terms = th.get_query_terms(1430);
        assert_eq!(terms.len(), 5);
        assert_eq!(terms[0], "12");
        assert_eq!(terms[1], "1214");
        assert_eq!(terms[2], "121430");
        assert_eq!(terms[3], "12143030");
        assert_eq!(terms[4], "1214303030");
    }

    #[test]
    fn test_get_query_terms_invalid() {
        let th = Timehash::new();
        let terms = th.get_query_terms(10001);
        assert_eq!(terms.len(), 0);
    }

    #[test]
    fn test_get_index_terms_simple() {
        let th = Timehash::new();
        let terms = th.get_index_terms("1200", "1300");
        assert!(terms.contains(&"1212".to_string()));
    }

    #[test]
    fn test_get_index_terms_complex() {
        let th = Timehash::new();
        let terms = th.get_index_terms("1140", "2100");
        assert!(terms.contains(&"08113040".to_string()));
        assert!(terms.contains(&"081145".to_string()));
        assert!(terms.contains(&"12".to_string()));
        assert!(terms.contains(&"16".to_string()));
        assert!(terms.contains(&"2020".to_string()));
    }

    #[test]
    fn test_query_matches_index() {
        let th = Timehash::new();
        let index_terms = th.get_index_terms("1140", "2100");
        
        let query_terms = th.get_query_terms(1430);
        let has_match = query_terms.iter().any(|qk| index_terms.contains(qk));
        assert!(has_match, "Query at 14:30 should match business open 11:40-21:00");
        
        let query_terms_10 = th.get_query_terms(1000);
        let has_match_10 = query_terms_10.iter().any(|qk| index_terms.contains(qk));
        assert!(!has_match_10, "Query at 10:00 should not match business open 11:40-21:00");
    }
}
