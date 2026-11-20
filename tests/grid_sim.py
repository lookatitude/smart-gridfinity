#!/usr/bin/env python3
"""Whole-grid scenario. Lays out the full collection on tiles of several sizes, then runs
the position discovery the firmware would run, using only what the hardware can report:
  * tile boards: "my port P touches port Q of tile T" (neighbour pin of each edge connector)
  * tile boards: "my cell N reads ID X" (the ID chip of the bin board standing on that cell)
Bins have no processor. A bin larger than one cell shows the same ID in two cells.
The discovered map is compared with the true layout. The script also works out the feed
voltage at every tile (12 V feed, a step-down converter on each tile), and writes docs/smart/layout.svg."""
import itertools, collections, sys, os
import numpy as np

MAX_CELLS = 16          # per tile
MAX_SIDE = 4            # cells each way: a row board is four cells long, the cable chain reaches four rows
BED_CELLS = 5           # 256 mm bed, 5 mm margin

class Tile:
    def __init__(self, name, x, y, w, h):
        self.name, self.x, self.y, self.w, self.h = name, x, y, w, h
    def cells(self):
        return [(self.x + i, self.y + j) for j in range(self.h) for i in range(self.w)]
    def index(self, gx, gy):               # cell number the address resistor encodes
        return (gy - self.y) * self.w + (gx - self.x)
    def cell_of(self, idx):
        return (idx % self.w, idx // self.w)
    def ports(self):                       # (side, n) -> local cell; E and N are plug sides
        p = {}
        for j in range(self.h): p[("E", j)] = (self.w - 1, j); p[("W", j)] = (0, j)
        for i in range(self.w): p[("N", i)] = (i, self.h - 1); p[("S", i)] = (i, 0)
        return p

class Bin:
    def __init__(self, name, nx, ny, x, y, rot=0, comps=1, units=3, kind="bin", contents=None):
        self.name, self.nx, self.ny, self.x, self.y, self.rot = name, nx, ny, x, y, rot
        self.comps, self.units, self.kind = comps, units, kind
        self.contents = contents or ["" for _ in range(comps)]
    def size(self):
        return (self.nx, self.ny) if self.rot % 2 == 0 else (self.ny, self.nx)
    def foot(self, i, j):                  # global cell under local foot (i, j)
        nx, ny, r = self.nx, self.ny, self.rot % 4
        dx, dy = [(i, j), (ny - 1 - j, i), (nx - 1 - i, ny - 1 - j), (j, nx - 1 - i)][r]
        return (self.x + dx, self.y + dy)
    def cells(self):
        w, h = self.size()
        return [(self.x + i, self.y + j) for j in range(h) for i in range(w)]
    def pads(self):                        # primary foot, and the diagonally opposite one
        a = self.foot(0, 0)
        return [a] if self.nx * self.ny == 1 else [a, self.foot(self.nx - 1, self.ny - 1)]

def build():
    # 12 x 6 cells from tiles of three sizes. Columns 4,3,3,2 and rows 3,3.
    tiles, n = [], 0
    for ry, h in ((0, 3), (3, 3)):
        cx = 0
        for w in (4, 3, 3, 2):
            n += 1
            tiles.append(Tile("T%d" % n, cx, ry, w, h)); cx += w
    paints = ["paint %02d" % k for k in range(1, 49)]
    for k, name in ((3, "cadmium yellow"), (17, "lemon yellow"), (30, "yellow ochre")):
        paints[k] = name
    bins = [Bin("bottles", 4, 3, 0, 0, comps=6, units=8,
                contents=["thinner", "primer white", "primer black", "varnish gloss",
                          "varnish matt", "flow improver"])]
    spots = [(4, 0), (6, 0), (8, 0), (10, 0), (4, 2), (6, 2), (8, 2), (10, 2),
             (0, 4), (2, 4), (4, 4), (6, 4)]
    for k, (x, y) in enumerate(spots):
        bins.append(Bin("paint-%02d" % (k + 1), 2, 2, x, y, rot=k % 4, comps=4, units=5,
                        contents=paints[4 * k: 4 * k + 4]))
    bins.append(Bin("cleaner", 2, 1, 0, 3, comps=2, units=7, contents=["airbrush cleaner"] * 2))
    bins.append(Bin("pens", 2, 1, 2, 3, rot=2, comps=2, units=10, contents=["pens", "brushes"]))
    bins.append(Bin("controller", 1, 1, 11, 5, kind="controller"))
    return tiles, bins

def build_drawers():
    # Drawer row: three 4x3 drawer units on three 4x3 tiles, and a 2x3 tile for the
    # controller and the pen holder. A drawer unit reports exactly like a 4x3 bin.
    tiles = [Tile("D%d" % (k + 1), 4 * k, 0, 4, 3) for k in range(3)] + [Tile("D4", 12, 0, 2, 3)]
    bins = [Bin("drawer-%d" % (k + 1), 4, 3, 4 * k, 0, comps=6, units=13,
                contents=["drawer %d compartment %d" % (k + 1, c + 1) for c in range(6)]) for k in range(3)]
    bins.append(Bin("pens", 2, 1, 12, 0, comps=2, units=10, contents=["pens", "brushes"]))
    bins.append(Bin("controller", 1, 1, 13, 2, kind="controller"))
    return tiles, bins

def physical_checks(tiles, bins):
    cell_tile = {}
    for t in tiles:
        assert t.w * t.h <= MAX_CELLS, "%s has more than %d cells" % (t.name, MAX_CELLS)
        assert max(t.w, t.h) <= MAX_SIDE and min(t.w, t.h) >= 2, "%s is not between 2 and %d cells each way" % (t.name, MAX_SIDE)
        assert max(t.w, t.h) <= BED_CELLS, "%s does not fit the printer bed" % t.name
        for c in t.cells():
            assert c not in cell_tile, "tiles overlap at %s" % (c,)
            cell_tile[c] = t
    used = {}
    for b in bins:
        for c in b.cells():
            assert c in cell_tile, "%s hangs off the grid at %s" % (b.name, c)
            assert c not in used, "%s and %s overlap at %s" % (b.name, used[c], c)
            used[c] = b.name
    return cell_tile, used

def neighbour_reports(tiles, one_per_joint):
    """What the tile boards can sense. With one_per_joint only one connector pair is fitted
    between any two tiles (the lowest-numbered port that faces the other tile)."""
    at = {}
    for t in tiles:
        for (side, n), (i, j) in t.ports().items():
            at[(t.x + i, t.y + j, side)] = (t, side, n)
    reports, seen = [], set()
    for (gx, gy, side), (t, s, n) in sorted(at.items(), key=lambda kv: (kv[1][0].name, kv[1][1], kv[1][2])):
        if side not in ("E", "N"): continue
        other = at.get((gx + 1, gy, "W")) if side == "E" else at.get((gx, gy + 1, "S"))
        if not other or other[0] is t: continue
        key = (t.name, other[0].name)
        if one_per_joint and key in seen: continue
        seen.add(key)
        reports.append((t.name, side, n, other[0].name, other[1], other[2]))
    return reports

def discover_tiles(tiles, reports, start):
    size = {t.name: (t.w, t.h) for t in tiles}
    origin, queue, conflicts = {start: (0, 0)}, collections.deque([start]), 0
    links = collections.defaultdict(list)
    for a, sa, na, b, sb, nb in reports:
        if sa == "E": d = (size[a][0], na - nb)        # b sits to the right of a
        else:         d = (na - nb, size[a][1])        # b sits above a
        links[a].append((b, d)); links[b].append((a, (-d[0], -d[1])))
    while queue:
        a = queue.popleft()
        for b, d in links[a]:
            pos = (origin[a][0] + d[0], origin[a][1] + d[1])
            if b not in origin: origin[b] = pos; queue.append(b)
            elif origin[b] != pos: conflicts += 1
    return origin, conflicts

def id_reports(bins, cell_tile):
    """What the tile boards read: (tile, cell number) -> ID of the bin board on that cell."""
    seen = {}
    for b in bins:
        for c in b.pads():
            seen[(cell_tile[c].name, cell_tile[c].index(*c))] = b.name
    return seen

def locate_bins(seen, tiles, origin):
    by_name = {t.name: t for t in tiles}
    pts = collections.defaultdict(list)
    for (tname, idx), ident in seen.items():
        i, j = by_name[tname].cell_of(idx)
        pts[ident].append((origin[tname][0] + i, origin[tname][1] + j))
    found = {}
    for ident, p in pts.items():
        xs, ys = [q[0] for q in p], [q[1] for q in p]
        found[ident] = (min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)
    return found

FEED_VOLTS = 12.0       # lowest feed voltage of the 12-24 V range: the hardest case
MIN_TILE_VOLTS = 7.0    # a tile's step-down converter needs headroom above its 5 V output

def supply_voltages(tiles, bins, cell_tile, reports, source):
    """Feed voltage at each tile. The power bin feeds the starter tile; every connector pair
    adds 0.1 ohm in each of the two lines. Each tile's converter draws constant power:
    its board plus the LEDs of the bins fed from it (a bin is fed through its first foot)."""
    names = [t.name for t in tiles]; n = len(names); k = {m: i for i, m in enumerate(names)}
    watt = np.full(n, 5 * 0.087 / 0.88)
    for b in bins:
        if b.kind == "controller": continue
        t = cell_tile[b.pads()[0]].name
        watt[k[t]] += 5 * (b.comps * 0.0008 + 0.020 * 0.4) / 0.88      # idle LEDs, some lit
    hub = 5 * 0.087 / 0.88
    g = np.zeros((n, n))
    for a, _, _, b, _, _ in reports:
        c = 1 / 0.2
        g[k[a], k[a]] += c; g[k[b], k[b]] += c; g[k[a], k[b]] -= c; g[k[b], k[a]] -= c
    s = k[source]
    keep = [i for i in range(n) if i != s]
    volts = np.full(n, FEED_VOLTS)
    for _ in range(6):                                # constant-power loads: iterate
        amps = watt / volts
        total = amps.sum() + hub / FEED_VOLTS
        v_start = FEED_VOLTS - total * (0.07 + 2 * 0.05 / 2)    # fuse, two feed pins per pole
        drop = np.zeros(n)
        drop[keep] = np.linalg.solve(g[np.ix_(keep, keep)], amps[keep])
        volts = v_start - drop
    return {m: volts[k[m]] for m in names}, total

def run(one_per_joint, layout=build):
    tiles, bins = layout()
    cell_tile, used = physical_checks(tiles, bins)
    ctrl = next(b for b in bins if b.kind == "controller")
    start = cell_tile[(ctrl.x, ctrl.y)]
    reports = neighbour_reports(tiles, one_per_joint)
    origin, conflicts = discover_tiles(tiles, reports, start.name)
    assert conflicts == 0, "tile reports contradict each other"
    assert len(origin) == len(tiles), "tiles not reached: %s" % (set(t.name for t in tiles) - set(origin))
    shift = (start.x, start.y)
    for t in tiles:
        assert (origin[t.name][0] + shift[0], origin[t.name][1] + shift[1]) == (t.x, t.y), t.name
    found = locate_bins(id_reports(bins, cell_tile), tiles, origin)
    for b in bins:
        fx, fy, fw, fh = found[b.name]
        assert (fx + shift[0], fy + shift[1], fw, fh) == (b.x, b.y) + b.size(), b.name
    volts, amps = supply_voltages(tiles, bins, cell_tile, reports, start.name)
    run.volts, run.amps = volts, amps
    return tiles, bins, cell_tile, used, reports

def svg(tiles, bins, cell_tile, lit, path):
    S, pad = 56, 34
    W, H = 12 * S + 2 * pad, 6 * S + 2 * pad + 20
    Y = lambda gy: pad + (6 - gy) * S          # y grows upward in the grid
    out = ['<svg viewBox="0 0 %d %d" role="img" aria-label="Plan view of the full collection: eight base tiles of three sizes carrying one bottle bin, twelve paint bins, a cleaner bin, a pen holder and the power bin">' % (W, H)]
    for t in tiles:
        out.append('<rect x="%d" y="%d" width="%d" height="%d" rx="6" fill="var(--part-base)" opacity=".22" stroke="var(--part-base)" stroke-width="2"/>'
                   % (pad + t.x * S + 1, Y(t.y + t.h) + 1, t.w * S - 2, t.h * S - 2))
    for b in bins:
        w, h = b.size()
        x, y = pad + b.x * S + 5, Y(b.y + h) + 5
        fill = "var(--ink)" if b.kind == "controller" else "var(--part-bin)"
        out.append('<rect x="%d" y="%d" width="%d" height="%d" rx="5" fill="%s" opacity="%s"/>'
                   % (x, y, w * S - 10, h * S - 10, fill, ".85" if b.kind == "controller" else ".5"))
        cols = {6: 3, 4: 2, 2: 2, 1: 1}[b.comps] if b.kind != "controller" else 0
        if cols:
            rows = b.comps // cols
            if w < h: cols, rows = rows, cols
            for k in range(b.comps):
                cx = x + (k % cols + .5) * (w * S - 10) / cols
                cy = y + (k // cols + .5) * (h * S - 10) / rows
                r = min((w * S - 10) / cols, (h * S - 10) / rows) * .36
                on = (b.name, k) in lit
                out.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" stroke="var(--ink)" stroke-width="%s"/>'
                           % (cx, cy, r, "var(--light)" if on else "var(--surface)", "2.5" if on else "1"))
    for t in tiles:   # tile joints on top, so they stay visible under the bins
        out.append('<rect x="%d" y="%d" width="%d" height="%d" rx="6" fill="none" stroke="var(--ink)" stroke-width="1.5" stroke-dasharray="7 5"/>'
                   % (pad + t.x * S + 1, Y(t.y + t.h) + 1, t.w * S - 2, t.h * S - 2))
    out.append('<text x="%d" y="%d" class="small">12 x 6 cells = 504 x 252 mm, front at the bottom. Dashed lines: tile edges.</text>' % (pad, H - 8))
    out.append('</svg>')
    open(path, "w").write("\n".join(out) + "\n")

if __name__ == "__main__":
    for mode in (False, True):
        tiles, bins, cell_tile, used, reports = run(mode)
        print("%-34s %2d connector pairs -> all %d tiles and %d bins located correctly; 12 V feed: %.2f A, lowest tile voltage %.2f V"
              % ("one connector pair per joint:" if mode else "a connector on every facing edge:",
                 len(reports), len(tiles), len(bins), run.amps, min(run.volts.values())))
        if mode: one_pair_volts = min(run.volts.values())
        assert min(run.volts.values()) >= MIN_TILE_VOLTS, "feed voltage too low at the far tile"
    sizes = collections.Counter("%dx%d" % (t.w, t.h) for t in tiles)
    print("tiles:", ", ".join("%d of %s" % (n, s) for s, n in sorted(sizes.items())),
          "| cells:", sum(t.w * t.h for t in tiles), "| used:", len(used))
    straddle = [b.name for b in bins if len({cell_tile[c].name for c in b.cells()}) > 1]
    print("bins sitting across a tile joint:", ", ".join(straddle))
    four = [b.name for b in bins if len({cell_tile[c].name for c in b.cells()}) == 4]
    print("bins sitting on four tiles at once:", ", ".join(four) or "none")
    lit = {(b.name, k) for b in bins for k, c in enumerate(b.contents) if "yellow" in c}
    print('ask for "yellow" ->', ", ".join("%s compartment %d (%s)" % (n, k + 1,
          next(b for b in bins if b.name == n).contents[k]) for n, k in sorted(lit)))
    comps = sum(b.comps for b in bins if b.kind != "controller")
    print("radios: %d tile boards + 1 hub in the power bin = %d | bin boards: %d | LEDs: %d"
          % (len(tiles), len(tiles) + 1, len(bins) - 1, comps))
    two = [b.name for b in bins if len({cell_tile[c].name for c in b.pads()}) > 1]
    print("bins whose ID chip is read by two tile boards (firmware must avoid collisions):", ", ".join(two) or "none")
    tiles, bins, cell_tile, used, reports = run(True, build_drawers)
    print("drawer row: %d tiles, %d units and bins located correctly with %d connector pairs; %d cells, %d used; 12 V feed: %.2f A, lowest tile voltage %.2f V"
          % (len(tiles), len(bins), len(reports), sum(t.w * t.h for t in tiles), len(used), run.amps, min(run.volts.values())))
    tiles, bins, cell_tile, used, reports = run(True)
    here = os.path.dirname(os.path.abspath(__file__))
    svg(tiles, bins, cell_tile, lit, os.path.join(here, "..", "docs", "smart", "layout.svg"))
    print("PASS")
