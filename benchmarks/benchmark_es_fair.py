# Timehash
# Copyright (c) 2026-present NAVER Corp.
# Apache-2.0

"""
FAIR within-Elasticsearch composability benchmark.

Addresses two methodological concerns raised in the methodology audit:

  (1) Per-doc asymmetry: previous BKD index used 1 ES doc per (poi, day-range),
      yielding ~4x more docs than Timehash index (1 ES doc per poi). This
      conflates "indexing strategy" with "algorithm" in the latency comparison.

  (2) Top-K cherry-picking: size=20 vs size=10000 yielded very different
      narratives (TH 2x faster vs BKD 1.3x faster). Need a K-curve to
      characterize where each method dominates.

This benchmark fixes both:

  (1) BKD index now uses multi-valued integer_range: 1 doc per poi with array
      of ranges. Doc counts match Timehash exactly (~127K each).

  (2) Latency measured at K = 10, 100, 1000, 10000. Precision/recall verified
      at K = 200000 (no truncation).

Three predicate forms tested per K value:
  P1: time only
  P2: time + category
  P3: time + category + state

USAGE
-----
    python benchmark_es_fair.py /path/to/yelp_academic_dataset_business.json
"""

import argparse
import json
import random
import statistics
import sys
import os
import time

from elasticsearch import Elasticsearch, helpers

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../python"))
from timehash import Timehash

# ── configuration ──────────────────────────────────────────────────────────────
N_QUERIES    = 1_000
QUERY_START  = 8 * 60
QUERY_END    = 22 * 60
RANDOM_SEED  = 42
WARMUP_N     = 100

INDEX_RANGE    = "yelp_fair_range"
INDEX_TIMEHASH = "yelp_fair_timehash"

K_VALUES   = [10, 100, 1000, 10000]
VERIFY_K   = 200_000

TOP_CATEGORIES = ["Restaurants", "Shopping", "Beauty & Spas", "Bars", "Coffee & Tea"]
TOP_STATES     = ["PA", "FL", "TN", "IN", "MO"]


def get_es() -> Elasticsearch:
    return Elasticsearch(["http://localhost:9200"], timeout=120)


# ── Yelp loader (same as benchmark_es_multi3.py) ─────────────────────────────

DAYS = ("Monday", "Tuesday", "Wednesday", "Thursday",
        "Friday", "Saturday", "Sunday")


def parse_hhmm(s: str) -> int:
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def parse_yelp_range(spec):
    try:
        start_s, end_s = spec.split("-")
        start = parse_hhmm(start_s)
        end = parse_hhmm(end_s)
        if end == 0:
            end = 24 * 60
        if end <= start:
            end = 24 * 60
        if not (0 <= start < end <= 24 * 60):
            return None
        return (start, end)
    except (ValueError, AttributeError):
        return None


def load_yelp(business_json_path):
    print(f"  Loading {business_json_path}...", end=" ", flush=True)
    t0 = time.time()
    dataset = []
    poi_id = 0
    with open(business_json_path) as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            hours = rec.get("hours")
            cats_str = rec.get("categories")
            state = rec.get("state")
            if not hours or not cats_str or not state:
                continue
            seen = set()
            for d in DAYS:
                spec = hours.get(d)
                if spec is None:
                    continue
                r = parse_yelp_range(spec)
                if r is not None:
                    seen.add(r)
            if seen:
                categories = [c.strip() for c in cats_str.split(",")]
                dataset.append({
                    "id": poi_id,
                    "ranges": list(seen),
                    "categories": categories,
                    "state": state,
                })
                poi_id += 1
    print(f"{time.time()-t0:.1f}s, {len(dataset):,} businesses")
    return dataset


def generate_queries():
    rng = random.Random(RANDOM_SEED)
    return [(rng.randint(QUERY_START, QUERY_END),
             rng.choice(TOP_CATEGORIES),
             rng.choice(TOP_STATES))
            for _ in range(N_QUERIES)]


def to_hhmm(minutes):
    h, m = divmod(minutes, 60)
    return f"{h:02d}{m:02d}"


def measure_latency(fn, queries, repeat=3):
    lats = []
    for q in queries:
        runs = []
        for _ in range(repeat):
            t0 = time.perf_counter_ns()
            fn(q)
            runs.append(time.perf_counter_ns() - t0)
        lats.append(min(runs) / 1_000)
    lats.sort()
    return {
        "p50": statistics.median(lats),
        "p95": lats[int(len(lats) * 0.95)],
        "mean": statistics.mean(lats),
    }


# ── A. BKD index: 1 doc per poi, multi-valued integer_range ──────────────────

def build_range_index(es, dataset):
    if es.indices.exists(index=INDEX_RANGE):
        es.indices.delete(index=INDEX_RANGE)
    es.indices.create(index=INDEX_RANGE, body={
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "refresh_interval": "-1",
            "index.max_result_window": 500_000,
        },
        "mappings": {
            "properties": {
                "poi_id":     {"type": "integer"},
                "hours":      {"type": "integer_range"},
                "categories": {"type": "keyword"},
                "state":      {"type": "keyword"},
            }
        }
    })
    t0 = time.time()
    actions = []
    for poi in dataset:
        hours_array = [{"gte": s, "lte": e - 1} for (s, e) in poi["ranges"]]
        actions.append({
            "_index": INDEX_RANGE,
            "_source": {
                "poi_id": poi["id"],
                "hours":  hours_array,
                "categories": poi["categories"],
                "state": poi["state"],
            }
        })
    helpers.bulk(es, actions, chunk_size=5_000, request_timeout=120)
    es.indices.refresh(index=INDEX_RANGE)
    n_docs = es.count(index=INDEX_RANGE)["count"]
    return time.time() - t0, n_docs


def query_range(es, q, size, k_predicates):
    q_time, q_cat, q_state = q
    filters = [{"range": {"hours": {"gte": q_time, "lte": q_time, "relation": "contains"}}}]
    if k_predicates >= 2:
        filters.append({"term": {"categories": q_cat}})
    if k_predicates >= 3:
        filters.append({"term": {"state": q_state}})
    resp = es.search(index=INDEX_RANGE, body={
        "size": size,
        "_source": ["poi_id"],
        "query": {"bool": {"filter": filters}}
    }, request_timeout=60)
    return {hit["_source"]["poi_id"] for hit in resp["hits"]["hits"]}


# ── B. Timehash index: 1 doc per poi (already) ───────────────────────────────

def build_timehash_index(es, dataset, th):
    if es.indices.exists(index=INDEX_TIMEHASH):
        es.indices.delete(index=INDEX_TIMEHASH)
    es.indices.create(index=INDEX_TIMEHASH, body={
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "refresh_interval": "-1",
            "index.max_result_window": 500_000,
        },
        "mappings": {
            "properties": {
                "poi_id":        {"type": "integer"},
                "timehash_keys": {"type": "keyword"},
                "categories":    {"type": "keyword"},
                "state":         {"type": "keyword"},
            }
        }
    })
    t0 = time.time()
    total_terms = 0
    actions = []
    for poi in dataset:
        keys = set()
        for (s, e) in poi["ranges"]:
            keys.update(th.get_index_terms(to_hhmm(s), to_hhmm(e)))
        total_terms += len(keys)
        actions.append({
            "_index": INDEX_TIMEHASH,
            "_source": {
                "poi_id":        poi["id"],
                "timehash_keys": list(keys),
                "categories":    poi["categories"],
                "state":         poi["state"],
            }
        })
    helpers.bulk(es, actions, chunk_size=5_000, request_timeout=120)
    es.indices.refresh(index=INDEX_TIMEHASH)
    n_docs = es.count(index=INDEX_TIMEHASH)["count"]
    return time.time() - t0, total_terms / len(dataset), n_docs


def query_timehash(es, th, q, size, k_predicates):
    q_time, q_cat, q_state = q
    h, m = divmod(q_time, 60)
    keys = th.get_query_terms(h * 100 + m)
    filters = [{"terms": {"timehash_keys": keys}}]
    if k_predicates >= 2:
        filters.append({"term": {"categories": q_cat}})
    if k_predicates >= 3:
        filters.append({"term": {"state": q_state}})
    resp = es.search(index=INDEX_TIMEHASH, body={
        "size": size,
        "_source": ["poi_id"],
        "query": {"bool": {"filter": filters}}
    }, request_timeout=60)
    return {hit["_source"]["poi_id"] for hit in resp["hits"]["hits"]}


# ── ground truth + precision/recall ──────────────────────────────────────────

def ground_truth(dataset, q_time, q_cat, q_state, k_predicates):
    result = set()
    for poi in dataset:
        if k_predicates >= 2 and q_cat not in poi["categories"]:
            continue
        if k_predicates >= 3 and poi["state"] != q_state:
            continue
        for (s, e) in poi["ranges"]:
            if s <= q_time < e:
                result.add(poi["id"])
                break
    return result


def measure_precision_recall(method_fn, dataset, queries, k_predicates, n_sample=50):
    precisions = []
    recalls = []
    for q in queries[:n_sample]:
        got = method_fn(q)
        expected = ground_truth(dataset, q[0], q[1], q[2], k_predicates)
        if got:
            p = len(got & expected) / len(got)
        else:
            p = 1.0 if not expected else 0.0
        if expected:
            r = len(got & expected) / len(expected)
        else:
            r = 1.0
        precisions.append(p)
        recalls.append(r)
    return {"precision": statistics.mean(precisions), "recall": statistics.mean(recalls)}


# ── main ──────────────────────────────────────────────────────────────────────

def run(dataset, queries):
    n = len(dataset)
    print(f"\n{'='*78}")
    print(f"FAIR composability benchmark: {n:,} businesses (Yelp), multi-valued BKD")
    print(f"{'='*78}")

    es = get_es()
    th = Timehash()

    # ── build indexes ──
    print("  [BKD] building index (1 doc/poi, multi-valued integer_range)...", end=" ", flush=True)
    bt_bkd, n_bkd_docs = build_range_index(es, dataset)
    print(f"done ({bt_bkd:.2f}s, {n_bkd_docs:,} docs)")

    print("  [Timehash] building index (1 doc/poi, multi-valued keyword)...", end=" ", flush=True)
    bt_th, tpd, n_th_docs = build_timehash_index(es, dataset, th)
    print(f"done ({bt_th:.2f}s, {tpd:.1f} terms/doc, {n_th_docs:,} docs)")

    print(f"\n  Doc count asymmetry resolved: BKD={n_bkd_docs:,}, TH={n_th_docs:,} (ratio={n_bkd_docs/n_th_docs:.2f}x)")

    # ── precision/recall sanity check (size=VERIFY_K) ──
    print(f"\n  [precision/recall] validating algorithmic correctness (size={VERIFY_K})...")
    for kp in (1, 2, 3):
        bkd_pr = measure_precision_recall(lambda q: query_range(es, q, VERIFY_K, kp), dataset, queries, kp)
        th_pr  = measure_precision_recall(lambda q: query_timehash(es, th, q, VERIFY_K, kp), dataset, queries, kp)
        print(f"    P{kp}: BKD precision={bkd_pr['precision']:.4f} recall={bkd_pr['recall']:.4f}   "
              f"TH precision={th_pr['precision']:.4f} recall={th_pr['recall']:.4f}")

    # ── latency curve over K ──
    print(f"\n  [latency curve] measuring at K = {K_VALUES}")

    results = {}
    for k in K_VALUES:
        print(f"\n  ── size={k} ─────────────────────────────────────")
        for kp in (1, 2, 3):
            # warmup
            for q in queries[:WARMUP_N]:
                query_range(es, q, k, kp)
                query_timehash(es, th, q, k, kp)
            bkd_lat = measure_latency(lambda q: query_range(es, q, k, kp), queries)
            th_lat  = measure_latency(lambda q: query_timehash(es, th, q, k, kp), queries)
            ratio = bkd_lat["p50"] / th_lat["p50"] if th_lat["p50"] > 0 else 0
            winner = f"TH {ratio:.2f}x" if ratio > 1 else f"BKD {1/ratio:.2f}x"
            results[(k, kp)] = {"bkd": bkd_lat, "th": th_lat, "ratio": ratio, "winner": winner}
            print(f"    P{kp}: BKD P50={bkd_lat['p50']/1000:7.2f}ms P95={bkd_lat['p95']/1000:7.2f}ms   "
                  f"TH P50={th_lat['p50']/1000:7.2f}ms P95={th_lat['p95']/1000:7.2f}ms   {winner}")

    # ── summary matrix ──
    print(f"\n  {'='*78}")
    print("  SUMMARY MATRIX: P50 latency (ms) — same docs/poi, fair comparison")
    print(f"  {'='*78}")
    print(f"  {'K (size)':<10}", end="")
    for kp in (1, 2, 3):
        print(f"{'P'+str(kp)+' BKD':>9} {'P'+str(kp)+' TH':>9} {'Winner':>11}", end=" ")
    print()
    print(f"  {'-'*78}")
    for k in K_VALUES:
        print(f"  {k:<10}", end="")
        for kp in (1, 2, 3):
            r = results[(k, kp)]
            print(f"{r['bkd']['p50']/1000:>9.2f} {r['th']['p50']/1000:>9.2f} {r['winner']:>11}", end=" ")
        print()

    return results


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("business_json")
    args = ap.parse_args()

    es = get_es()
    if not es.ping():
        print("ERROR: Elasticsearch not running at localhost:9200"); sys.exit(1)
    print(f"Connected to ES {es.info()['version']['number']}")

    dataset = load_yelp(args.business_json)
    queries = generate_queries()
    results = run(dataset, queries)
