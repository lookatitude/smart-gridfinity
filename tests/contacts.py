#!/usr/bin/env python3
"""Contact geometry check for the four-ring bin board. The four socket pins sit in a row
from the cell centre; the bin board has concentric rings, so rotation does not matter.
How far can the foot be off-centre before a pin leaves its ring or touches the next one?
Also checks that the board clears the magnets. Dimensions mirror lib/smart.scad."""
import math

NAMES = ["ID", "LED data", "5V", "ground"]
PIN_R = [0.0, 5.4, 9.2, 12.9]
RINGS = [(0.0, 2.6), (4.4, 6.4), (8.2, 10.2), (12.0, 13.8)]
TIP_R = 0.75                     # radius of the pin's contact face (assumed)
BOARD_D, BOARD_FIT = 28.6, 0.2
MAGNET_OFFSET, MAGNET_D = 13.0, 6.5

def touched(r):
    return {n for n, (a, b) in zip(NAMES, RINGS) if r + TIP_R > a and r - TIP_R < b}

def problems(offset):
    out = []
    for k in range(72):
        ox, oy = offset * math.cos(k * math.pi / 36), offset * math.sin(k * math.pi / 36)
        for pr, name in zip(PIN_R, NAMES):
            t = touched(math.hypot(pr - ox, oy))
            if name not in t: out.append((name, "no contact"))
            if t - {name}: out.append((name, "also touches %s" % sorted(t - {name})))
    return out

ok = 0.0
for off10 in range(0, 41):
    p = problems(off10 / 10)
    if p:
        print("first problem at %.1f mm off-centre: %s %s" % (off10 / 10, p[0][0], p[0][1])); break
    ok = off10 / 10
play = ((42 - 2 * 2.15) - (41.5 - 2 * 2.95)) / 2
print("every pin on its own ring, and only that ring, up to %.1f mm off-centre" % ok)
print("foot play in the socket at pin height: +/- %.2f mm -> margin %.1fx" % (play, ok / play))
assert ok >= 1.5 * play, "ring layout has too little margin"

assert RINGS[-1][1] + 0.3 <= BOARD_D / 2 + 1e-9, "ground ring too close to the board edge"
wall = math.hypot(MAGNET_OFFSET, MAGNET_OFFSET) - MAGNET_D / 2 - (BOARD_D / 2 + BOARD_FIT)
print("plastic between the board recess and each magnet pocket: %.2f mm" % wall)
assert wall >= 0.5, "bin board too close to the magnets"
gaps = [RINGS[i + 1][0] - RINGS[i][1] for i in range(3)]
print("gap between rings: %s mm; pin tip %.1f mm across cannot bridge one" % (gaps, 2 * TIP_R))
assert min(gaps) > 2 * TIP_R
print("PASS")
