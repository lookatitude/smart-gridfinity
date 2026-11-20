#!/usr/bin/env python3
"""ngspice model of power distribution in a large grid (KiCad's simulator is ngspice).
Grid: 12 x 36 cells = 3 x 12 tiles of 4x3. One feed at the middle of a long side.
Every joint between tiles is one magnetic connector pair (0.1 ohm per rail, so both the
supply and the ground wire are modelled). Compares distributing 5 V directly with
distributing a higher voltage and stepping it down to 5 V on every tile."""
import subprocess, tempfile, os, re

W, H = 3, 12
R_PAIR = 0.10      # ohm per rail per connector pair, incl. solder joints and tile wiring
R_ENTRY = 0.15     # ohm per rail: fuse, inlet connector
PIN_LIMIT = 2.0    # A per connector pin
ETA = 0.88         # step-down converter efficiency
LOADS = {          # watts drawn at 5 V by one tile (board + its 12 cells' LEDs)
    "radios asleep, 10 LEDs lit in all": 5 * (0.020 + 12 * 0.0008) + 5 * 0.2 / 36,
    "radios always on, 10 LEDs lit in all": 5 * (0.085 + 12 * 0.0008) + 5 * 0.2 / 36,
    "radios on, 4 LEDs lit on every tile": 5 * (0.085 + 12 * 0.0008 + 4 * 0.020),
}

def run(vin, watts, feed=(0, 6)):
    n = lambda x, y, rail: "%s%d_%d" % (rail, x, y)
    L = ["grid power", "Vin src 0 %g" % vin,
         "Rep src %s %g" % (n(*feed, "p"), R_ENTRY), "Ren 0 %s %g" % (n(*feed, "g"), R_ENTRY)]
    for y in range(H):
        for x in range(W):
            for dx, dy in ((1, 0), (0, 1)):
                if x + dx < W and y + dy < H:
                    for rail in "pg":
                        L.append("R%s%d_%d_%d%d %s %s %g" % (rail, x, y, dx, dy, n(x, y, rail), n(x + dx, y + dy, rail), R_PAIR))
            p, g = n(x, y, "p"), n(x, y, "g")
            if vin <= 5.5:   # no converter: the tile draws a fixed current
                L.append("I%d_%d %s %s %g" % (x, y, p, g, watts / 5))
            else:            # step-down converter: fixed power, so current rises as voltage falls
                L.append("B%d_%d %s %s I = %g / max(v(%s,%s), 4)" % (x, y, p, g, watts / ETA, p, g))
    probes = " ".join("v(%s,%s)" % (n(x, y, "p"), n(x, y, "g")) for y in range(H) for x in range(W))
    L += [".op", ".control", "op", "print i(Vin) " + probes, ".endc", ".end"]
    with tempfile.NamedTemporaryFile("w", suffix=".cir", delete=False) as f:
        f.write("\n".join(L) + "\n"); path = f.name
    out = subprocess.run(["ngspice", "-b", path], capture_output=True, text=True).stdout
    os.unlink(path)
    i = -float(re.search(r"i\(vin\) = ([-+0-9.eE]+)", out).group(1))
    vs = [float(v) for v in re.findall(r"v\(p\d+_\d+,g\d+_\d+\) = ([-+0-9.eE]+)", out)]
    assert len(vs) == W * H
    return i, min(vs)

print("36 tiles of 4x3 (12 x 36 cells), one feed at the middle of a long side, 1 connector pair per joint")
print("%-38s %6s %8s %9s %10s  %s" % ("load", "feed V", "feed A", "feed W", "lowest V", "verdict"))
for name, w in LOADS.items():
    for vin in (5, 12, 20):
        i, vmin = run(vin, w)
        need = 4.0 if vin <= 5.5 else 6.5          # LDO + diode, or converter headroom
        ok = vmin >= need and i <= PIN_LIMIT
        why = "" if ok else ("voltage too low" if vmin < need else "over %g A per pin" % PIN_LIMIT)
        print("%-38s %6g %8.2f %9.1f %10.2f  %s" % (name, vin, i, i * vin, vmin, "ok" if ok else "no: " + why))
