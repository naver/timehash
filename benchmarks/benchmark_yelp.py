# Timehash
# Copyright (c) 2026-present NAVER Corp.
# Apache-2.0

"""
Yelp Open Dataset cross-validation for Timehash hierarchy choice.

Reproduces, on Yelp's US business hours data, the same analysis that
§7.1 / Table 4 perform on the production distribution:

  1. Start-time distribution: fraction of POIs opening at :00, :15, :30, :45,
     and the long tail of non-aligned minutes.
  2. Hierarchy optimization sweep: for 2- to 6-level configurations,
     compute total index terms across all POIs and report ratio relative
     to the single-level 5-minute baseline (matches Table 4 methodology).
  3. Per-state sub-analysis: top 5 states by count, same metrics, to see
     whether one hierarchy works across regions or whether the choice is
     state-sensitive.

Defends R3 O3 (regional variability) without claiming cross-cultural
breadth, since Yelp coverage is US (+ small CA).

USAGE
-----
1. Download Yelp Open Dataset from https://business.yelp.com/data/resources/open-dataset/
   (academic license; requires email + agreement). Unpack the tar.
2. Run:
       python benchmark_yelp.py /path/to/yelp_academic_dataset_business.json

Output is printed in the same table style as results.md so it can be
pasted directly into the paper.
"""

import argparse
import json
import sys
from collections import Counter, defaultdict


# ── Yelp hours parsing ────────────────────────────────────────────────────────

DAYS = ("Monday", "Tuesday", "Wednesday", "Thursday",
        "Friday", "Saturday", "Sunday")


def parse_hhmm(s: str) -> int:
    """'8:0' or '17:30' → minutes since midnight."""
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def parse_yelp_range(spec: str):
    """'8:0-17:30' → (start_min, end_min) or None on parse failure."""
    try:
        start_s, end_s = spec.split("-")
        start = parse_hhmm(start_s)
        end = parse_hhmm(end_s)
        if end == 0:                        # midnight rollover convention
            end = 24 * 60
        if end <= start:                    # spans midnight; clip to same-day
            end = 24 * 60
        if not (0 <= start < end <= 24 * 60):
            return None
        return (start, end)
    except (ValueError, AttributeError):
        return None


def iter_yelp_ranges(business_json_path: str):
    """Yield (state, [(start_min, end_min), ...]) per business that has hours."""
    with open(business_json_path) as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            hours = rec.get("hours")
            if not hours:
                continue
            ranges = []
            for d in DAYS:
                spec = hours.get(d)
                if spec is None:
                    continue
                r = parse_yelp_range(spec)
                if r is not None:
                    ranges.append(r)
            if ranges:
                yield rec.get("state", "??"), ranges


# ── distribution analysis ─────────────────────────────────────────────────────

def alignment_label(minute: int) -> str:
    if minute == 0:
        return ":00"
    if minute == 30:
        return ":30"
    if minute in (15, 45):
        return ":15/:45"
    return "other"


def start_time_distribution(all_ranges):
    """Return dict like {':00': pct, ':30': pct, ':15/:45': pct, 'other': pct}."""
    c = Counter()
    total = 0
    for ranges in all_ranges:
        for (s, _) in ranges:
            c[alignment_label(s % 60)] += 1
            total += 1
    return {k: 100.0 * v / total for k, v in c.items()}, total


def avg_duration(all_ranges):
    durs = [e - s for ranges in all_ranges for (s, e) in ranges]
    if not durs:
        return 0.0
    return sum(durs) / len(durs)


# ── Timehash key generation (self-contained, level-agnostic) ──────────────────

def cover(start: int, end: int, measures: list) -> int:
    """Recursive hierarchical decomposition: count keys for [start, end) using
    the supplied measures (descending). Mirrors the algorithm in timehash core
    libs. Boundaries that are not aligned to the coarsest level recurse into
    finer measures; if no measure tiles a residual sub-range exactly, the
    residual is counted at the finest measure (one key per finest-block)."""
    if start >= end or not measures:
        return 0
    m = measures[0]
    finer = measures[1:]
    # aligned interior with blocks of size m
    interior_start = ((start + m - 1) // m) * m       # round up to multiple of m
    interior_end   = (end // m) * m                    # round down to multiple of m
    if interior_start >= interior_end:
        # no full m-sized block fits; descend
        if not finer:
            # treat residual as one key per m-sized chunk (rounding outward)
            return ((end - start) + m - 1) // m
        return cover(start, end, finer)
    interior_keys = (interior_end - interior_start) // m
    left  = cover(start, interior_start, finer) if start < interior_start else 0
    right = cover(interior_end, end,        finer) if interior_end < end    else 0
    return interior_keys + left + right


def total_keys(all_ranges, measures: list) -> int:
    return sum(cover(s, e, measures) for ranges in all_ranges for (s, e) in ranges)


def _self_test():
    # Paper canonical example: 11:40 AM–9:00 PM with 5-level hierarchy
    # generates 5 keys: {08113040, 081145, 12, 16, 2020}
    n = cover(11*60+40, 21*60, [240, 60, 15, 5, 1])
    assert n == 5, f"expected 5 for 11:40-21:00 with 5-level, got {n}"
    # Aligned 12:00-16:00 should be 1 key (single 4h block)
    assert cover(12*60, 16*60, [240, 60, 15, 5, 1]) == 1
    # Aligned 12:00-13:00 should be 2 keys (4h refines to 1h, so 1 key)
    assert cover(12*60, 13*60, [240, 60, 15, 5, 1]) == 1
    # Empty range
    assert cover(700, 700, [240, 60, 15, 5, 1]) == 0
    # 5M baseline on a clean 8-hour range = 96 keys
    assert cover(9*60, 17*60, [5]) == 96


# ── hierarchy configurations (mirror Table 4 of paper) ────────────────────────

CONFIGS = [
    ("5M only",                 [5]),
    ("1H, 5M",                  [60, 5]),
    ("1H, 30M, 5M",             [60, 30, 5]),
    ("2H, 1H, 5M",              [120, 60, 5]),
    ("2H, 1H, 30M, 5M",         [120, 60, 30, 5]),
    ("2H, 1H, 30M, 15M, 5M",    [120, 60, 30, 15, 5]),
    ("4H, 1H, 15M, 5M, 1M",     [240, 60, 15, 5, 1]),    # reference 5-level
]


def hierarchy_sweep(all_ranges):
    baseline = total_keys(all_ranges, [5])
    rows = []
    for name, measures in CONFIGS:
        t = total_keys(all_ranges, measures)
        ratio = 100.0 * t / baseline if baseline else 0.0
        rows.append((name, len(measures), t, ratio))
    return rows, baseline


# ── reporting ─────────────────────────────────────────────────────────────────

def print_dist(dist, total, label):
    print(f"\n## Start-time distribution ({label}, n={total:,} day-ranges)")
    print(f"  :00     {dist.get(':00', 0):6.2f}%")
    print(f"  :30     {dist.get(':30', 0):6.2f}%")
    print(f"  :15/:45 {dist.get(':15/:45', 0):6.2f}%")
    print(f"  other   {dist.get('other', 0):6.2f}%")


def print_sweep(rows, baseline, label):
    print(f"\n## Hierarchy optimization sweep ({label})")
    print(f"  baseline (5M only): {baseline:,} keys = 100%")
    print(f"  {'Configuration':<25} {'Depth':>6} {'Keys':>15} {'Ratio':>8}")
    print(f"  {'-'*60}")
    for name, depth, keys, ratio in rows:
        print(f"  {name:<25} {depth:>6} {keys:>15,} {ratio:>7.2f}%")


def print_pretty_summary(rows, label):
    """Compact summary suitable for paper Table comparison."""
    print(f"\n## Compact summary for paper ({label})")
    for name, _, _, ratio in rows:
        print(f"  {name:<25} {ratio:>7.2f}%")


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("business_json", help="path to yelp_academic_dataset_business.json")
    ap.add_argument("--top-states", type=int, default=5,
                    help="run per-state sub-analysis on top N states (default: 5)")
    args = ap.parse_args()

    print(f"Loading {args.business_json} ...")
    by_state = defaultdict(list)
    for state, ranges in iter_yelp_ranges(args.business_json):
        by_state[state].append(ranges)

    all_ranges = [r for v in by_state.values() for r in v]
    print(f"Loaded {sum(len(v) for v in by_state.values()):,} businesses with hours "
          f"across {len(by_state)} states.")

    # global
    dist, total = start_time_distribution(all_ranges)
    print_dist(dist, total, "ALL Yelp")
    print(f"  avg duration: {avg_duration(all_ranges):.1f} minutes")
    rows, baseline = hierarchy_sweep(all_ranges)
    print_sweep(rows, baseline, "ALL Yelp")
    print_pretty_summary(rows, "ALL Yelp")

    # per-state
    top = sorted(by_state.items(), key=lambda kv: -len(kv[1]))[:args.top_states]
    for state, ranges_list in top:
        print(f"\n{'='*60}\nState: {state} (n={len(ranges_list):,} businesses)")
        dist, total = start_time_distribution(ranges_list)
        print_dist(dist, total, state)
        rows, baseline = hierarchy_sweep(ranges_list)
        print_pretty_summary(rows, state)

    # comparison cue
    print("\n## Compare to production distribution (paper Table 4)")
    print("  Production: :00=83.7%, :30=15.5%, :15/:45+other=0.8%")
    print("  Production hierarchy ratio (5-level 2H,1H,30M,15M,5M) = 6.30% of 5M-only baseline")
    print("\nIf Yelp ratio for the same 5-level config is within ~10% of 6.30%,")
    print("the chosen hierarchy is dataset-robust → universality argument.")
    print("If it differs by >50%, write up as evidence for adaptive hierarchy.")


if __name__ == "__main__":
    _self_test()
    sys.exit(main() or 0)
