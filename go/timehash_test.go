// Timehash
// Copyright (c) 2026-present NAVER Corp.
// Apache-2.0

package timehash

import (
	"testing"
)

func TestGetQueryTerms(t *testing.T) {
	th := New()
	
	// Test query term generation for 14:30
	terms := th.GetQueryTerms(1430)
	if len(terms) != 5 {
		t.Errorf("Expected 5 terms, got %d", len(terms))
	}
	expected := []string{"12", "1214", "121430", "12143030", "1214303030"}
	for i, exp := range expected {
		if terms[i] != exp {
			t.Errorf("Expected %s at index %d, got %s", exp, i, terms[i])
		}
	}
}

func TestGetQueryTermsInvalid(t *testing.T) {
	th := New()
	
	// Test with invalid input (> 10000)
	terms := th.GetQueryTerms(10001)
	if len(terms) != 0 {
		t.Errorf("Expected 0 terms for invalid input, got %d", len(terms))
	}
}

func TestGetIndexTermsSimple(t *testing.T) {
	th := New()
	
	// Test index term generation for 12:00 - 13:00
	terms, err := th.GetIndexTerms("1200", "1300")
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}
	
	found := false
	for _, term := range terms {
		if term == "1212" {
			found = true
			break
		}
	}
	if !found {
		t.Error("Should contain key 1212")
	}
}

func TestGetIndexTermsComplex(t *testing.T) {
	th := New()
	
	// Test index term generation for 11:40 - 21:00
	terms, err := th.GetIndexTerms("1140", "2100")
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}
	
	expected := []string{"08113040", "081145", "12", "16", "2020"}
	for _, exp := range expected {
		found := false
		for _, term := range terms {
			if term == exp {
				found = true
				break
			}
		}
		if !found {
			t.Errorf("Should contain %s", exp)
		}
	}
}

func TestQueryMatchesIndex(t *testing.T) {
	th := New()
	
	// Business: 11:40 - 21:00
	indexTerms, err := th.GetIndexTerms("1140", "2100")
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}
	
	// Query: 14:30 (should match)
	queryTerms := th.GetQueryTerms(1430)
	hasMatch := false
	for _, qk := range queryTerms {
		for _, ik := range indexTerms {
			if qk == ik {
				hasMatch = true
				break
			}
		}
		if hasMatch {
			break
		}
	}
	if !hasMatch {
		t.Error("Query at 14:30 should match business open 11:40-21:00")
	}
	
	// Query: 10:00 (should not match)
	queryTerms10 := th.GetQueryTerms(1000)
	hasMatch10 := false
	for _, qk := range queryTerms10 {
		for _, ik := range indexTerms {
			if qk == ik {
				hasMatch10 = true
				break
			}
		}
		if hasMatch10 {
			break
		}
	}
	if hasMatch10 {
		t.Error("Query at 10:00 should not match business open 11:40-21:00")
	}
}
