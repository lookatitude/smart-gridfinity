#!/usr/bin/env python3
"""Volume (mm3) and bounding box of ASCII STL files."""
import sys
def measure(path):
    vol, lo, hi, tri = 0.0, [1e9] * 3, [-1e9] * 3, []
    for line in open(path):
        if "vertex" in line:
            v = [float(x) for x in line.split()[1:4]]
            tri.append(v)
            for i in range(3): lo[i] = min(lo[i], v[i]); hi[i] = max(hi[i], v[i])
            if len(tri) == 3:
                a, b, c = tri; tri = []
                vol += (a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0])
                        + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6
    return abs(vol), lo, hi
if __name__ == "__main__":
    for p in sys.argv[1:]:
        try:
            v, lo, hi = measure(p)
            print("%-28s %10.2f mm3  x %.2f..%.2f  y %.2f..%.2f  z %.2f..%.2f" % (p.split("/")[-1], v, lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
        except Exception as e:
            print("%-28s empty" % p.split("/")[-1])
