/*
 * Timehash
 * Copyright (c) 2026-present NAVER Corp.
 * Apache-2.0
 */

#ifndef __TIMEHASH_HPP__
#define __TIMEHASH_HPP__

#include <vector>
#include <string>
#include <cstdio>

/**
 *  Timehash is designed for time-based search.
 *  Useful for checking if a business operating from FROM~TO is open at a specific time A.
 *
 *  Supports multi-depth precision (precision set is called "measures") to reduce hash key set size
 *  while fully covering smaller time intervals.
 */
    class Timehash {
        public:
            /**
             *  Creates a Timehash instance with default options.
             *
             *  - measures: {400, 100, 15, 5, 1}
             */
            Timehash() = default;
            ~Timehash() = default;

            /**
             *  Sets the precision set.
             *
             *  @param measures Precision set for dividing time intervals.
             */
            void setMeasures(std::vector<int> measures) {
                measures_ = std::move(measures);
            }

            /**
             *  Converts a query term in hhmm format to hash keys at each depth.
             *
             *  @param hhmm Time as int in hhmm format. e.g., 17:20 -> 1720
             *  @return Vector of hash keys converted from hhmm at each depth.
             */
            std::vector<std::string> getQueryTerms(int hhmm) {
                std::vector<std::string> terms;

                if (hhmm > 10000) {
                    return terms;
                }

                for (auto measure : measures_) {
                    int target = hhmm;

                    if (measure >= 100) {
                        target /= 100;
                        measure /= 100;
                    }
                    else {
                        target %= 100;
                    }

                    int key = (target / measure) * measure;
                    std::string term = twoDigitTerm(key);

                    if (terms.empty()) {
                        terms.push_back(term);
                    }
                    else {
                        terms.push_back(terms.back() + term);
                    }
                }

                return terms;
            }

            /**
             *  Converts a time range expressed as FROM~TO to Timehash keys.
             *
             *  @param from Start of time range. String in hhmm format.
             *  @param to End of time range. String in hhmm format.
             *  @return Set of timehash keys as string vector.
             */
            std::vector<std::string> getIndexTerms(std::string from, std::string to) {
                std::vector<std::string> terms;
                cover(terms, 0, "", std::stoi(from), std::stoi(to));

                return terms;
            }

        private:
            std::vector<int> measures_ = {400, 100, 15, 5, 1};

            std::string twoDigitTerm(int key) {
                if (key >= 100) {
                    key /= 100;
                }

                char term[3] = {};
                std::snprintf(term, sizeof(term), "%d%d", key / 10, key % 10);

                return std::string(term);
            }

            void cover(std::vector<std::string>& terms, size_t measureIndex, std::string parentKey, int from, int to) {
                if (measureIndex >= measures_.size()) {
                    return ;
                }

                int measure = measures_[measureIndex];

                if (measure < 100) {
                    from %= 100;
                    to %= 100;

                    if (to == 0) {
                        to = 60;
                    }
                }

                for (int i = from / measure; i < (to / measure) + 1; i++) {
                    int key = measure * i;

                    if (from <= key && key + measure <= to) {
                        terms.push_back(parentKey + twoDigitTerm(key));
                    }
                    else if (key < from && from < key + measure) {
                        int end = (to < key + measure) ? to : key + measure;
                        cover(terms, measureIndex + 1, parentKey + twoDigitTerm(key), from, end);
                    }
                    else if (key < to && to < key + measure) {
                        cover(terms, measureIndex + 1, parentKey + twoDigitTerm(key), key, to);
                    }
                }

                return ;
            }
    };

#endif
