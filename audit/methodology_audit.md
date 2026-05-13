# Multi-Predicate Composability Benchmark — Methodology Audit

This document records the methodology iteration history behind the within-Elasticsearch composability benchmark reported in the Timehash paper (Section 5.5, Table 8). The final fair-comparison numbers in the paper come from `benchmarks/es_fair_results.log`; the intermediate logs in this directory (`es_multi3_results.log`, `es_multi3_topk_results.log`) are kept as the audit trail explaining why earlier methodology choices were corrected.

- **Dataset:** Yelp Open Dataset (127,123 US/CA businesses with hours + category + state, real data)
- **Elasticsearch:** 7.17.4, single shard, no replicas, localhost
- **Configuration:** 1,000 random queries, seed 42, 100 warmup, repeat = 3 (take min per query), P50/P95 over the 1k

The benchmark went through three runs as methodological flaws were discovered and corrected:

| Run | What it measured | Flaw discovered | Lesson |
|-----|------------------|-----------------|--------|
| **Run 1** (`es_multi3_results.log`) | size = 10K, 1 doc per (poi, range) for BKD | Truncation: BKD index had ~4× more documents → hit the 10K cap earlier → asymmetric recall (BKD 6–97 %, TH 11–100 %) | size = 10K conflates filter cost with materialization cost |
| **Run 2** (`es_multi3_topk_results.log`) | size = 20 top-K + size = 200K verification | Cherry-pick risk: a single K value can be selectively favourable; doc-count asymmetry not addressed | Need a K-curve and matched doc counts |
| **Run 3** (`es_fair_results.log`) | BKD index restructured to 1 doc/poi with multi-valued `integer_range`; K = 10 / 100 / 1000 / 10000 | None known | Apples-to-apples comparison; this is the result reported in the paper |

## Run 3 — fair-comparison summary

Same dataset (Yelp 127K). Same indexing granularity (1 doc per business for both methods, multi-valued range or keyword fields). Same query forms. `K` is varied to characterize the latency curve.

| K | P1 (time) | P2 (+ category) | P3 (+ category + state) |
|---|-----------|------------------|-------------------------|
| 10 | TH 2.17× | TH 1.57× | TH 1.28× |
| 100 | TH 1.53× | TH 1.33× | TH 1.14× |
| 1000 | TH 1.08× | TH 1.01× | TH 1.04× |
| 10000 | BKD 1.02× | BKD 1.02× | TH 1.01× |

`a×` means the winning method's P50 is `a` times faster than the other method's P50.

**Algorithmic correctness:** precision = 1.000, recall = 1.000 for both methods at all three predicate counts, verified at size = 200,000 (effectively unlimited).

**Headline:** Timehash dominates production-typical top-K (K ≤ 100); the methods converge to within 8 % by K = 1000 and to within 2 % at K = 10000 where document materialization dominates query cost.

## Mechanism interpretation

### Why does Timehash win at low K?

Elasticsearch short-circuits a `bool/filter + size = K` query after collecting K matching documents. The dominant cost is the access path to the first K hits. Three factors favour Timehash here:

1. **Uniform posting-list access path.** All filters traverse posting lists; Elasticsearch's skip-list-based AND iterator is the most optimised hot path in Lucene. Timehash's five query keys union and intersect with category/state posting lists entirely within this hot path.
2. **BKD requires path conversion.** The BKD tree yields a doc-id stream that must then be composed with the posting-list iterator. This is more code path and more cache misses.
3. **Posting-list seek efficiency.** Elasticsearch's skip-list iterator amortises well over sorted doc IDs from posting lists. BKD-derived doc IDs may not have the same skip-friendly locality.

### Why does the gap close as K grows?

- At K = 10: the query terminates after roughly 10 candidate evaluations. Dominated by per-evaluation overhead. Posting-list path wins.
- At K = 100: terminates after roughly 100 evaluations. Still dominated by filter cost, but more evaluations make the cumulative per-evaluation gap matter less in relative terms.
- At K = 1000: filter cost is still meaningful, but materialization (doc fetch + JSON serialization) starts to register. Methods converge.
- At K = 10000: materialization is 95 % or more of total query time. Filter algorithm is essentially invisible. Methods tied.

### Why does P3 < P1 at K = 10000?

P3 has a highly selective state filter. The result set is small (~8–12K matches across the dataset), so materialization cost is lower than for P1 where the result set hits the K = 10K cap. P3 at K = 10K measures actual full-result-set cost, not capped fetch. Both methods take ~8.7 ms — equal.

## What changed across the three runs

### Run 1 was misleading

The Run 1 strategy of 1 doc per `(poi, range)` created roughly 4× more BKD documents than Timehash documents. At size = 10K, BKD hit the truncation cap earlier (lower recall), and the latency comparison was contaminated by:

- BKD scanning ~4× more candidate documents.
- Asymmetric materialization costs.
- Truncation hiding the true full-result behaviour.

Run 1 reported "BKD 1.31× faster at P1/P2." **This finding does not survive fair-indexing correction.** Run 3 shows BKD only 1.02× faster at K = 10K — within noise.

### Run 2 partly recovered the right answer for partly the wrong reason

Run 2's "TH 2.00× faster at P1, top-K = 20" finding survives. In Run 3 with fair indexing, the same comparison at K = 10 yields TH 2.17× — slightly stronger. Run 2's headline number was real; the doc-count asymmetry was also helping (BKD had to plough through 4× more docs before reaching 20 hits). With fair indexing, BKD has fewer docs to scan but the access-path cost difference remains.

### Net effect

Run 3 strengthens the headline (TH wins more clearly at low K) and weakens the unfair-looking comparisons (large K is now a near-tie, not a BKD win).

## Reproducibility

- **Final script:** `benchmarks/benchmark_es_fair.py`
- **Final log:** `benchmarks/es_fair_results.log`
- **Intermediate logs (audit trail):**
  - Run 1 (unfair indexing, size = 10K): `audit/es_multi3_results.log`
  - Run 2 (unfair indexing, size = 20): `audit/es_multi3_topk_results.log`
- **Data:** Yelp Open Dataset (`yelp_academic_dataset_business.json`); download from https://business.yelp.com/data/resources/open-dataset/.

To reproduce the final result:

```bash
# Start ES 7.17 on localhost:9200
python3 benchmarks/benchmark_es_fair.py /path/to/yelp_academic_dataset_business.json
```

### Known limitations

- Single-shard Elasticsearch (production deployments use multiple shards; multi-shard latency adds merge overhead, likely a similar shift for both methods).
- Single-machine localhost (no network jitter).
- Categories sampled from the top five in the Yelp dataset; states sampled from the top five US states by business count.
- 1,000 queries, single run. For tight statistical confidence, three or more independent runs are recommended.
- Yelp 127K only; production scale (10M+) is not exercised here.
- Sub-millisecond measurements at K = 10 are subject to JVM warmup / GC jitter; P95 numbers are more robust than P50 in this regime.

## Lessons learned (for future composability benchmarks)

1. **Measure precision/recall against ground truth, not just inter-method consistency.** Inter-method mismatches can be benign (truncation) or critical (algorithm bug); precision/recall against ground truth localizes which.
2. **Match doc-per-entity counts before claiming an algorithmic advantage.** Indexing strategy asymmetry (here: 4× doc multiplication) can entirely produce a "winning" benchmark that disappears under fair comparison.
3. **K is a major confound for filter-cost benchmarks.** Single-K reports are easy to cherry-pick. A K-curve makes the trade-off explicit.
4. **Sub-millisecond measurements need P95.** Below ~5 ms, JVM/GC jitter dominates P50; P95 is the more robust statistic.
5. **size = 10K is rarely the right benchmark target.** Production search uses K = 10–100; analytics use K = 1000–10000 with sort; full-scan rarely has tight latency requirements. Pick K based on the workload being characterised.
