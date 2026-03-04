// Timehash
// Copyright (c) 2026-present NAVER Corp.
// Apache-2.0

package timehash

import (
	"fmt"
	"strconv"
)

// Default measures: [400, 100, 15, 5, 1] representing:
// - 400 minutes (4 hours)
// - 100 minutes (1 hour, treated as 60 minutes)
// - 15 minutes
// - 5 minutes
// - 1 minute
var defaultMeasures = []int{400, 100, 15, 5, 1}

// Timehash generates hierarchical hash keys for time ranges.
type Timehash struct {
	measures []int
}

// New creates a new Timehash instance with default measures.
func New() *Timehash {
	measures := make([]int, len(defaultMeasures))
	copy(measures, defaultMeasures)
	return &Timehash{measures: measures}
}

// NewWithMeasures creates a new Timehash instance with custom measures.
func NewWithMeasures(measures []int) *Timehash {
	m := make([]int, len(measures))
	copy(m, measures)
	return &Timehash{measures: m}
}

// GetQueryTerms generates query terms for a given time.
// hhmm: Time in hhmm format (e.g., 1720 for 17:20)
// Returns: List of hierarchical hash keys for the query time
func (th *Timehash) GetQueryTerms(hhmm int) []string {
	var terms []string

	if hhmm > 10000 {
		return terms
	}

	for _, measure := range th.measures {
		target := hhmm
		var measureVal int

		if measure >= 100 {
			target /= 100
			measureVal = measure / 100
		} else {
			target %= 100
			measureVal = measure
		}

		key := (target / measureVal) * measureVal
		term := th.twoDigitTerm(key)

		if len(terms) == 0 {
			terms = append(terms, term)
		} else {
			terms = append(terms, terms[len(terms)-1]+term)
		}
	}

	return terms
}

// GetIndexTerms generates index terms for a time range.
// fromTime: Start time in hhmm format (e.g., "1140")
// toTime: End time in hhmm format (e.g., "2100")
// Returns: List of hierarchical hash keys covering the time range
func (th *Timehash) GetIndexTerms(fromTime, toTime string) ([]string, error) {
	fromInt, err := strconv.Atoi(fromTime)
	if err != nil {
		return nil, fmt.Errorf("invalid fromTime: %w", err)
	}

	toInt, err := strconv.Atoi(toTime)
	if err != nil {
		return nil, fmt.Errorf("invalid toTime: %w", err)
	}

	var terms []string
	th.cover(&terms, 0, "", fromInt, toInt)
	return terms, nil
}

// twoDigitTerm converts a key to two-digit string representation.
func (th *Timehash) twoDigitTerm(key int) string {
	if key >= 100 {
		key /= 100
	}
	return fmt.Sprintf("%d%d", key/10, key%10)
}

// cover recursively generates keys for a time range.
func (th *Timehash) cover(terms *[]string, measureIndex int, parentKey string,
	fromTime, toTime int) {
	if measureIndex >= len(th.measures) {
		return
	}

	measure := th.measures[measureIndex]
	fromVal := fromTime
	toVal := toTime

	if measure < 100 {
		fromVal %= 100
		toVal %= 100
		if toVal == 0 {
			toVal = 60
		}
	}

	for i := fromVal / measure; i <= (toVal / measure); i++ {
		key := measure * i

		if fromVal <= key && key+measure <= toVal {
			*terms = append(*terms, parentKey+th.twoDigitTerm(key))
		} else if key < fromVal && fromVal < key+measure {
			end := key + measure
			if toVal < end {
				end = toVal
			}
			th.cover(terms, measureIndex+1,
				parentKey+th.twoDigitTerm(key),
				fromVal, end)
		} else if key < toVal && toVal < key+measure {
			th.cover(terms, measureIndex+1,
				parentKey+th.twoDigitTerm(key),
				key, toVal)
		}
	}
}
