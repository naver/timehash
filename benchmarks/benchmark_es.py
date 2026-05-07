# Timehash
# Copyright (c) 2026-present NAVER Corp.
# Apache-2.0

"""
Elasticsearch benchmark: within-ES comparison of two temporal range indexing strategies.

  A. ES integer_range + contains query  (BKD tree, ES native)
  B. ES Timehash keyword terms          (inverted index, composable)

Both share the same HTTP/JVM overhead → apples-to-apples comparison.
Scales: 100K, 1M POIs.  Same synthetic distribution as benchmark.py.
"""

import random
import time
import sys
import os
import statistics

from elasticsearch import Elasticsearch, helpers

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../python"))
from timehash import Timehash

# ── configuration ──────────────────────────────────────────────────────────────
SCALES       = [100_000, 1_000_000]
N_QUERIES    = 1_000
QUERY_START  = 8 * 60    # 08:00
QUERY_END    = 22 * 60   # 22:00
RANDOM_SEED  = 42
WARMUP_N     = 100

INDEX_RANGE    = "biz_range"
INDEX_TIMEHASH = "biz_timehash"


def get_es() -> Elasticsearch:
    return Elasticsearch(["http://localhost:9200"], timeout=60)


# ── synthetic data (same distribution as benchmark.py) ────────────────────────

def random_start_minute() -> int:
    r = random.random()
    if r < 0.837:  return 0
    if r < 0.992:  return 30
    return random.randint(1, 59)


def generate_poi(poi_id: int) -> dict:
    start_hour = random.randint(6, 11)
    start = start_hour * 60 + random_start_minute()
    duration = max(60, int(random.gauss(454, 120)))
    end = min(start + duration, 1440)
    ranges = []
    if random.random() < 0.091:
        mid = start + (end - start) // 2
        blen = random.choice([60, 90, 120, 180])
        bs = max(mid - blen // 2, start + 30)
        be = min(mid + blen // 2, end - 30)
        ranges = [(start, bs), (be, end)] if bs < be else [(start, end)]
    else:
        ranges = [(start, end)]
    return {"id": poi_id, "ranges": ranges}


def generate_dataset(n: int) -> list:
    print(f"  Generating {n:,} POIs...", end=" ", flush=True)
    t0 = time.time()
    data = [generate_poi(i) for i in range(n)]
    print(f"{time.time()-t0:.1f}s")
    return data


def generate_queries() -> list:
    return [random.randint(QUERY_START, QUERY_END) for _ in range(N_QUERIES)]


def to_hhmm(minutes: int) -> str:
    h, m = divmod(minutes, 60)
    return f"{h:02d}{m:02d}"


def ground_truth(dataset: list, q: int) -> set:
    result = set()
    for poi in dataset:
        for (s, e) in poi["ranges"]:
            if s <= q < e:
                result.add(poi["id"])
                break
    return result


def precision(got: set, expected: set) -> float:
    if not got:
        return 1.0 if not expected else 0.0
    return len(got & expected) / len(got)


def measure_latency(fn, queries: list, repeat: int = 3) -> dict:
    lats = []
    for q in queries:
        runs = []
        for _ in range(repeat):
            t0 = time.perf_counter_ns()
            fn(q)
            runs.append(time.perf_counter_ns() - t0)
        lats.append(min(runs) / 1_000)   # ns → µs
    lats.sort()
    return {
        "p50": statistics.median(lats),
        "p95": lats[int(len(lats) * 0.95)],
    }


# ── A. ES integer_range (BKD tree) ────────────────────────────────────────────

def build_range_index(es: Elasticsearch, dataset: list, n: int) -> float:
    if es.indices.exists(index=INDEX_RANGE):
        es.indices.delete(index=INDEX_RANGE)
    es.indices.create(index=INDEX_RANGE, body={
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "refresh_interval": "-1",
            "index.max_result_window": min(n * 2, 500_000),
        },
        "mappings": {
            "properties": {
                "poi_id": {"type": "integer"},
                "hours":  {"type": "integer_range"},
            }
        }
    })
    t0 = time.time()
    actions = [
        {"_index": INDEX_RANGE,
         "_source": {"poi_id": poi["id"], "hours": {"gte": s, "lte": e - 1}}}
        for poi in dataset for (s, e) in poi["ranges"]
    ]
    helpers.bulk(es, actions, chunk_size=5_000, request_timeout=120)
    es.indices.refresh(index=INDEX_RANGE)
    return time.time() - t0


def query_range(es: Elasticsearch, q: int, size: int = 50_000) -> set:
    resp = es.search(index=INDEX_RANGE, body={
        "size": size,
        "_source": ["poi_id"],
        "query": {"range": {"hours": {"gte": q, "lte": q, "relation": "contains"}}}
    }, request_timeout=60)
    return {hit["_source"]["poi_id"] for hit in resp["hits"]["hits"]}


# ── B. ES Timehash keyword terms ──────────────────────────────────────────────

def build_timehash_index(es: Elasticsearch, dataset: list, th: Timehash,
                          n: int) -> tuple:
    if es.indices.exists(index=INDEX_TIMEHASH):
        es.indices.delete(index=INDEX_TIMEHASH)
    es.indices.create(index=INDEX_TIMEHASH, body={
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "refresh_interval": "-1",
            "index.max_result_window": min(n * 2, 500_000),
        },
        "mappings": {
            "properties": {
                "poi_id":        {"type": "integer"},
                "timehash_keys": {"type": "keyword"},
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
            "_source": {"poi_id": poi["id"], "timehash_keys": list(keys)}
        })
    helpers.bulk(es, actions, chunk_size=5_000, request_timeout=120)
    es.indices.refresh(index=INDEX_TIMEHASH)
    return time.time() - t0, total_terms / len(dataset)


def query_timehash(es: Elasticsearch, th: Timehash, q: int,
                   size: int = 50_000) -> set:
    h, m = divmod(q, 60)
    keys = th.get_query_terms(h * 100 + m)
    resp = es.search(index=INDEX_TIMEHASH, body={
        "size": size,
        "_source": ["poi_id"],
        "query": {"terms": {"timehash_keys": keys}}
    }, request_timeout=60)
    return {hit["_source"]["poi_id"] for hit in resp["hits"]["hits"]}


# ── main ──────────────────────────────────────────────────────────────────────

def run(n: int, queries: list):
    print(f"\n{'='*60}")
    print(f"Scale: {n:,} POIs")
    print(f"{'='*60}")

    random.seed(RANDOM_SEED)
    dataset  = generate_dataset(n)
    sample   = queries[:100]
    es       = get_es()
    th       = Timehash()
    results  = {}

    # Use 10K fetch_size consistently across all scales (production-realistic top-N).
    # This avoids latency being dominated by JSON serialization of large result sets.
    fetch_size = 10_000

    # ── A. integer_range ──
    print("  [ES integer_range] building...", end=" ", flush=True)
    bt = build_range_index(es, dataset, n)
    print(f"done ({bt:.2f}s)")
    for q in queries[:WARMUP_N]:          # JVM + cache warmup
        query_range(es, q, fetch_size)
    lat = measure_latency(lambda q: query_range(es, q, fetch_size), queries)
    prec_vals = [precision(query_range(es, q, fetch_size), ground_truth(dataset, q))
                 for q in sample]
    results["ES integer_range"] = {"build": bt, **lat, "prec": statistics.mean(prec_vals)}

    # ── B. ES Timehash ──
    print("  [ES Timehash] building...", end=" ", flush=True)
    bt, tpd = build_timehash_index(es, dataset, th, n)
    print(f"done ({bt:.2f}s, {tpd:.1f} terms/doc)")
    for q in queries[:WARMUP_N]:
        query_timehash(es, th, q, fetch_size)
    lat = measure_latency(lambda q: query_timehash(es, th, q, fetch_size), queries)
    prec_vals = [precision(query_timehash(es, th, q, fetch_size), ground_truth(dataset, q))
                 for q in sample]
    results["ES Timehash"] = {"build": bt, "terms_per_doc": tpd,
                              **lat, "prec": statistics.mean(prec_vals)}

    # ── table ──
    print(f"\n  {'Method':<22} {'Terms/Doc':>10} {'Build(s)':>9} "
          f"{'P50(ms)':>8} {'P95(ms)':>8} {'Prec':>6}")
    print(f"  {'-'*66}")
    for name, r in results.items():
        tpd_str = f"{r['terms_per_doc']:.1f}" if "terms_per_doc" in r else "—"
        print(f"  {name:<22} {tpd_str:>10} {r['build']:>9.2f} "
              f"{r['p50']/1000:>8.1f} {r['p95']/1000:>8.1f} {r['prec']:>6.3f}")

    return results


if __name__ == "__main__":
    es = get_es()
    if not es.ping():
        print("ERROR: Elasticsearch is not running at localhost:9200")
        sys.exit(1)
    ver = es.info()["version"]["number"]
    print(f"Connected to Elasticsearch {ver}")

    random.seed(RANDOM_SEED)
    queries = generate_queries()

    all_results = {}
    for scale in SCALES:
        all_results[scale] = run(scale, queries)

    print("\n\n" + "="*60)
    print("SUMMARY (P50 latency in ms)")
    print("="*60)
    for scale, res in all_results.items():
        print(f"\n{scale:>10,} POIs:")
        for name, r in res.items():
            print(f"  {name:<22}  P50={r['p50']/1000:6.1f}ms  "
                  f"P95={r['p95']/1000:6.1f}ms  Prec={r['prec']:.3f}")
