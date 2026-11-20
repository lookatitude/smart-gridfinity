#!/usr/bin/env python3
"""How large can a grid of 4x3 tiles get from ONE power feed? Same electrical model as
grid_power.py (both rails, 0.1 ohm per connector pair, 88 % step-down converters), solved
directly so many sizes can be tried. Limits checked: lowest tile voltage, and 2 A through
any single connector pin. The feed is wired into its tile, so the feed itself is not
limited by one connector."""
import numpy as np

R_PAIR, R_ENTRY, PIN, ETA = 0.10, 0.05, 2.0, 0.88
TILE_W = {"typical (radio on, a few LEDs)": 0.52, "heavy (radio on, 4 LEDs lit per tile)": 0.875,
          "asleep (radio mostly off)": 0.16}

def solve(w, h, feed, vin, watts, px, py):
    n = w * h; idx = lambda x, y: y * w + x
    edges = []
    for y in range(h):
        for x in range(w):
            if x + 1 < w: edges.append((idx(x, y), idx(x + 1, y), 2 * R_PAIR / px, px))
            if y + 1 < h: edges.append((idx(x, y), idx(x, y + 1), 2 * R_PAIR / py, py))
    G = np.zeros((n, n))
    for a, b, r, _ in edges:
        G[a, a] += 1 / r; G[b, b] += 1 / r; G[a, b] -= 1 / r; G[b, a] -= 1 / r
    f = idx(*feed); G[f, f] += 1 / (2 * R_ENTRY)
    v = np.full(n, float(vin))
    for _ in range(60):
        load = np.full(n, watts / 5) if vin <= 5.5 else watts / ETA / np.maximum(v, 3.0)
        rhs = -load; rhs[f] += vin / (2 * R_ENTRY)
        v_new = np.linalg.solve(G, rhs)
        if np.max(np.abs(v_new - v)) < 1e-6: v = v_new; break
        v = 0.5 * v + 0.5 * v_new
    worst_pin = max(abs(v[a] - v[b]) / r / pairs for a, b, r, pairs in edges) if edges else 0
    return v.min(), worst_pin, load.sum()

def ok(w, h, feed, vin, watts, px, py):
    vmin, pin, _ = solve(w, h, feed, vin, watts, px, py)
    return vmin >= (4.0 if vin <= 5.5 else 6.5) and pin <= PIN

def largest(test, cap):
    """Largest n in 1..cap for which test(n) holds (test is true up to some size, then false)."""
    lo, hi = 1, 2
    while hi <= cap and test(hi): lo, hi = hi, hi * 2
    hi = min(hi, cap + 1)
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if test(mid): lo = mid
        else: hi = mid
    return lo

def longest(vin, watts, pairs, centre):
    """Longest single row of tiles joined on their 3-cell sides (each tile adds 168 mm)."""
    return largest(lambda n: ok(n, 1, ((n // 2) if centre else 0, 0), vin, watts, pairs, 1), 300)

def biggest_square(vin, watts, full):
    px, py = (3, 4) if full else (1, 1)
    return largest(lambda n: ok(n, n, (n // 2, n // 2), vin, watts, px, py), 24)

for name, w in TILE_W.items():
    print(name)
    print("  %-6s | %-40s | %-40s | %s" % ("feed", "single row, fed at one end", "single row, fed in the middle", "square block, fed in the middle"))
    for vin in (5, 12, 20, 24):
        cells = []
        for centre in (False, True):
            a, b = longest(vin, w, 1, centre), longest(vin, w, 3, centre)
            cells.append("%3d tiles %5.1f m (1 pair) / %3d tiles (3 pairs)" % (a, a * 0.168, b))
        s1, s3 = biggest_square(vin, w, False), biggest_square(vin, w, True)
        print("  %-6s | %-40s | %-40s | %dx%d tiles (1 pair), %dx%d (all pairs)" % ("%d V" % vin, cells[0], cells[1], s1, s1, s3, s3))
    print()
