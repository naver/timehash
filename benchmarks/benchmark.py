# Timehash
# Copyright (c) 2026-present NAVER Corp.
# Apache-2.0

"""
Timehash benchmark: Timehash vs PostgreSQL TSRANGE/GiST vs baseline approaches.

Synthetic dataset generated from production distribution:
  - 83.7% start at :00, 15.5% at :30, 0.8% other
  - 9.1% have break times
  - Average duration ~454 minutes
"""

import random
import time
import sys
import os
import statistics
import psycopg2
import psycopg2.extras

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../python"))
from timehash import Timehash

# ── configuration ──────────────────────────────────────────────────────────────
SCALES       = [100_000, 1_000_000, 5_000_000, 12_600_000]
N_QUERIES    = 1_000
QUERY_START  = 8 * 60       # 08:00
QUERY_END    = 22 * 60      # 22:00
RANDOM_SEED  = 42

DB_NAME = "timehash_bench"
DB_USER = os.environ.get("USER", "postgres")
DB_HOST = "127.0.0.1"
DB_PORT = 5432

random.seed(RANDOM_SEED)


# ── synthetic data generation ──────────────────────────────────────────────────

def random_start_minute() -> int:
    """83.7% :00, 15.5% :30, 0.8% other"""
    r = random.random()
    if r < 0.837:
        return 0
    elif r < 0.992:
        return 30
    else:
        return random.randint(1, 59)


def generate_poi(poi_id: int) -> dict:
    """Generate one synthetic POI with realistic business hours."""
    start_hour = random.randint(6, 11)
    start_min  = random_start_minute()
    start      = start_hour * 60 + start_min

    # Duration: 454 min avg, normally distributed
    duration = max(60, int(random.gauss(454, 120)))
    end = min(start + duration, 1440)

    has_break = random.random() < 0.091
    ranges = []

    if has_break:
        mid      = start + (end - start) // 2
        break_len = random.choice([60, 90, 120, 180])
        break_end = min(mid + break_len // 2, end - 30)
        break_start = max(mid - break_len // 2, start + 30)
        if break_start < break_end:
            ranges = [(start, break_start), (break_end, end)]
        else:
            ranges = [(start, end)]
    else:
        ranges = [(start, end)]

    return {"id": poi_id, "ranges": ranges}


def to_hhmm(minutes: int) -> str:
    h, m = divmod(minutes, 60)
    return f"{h:02d}{m:02d}"


def generate_dataset(n: int) -> list:
    print(f"  Generating {n:,} synthetic POIs...", end=" ", flush=True)
    t0 = time.time()
    data = [generate_poi(i) for i in range(n)]
    print(f"{time.time()-t0:.1f}s")
    return data


def generate_queries(n: int = N_QUERIES) -> list:
    return [random.randint(QUERY_START, QUERY_END) for _ in range(n)]


# ── Timehash in-memory inverted index ─────────────────────────────────────────

class TimehashIndex:
    def __init__(self):
        self.th    = Timehash()
        self.index = {}   # term -> set of doc ids

    def build(self, dataset: list) -> float:
        t0 = time.time()
        for poi in dataset:
            for (s, e) in poi["ranges"]:
                for term in self.th.get_index_terms(to_hhmm(s), to_hhmm(e)):
                    self.index.setdefault(term, set()).add(poi["id"])
        return time.time() - t0

    def query(self, q_minutes: int) -> set:
        h, m = divmod(q_minutes, 60)
        hhmm = h * 100 + m
        result = set()
        for term in self.th.get_query_terms(hhmm):
            result |= self.index.get(term, set())
        return result

    def index_size(self) -> int:
        return sum(len(v) for v in self.index.values())


# ── Naive inverted indexes (1-min, 5-min, 1-hour) ─────────────────────────────

class NaiveIndex:
    def __init__(self, granularity: int):
        self.gran  = granularity   # minutes
        self.index = {}

    def build(self, dataset: list) -> float:
        t0 = time.time()
        for poi in dataset:
            for (s, e) in poi["ranges"]:
                t = (s // self.gran) * self.gran
                while t < e:
                    self.index.setdefault(t, set()).add(poi["id"])
                    t += self.gran
        return time.time() - t0

    def query(self, q_minutes: int) -> set:
        key = (q_minutes // self.gran) * self.gran
        return self.index.get(key, set())

    def index_size(self) -> int:
        return sum(len(v) for v in self.index.values())


# ── Scope filter (linear scan) ────────────────────────────────────────────────

class ScopeFilter:
    def __init__(self):
        self.data = []

    def build(self, dataset: list) -> float:
        t0 = time.time()
        self.data = dataset
        return time.time() - t0

    def query(self, q_minutes: int) -> set:
        result = set()
        for poi in self.data:
            for (s, e) in poi["ranges"]:
                if s <= q_minutes < e:
                    result.add(poi["id"])
                    break
        return result


# ── PostgreSQL TSRANGE + GiST ──────────────────────────────────────────────────

def get_conn():
    return psycopg2.connect(dbname=DB_NAME, user=DB_USER, host=DB_HOST, port=DB_PORT)


def setup_pg_db():
    conn = psycopg2.connect(dbname="postgres", user=DB_USER, host=DB_HOST, port=DB_PORT)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
    cur.execute(f"CREATE DATABASE {DB_NAME}")
    cur.close()
    conn.close()


def build_pg_index(dataset: list) -> float:
    conn = get_conn()
    cur  = conn.cursor()

    cur.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    cur.execute("DROP TABLE IF EXISTS biz_hours")
    cur.execute("""
        CREATE TABLE biz_hours (
            poi_id  INTEGER NOT NULL,
            hours   INT4RANGE NOT NULL
        )
    """)

    rows = []
    for poi in dataset:
        for (s, e) in poi["ranges"]:
            rows.append((poi["id"], psycopg2.extras.NumericRange(s, e)))

    t0 = time.time()
    psycopg2.extras.execute_values(
        cur,
        "INSERT INTO biz_hours (poi_id, hours) VALUES %s",
        rows,
        page_size=10_000
    )
    cur.execute("CREATE INDEX biz_hours_gist ON biz_hours USING gist (hours)")
    conn.commit()
    elapsed = time.time() - t0

    cur.close()
    conn.close()
    return elapsed


def query_pg(cur, q_minutes: int) -> set:
    cur.execute(
        "SELECT DISTINCT poi_id FROM biz_hours WHERE hours @> %s::integer",
        (q_minutes,)
    )
    return {row[0] for row in cur.fetchall()}


def pg_table_size() -> int:
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("""
        SELECT pg_relation_size('biz_hours') + pg_relation_size('biz_hours_gist')
    """)
    size = cur.fetchone()[0]
    cur.close()
    conn.close()
    return size


# ── latency measurement ────────────────────────────────────────────────────────

def measure_latency(query_fn, queries: list, repeat: int = 5) -> dict:
    """Time each query repeated `repeat` times and take the min run (warm cache)."""
    latencies = []
    for q in queries:
        timings = []
        for _ in range(repeat):
            t0 = time.perf_counter_ns()
            query_fn(q)
            timings.append(time.perf_counter_ns() - t0)
        latencies.append(min(timings) / 1_000)  # ns → µs

    latencies.sort()
    return {
        "p50": statistics.median(latencies),
        "p95": latencies[int(len(latencies) * 0.95)],
        "p99": latencies[int(len(latencies) * 0.99)],
    }


# ── ground truth ───────────────────────────────────────────────────────────────

def ground_truth(dataset: list, q_minutes: int) -> set:
    result = set()
    for poi in dataset:
        for (s, e) in poi["ranges"]:
            if s <= q_minutes < e:
                result.add(poi["id"])
                break
    return result


def precision_recall(got: set, expected: set) -> tuple:
    if not got:
        return (1.0, 0.0) if not expected else (0.0, 0.0)
    p = len(got & expected) / len(got)
    r = len(got & expected) / len(expected) if expected else 1.0
    return p, r


# ── main benchmark ─────────────────────────────────────────────────────────────

def run_benchmark(n: int, queries: list):
    print(f"\n{'='*60}")
    print(f"Scale: {n:,} POIs")
    print(f"{'='*60}")

    dataset = generate_dataset(n)
    results = {}

    # ── Scope filter ──
    if n <= 100_000:
        print("  [Scope filter] building...", end=" ", flush=True)
        sf = ScopeFilter()
        bt = sf.build(dataset)
        lat = measure_latency(sf.query, queries)
        print(f"done ({bt:.2f}s)")
        results["Scope filter"] = {"build": bt, **lat, "terms": n, "prec": 1.0}

    # ── 1-minute index ──
    if n <= 1_000_000:
        print("  [1-min index] building...", end=" ", flush=True)
        idx1 = NaiveIndex(1)
        bt = idx1.build(dataset)
        lat = measure_latency(idx1.query, queries)
        terms_per_doc = idx1.index_size() / n
        print(f"done ({bt:.2f}s, {terms_per_doc:.1f} terms/doc)")
        results["1-min"] = {"build": bt, **lat, "terms": terms_per_doc, "prec": 1.0}

    sample = random.sample(queries, min(100, len(queries)))

    # ── 5-minute index ──
    if n <= 5_000_000:
        print("  [5-min index] building...", end=" ", flush=True)
        idx5 = NaiveIndex(5)
        bt = idx5.build(dataset)
        lat = measure_latency(idx5.query, queries)
        terms_per_doc = idx5.index_size() / n
        print(f"done ({bt:.2f}s, {terms_per_doc:.1f} terms/doc)")
        prec_vals = []
        for q in sample:
            gt = ground_truth(dataset, q)
            got = idx5.query(q)
            p, _ = precision_recall(got, gt)
            prec_vals.append(p)
        results["5-min"] = {"build": bt, **lat, "terms": terms_per_doc,
                            "prec": statistics.mean(prec_vals)}

    # ── 1-hour index ──
    print("  [1-hour index] building...", end=" ", flush=True)
    idx60 = NaiveIndex(60)
    bt = idx60.build(dataset)
    lat = measure_latency(idx60.query, queries)
    terms_per_doc = idx60.index_size() / n
    print(f"done ({bt:.2f}s, {terms_per_doc:.1f} terms/doc)")
    prec_vals = []
    for q in sample:
        gt = ground_truth(dataset, q)
        got = idx60.query(q)
        p, _ = precision_recall(got, gt)
        prec_vals.append(p)
    results["1-hour"] = {"build": bt, **lat, "terms": terms_per_doc,
                         "prec": statistics.mean(prec_vals)}

    # ── Timehash ──
    print("  [Timehash] building...", end=" ", flush=True)
    th_idx = TimehashIndex()
    bt = th_idx.build(dataset)
    lat = measure_latency(th_idx.query, queries)
    terms_per_doc = th_idx.index_size() / n
    prec_vals = []
    for q in sample:
        gt = ground_truth(dataset, q)
        got = th_idx.query(q)
        p, _ = precision_recall(got, gt)
        prec_vals.append(p)
    print(f"done ({bt:.2f}s, {terms_per_doc:.1f} terms/doc)")
    results["Timehash"] = {"build": bt, **lat, "terms": terms_per_doc,
                           "prec": statistics.mean(prec_vals)}

    # ── PostgreSQL TSRANGE + GiST ──
    if n <= 1_000_000:
        print("  [PostgreSQL GiST] building...", end=" ", flush=True)
        setup_pg_db()
        bt = build_pg_index(dataset)
        pg_size = pg_table_size()
        conn = get_conn()
        cur  = conn.cursor()
        lat  = measure_latency(lambda q: query_pg(cur, q), queries)
        prec_vals = []
        for q in sample:
            gt  = ground_truth(dataset, q)
            got = query_pg(cur, q)
            p, _ = precision_recall(got, gt)
            prec_vals.append(p)
        cur.close()
        conn.close()
        print(f"done ({bt:.2f}s, {pg_size/1024/1024:.1f} MB)")
        results["PostgreSQL GiST"] = {
            "build": bt, **lat,
            "terms": f"{pg_size/1024/1024:.1f} MB (total)",
            "prec": statistics.mean(prec_vals)
        }

    # ── print table ──
    print(f"\n  {'Method':<20} {'Terms/Doc':>10} {'Build(s)':>9} {'P50(µs)':>9} {'P95(µs)':>9} {'Prec':>6}")
    print(f"  {'-'*67}")
    for name, r in results.items():
        print(f"  {name:<20} {str(r['terms']):>10} {r['build']:>9.2f} "
              f"{r['p50']:>9.0f} {r['p95']:>9.0f} {r['prec']:>6.3f}")

    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", type=int, default=None,
                        help="Number of POIs (default: run all scales)")
    args = parser.parse_args()

    queries = generate_queries()
    scales = [args.scale] if args.scale else SCALES
    for scale in scales:
        run_benchmark(scale, queries)
