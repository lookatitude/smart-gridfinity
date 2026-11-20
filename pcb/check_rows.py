#!/usr/bin/env python3
"""Mechanical check of the two row boards, read back from the board files (not from the
layout script):  python3 check_rows.py
Prints, in the board frame (mm, origin at the centre of the ID pin of the first cell, +x along
the row, +y toward the next row, seen from the pin side; KiCad y = -y): the outline, every
spring pin, every screw hole, each flat-cable connector's mouth and the net at each position,
the side of every footprint and the tallest part. Exits non-zero if anything differs from the
numbers the printed tile was fit-checked with by more than TOL."""
import os, sys, math, pcbnew
from pcbnew import ToMM, FromMM

HERE = os.path.dirname(os.path.abspath(__file__))
TOL = 0.05
PITCH, PIN_X, HOLE_X = 42.0, (0.0, 5.4, 9.2, 12.9), -3.6
HEAD = 4.2 / 2 + 0.3
CABLE = ("+5V", "+5V", "GND", "GND", "LED_BUS", "GND", "ID_BUS")
SPEC = {
    "row_strip": dict(layers=2,
        outline=[(-7.5, -10.25), (15, -10.25), (15, -3), (141.5, -3), (141.5, 3), (15, 3), (15, 10.25), (-7.5, 10.25)],
        snaps=(15.5, 57.5, 99.5), holes=[(PITCH * c + HOLE_X, 0.0) for c in range(4)], parts_x=15.0, tallest=2.1, supply=0.8,
        connectors={"J_IN": (-10.25, -1, CABLE + ("A0", "A1", "EN_THIS", "EN_N1", "EN_N2")),
                    "J_OUT": (10.25, +1, CABLE + ("A0", "A1", "EN_N1", "EN_N2", ""))}),
    "row_main": dict(layers=4,
        outline=[(-12, -7), (54, -7), (54, -3), (141.5, -3), (141.5, 3), (54, 3), (54, 37.5), (34.5, 37.5), (34.5, 23), (17, 23), (17, 10.25), (-12, 10.25)],
        snaps=(57.5, 99.5), holes=[(PITCH * c + HOLE_X, 0.0) for c in range(4)] + [(48.0, 33.0)], parts_x=54.0, tallest=3.4, supply=1.0,
        connectors={"J_OUT": (10.25, +1, CABLE + ("SEL0", "SEL1", "EN1", "EN2", "EN3"))}),
}
# Heights above the board in mm, by footprint name. Read from the data sheets on 19 Nov 2026 for
# the socket (2.0), the module (3.2 +/- 0.15, so 3.35), the coil (2.8 +/- 0.2) and the converter
# (1.0 max); the rest are as remembered. The limit 3.4 is MAIN_PARTS_H in lib/smart.scad.
HEIGHT = {"Hirose_FH12-12S-0.5SH_1x12-1MP_P0.50mm_Horizontal": 2.0, "ESP32-C3-WROOM-02": 3.35, "L_Bourns_SRP5030T": 3.0,
          "D_SMA": 2.3, "TSSOP-16_4.4x5mm_P0.65mm": 1.2, "TSSOP-24_4.4x7.8mm_P0.65mm": 1.2, "SOT-23": 1.1, "SOT-23-5": 1.3,
          "TSOT-23-6": 1.0, "C_0603_1608Metric": 0.9, "R_0603_1608Metric": 0.55, "C_0805_2012Metric": 1.4, "C_1206_3216Metric": 1.8,
          "WirePad_1.0": 0.0, "WirePad_2.5": 0.0, "WirePads_1x06_P1.5mm": 0.0, "MountHole_M2_HeadBack": 0.0}

fails = []
def need(ok, text):
    if not ok: fails.append(text); print("   FAIL:", text)
    return ok
def near(a, b): return abs(a - b) <= TOL
xy = lambda v: (ToMM(v.x), 0.0 - ToMM(v.y))

def outline(board):
    segs = [(xy(d.GetStart()), xy(d.GetEnd())) for d in board.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]
    pts = [segs[0][0], segs[0][1]]; rest = segs[1:]
    while rest:
        for s in rest:
            for a, b in (s, s[::-1]):
                if math.dist(a, pts[-1]) < 1e-3: pts.append(b); rest.remove(s); break
            else: continue
            break
        else: return None
    return pts[:-1] if math.dist(pts[0], pts[-1]) < 1e-3 else None

def inside(pts, x, y):
    c = False
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0): c = not c
    return c

def check(name):
    spec = SPEC[name]
    board = pcbnew.LoadBoard(os.path.join(HERE, name, name + ".kicad_pcb"))
    print("=" * 30, name, "(%d copper layers)" % board.GetCopperLayerCount())
    need(board.GetCopperLayerCount() == spec["layers"], "copper layers")
    # outline
    pts = outline(board)
    print("outline:", " ".join("(%g, %g)" % p for p in pts) if pts else "NOT CLOSED")
    if need(pts is not None and len(pts) == len(spec["outline"]), "outline: closed, %d corners" % len(spec["outline"])):
        for e in spec["outline"]:
            need(any(near(e[0], p[0]) and near(e[1], p[1]) for p in pts), "outline corner (%g, %g)" % e)
    fps = sorted(board.GetFootprints(), key=lambda f: (f.GetPosition().x, f.GetPosition().y))
    kind = lambda f: str(f.GetFPID().GetLibItemName())
    # spring pins
    print("spring pins (ref, net, x, y, side):")
    pins = [f for f in fps if kind(f) == "SpringPin_MillMax0906"]
    for f in pins:
        x, y = xy(f.GetPosition()); print("   %-4s %-5s %8.3f %7.3f  %s" % (f.GetReference(), f.Pads()[0].GetNetname(), x, y, "front" if f.GetLayer() == pcbnew.F_Cu else "BACK"))
    need(len(pins) == 16, "16 spring pins")
    for c in range(4):
        for dx, net in zip(PIN_X, ("ID%d" % (c + 1), "LED%d" % (c + 1), "+5V", "GND")):
            need(any(near(xy(f.GetPosition())[0], PITCH * c + dx) and near(xy(f.GetPosition())[1], 0) and f.Pads()[0].GetNetname() == net
                     and f.GetLayer() == pcbnew.F_Cu for f in pins), "pin %s at (%g, 0) on the front" % (net, PITCH * c + dx))
    # screw holes and the keep-out under each head
    print("screw holes (ref, x, y, hole, back keep-out radius):")
    holes = [f for f in fps if kind(f) == "MountHole_M2_HeadBack"]
    areas = [z for z in board.Zones() if z.GetIsRuleArea() and z.IsOnLayer(pcbnew.B_Cu) and z.GetDoNotAllowTracks() and z.GetDoNotAllowZoneFills()]
    for f in holes:
        x, y = xy(f.GetPosition()); r = None
        for z in areas:
            bb = z.GetBoundingBox()
            if abs(ToMM(bb.GetCenter().x) - x) < 0.01 and abs(-ToMM(bb.GetCenter().y) - y) < 0.01: r = ToMM(bb.GetWidth()) / 2
        print("   %-3s %8.3f %7.3f  %.2f  %s" % (f.GetReference(), x, y, ToMM(f.Pads()[0].GetDrillSize().x), "%.2f" % r if r else "NONE"))
        need(r is not None and r >= HEAD - TOL, "back keep-out under the screw head at (%g, %g)" % (x, y))
        need(any(near(x, e[0]) and near(y, e[1]) for e in spec["holes"]), "hole at (%g, %g) is one of the planned holes" % (x, y))
    need(len(holes) == len(spec["holes"]), "%d screw holes" % len(spec["holes"]))
    for e in spec["holes"]: need(any(near(xy(f.GetPosition())[0], e[0]) and near(xy(f.GetPosition())[1], e[1]) for f in holes), "hole at (%g, %g)" % e)
    # flat-cable connectors
    for ref, (edge, toward, nets) in spec["connectors"].items():
        f = board.FindFootprintByReference(ref)
        if not need(f is not None, ref + " present"): continue
        fab = [g for g in f.GraphicalItems() if g.GetClass() == "PCB_SHAPE" and g.GetLayer() in (pcbnew.B_Fab, pcbnew.F_Fab)]
        ys = [-ToMM(v) for g in fab for v in (g.GetStart().y, g.GetEnd().y)]
        sig = sorted((p for p in f.Pads() if p.GetNumber() != "MP"), key=lambda p: p.GetPosition().x)
        pad_y = xy(sig[0].GetPosition())[1]
        mouth = max(ys) if max(ys) - pad_y > pad_y - min(ys) else min(ys)
        facing = 1 if mouth > pad_y else -1
        cx = sum(xy(p.GetPosition())[0] for p in sig) / len(sig)
        print("%s: %s, centre x %.3f, cable mouth at y = %.3f facing %sy; pads at y = %.3f" % (ref, "back" if f.GetLayer() == pcbnew.B_Cu else "FRONT", cx, mouth, "+" if facing > 0 else "-", pad_y))
        print("   position:" + "".join("%8d" % p for p in range(1, 13)))
        print("   pad:     " + "".join("%8s" % p.GetNumber() for p in sig))
        print("   x:       " + "".join("%8.2f" % xy(p.GetPosition())[0] for p in sig))
        print("   net:     " + "".join("%8s" % (p.GetNetname() or "-") for p in sig))
        need(near(cx, 8.0), ref + " centred on x = 8"); need(near(mouth, edge) and facing == toward, "%s mouth at y = %g facing %+d" % (ref, edge, toward))
        need(f.GetLayer() == pcbnew.B_Cu, ref + " on the back")
        need(any(near(p[1], edge) for p in pts or []), ref + " mouth on a board edge")
        for p, (pad, net) in enumerate(zip(sig, nets), 1):
            need(pad.GetNetname() == net and near(xy(pad.GetPosition())[0], 8.0 + (p - 6.5) * 0.5), "%s position %d carries %s" % (ref, p, net or "nothing"))
    need(sum(1 for f in fps if kind(f).startswith("Hirose_FH12")) == len(spec["connectors"]), "number of flat-cable connectors")
    # sides, reach along x, heights
    print("footprints (ref, footprint, side, x, y):")
    tallest = (0.0, None); unknown = set()
    for f in sorted(fps, key=lambda f: f.GetReference()):
        x, y = xy(f.GetPosition()); back = f.GetLayer() == pcbnew.B_Cu; k = kind(f)
        if k not in ("SpringPin_MillMax0906", "MountHole_M2_HeadBack") or "-v" in sys.argv:
            print("   %-6s %-52s %-5s %8.3f %8.3f" % (f.GetReference(), k, "back" if back else "front", x, y))
        if k == "SpringPin_MillMax0906": continue
        need(back or k == "MountHole_M2_HeadBack", f.GetReference() + " on the back")
        if k != "MountHole_M2_HeadBack":
            right = max(ToMM(p.GetBoundingBox().GetRight()) for p in f.Pads())
            need(right <= spec["parts_x"] + 1e-6, "%s lies at x <= %g (reaches %.2f)" % (f.GetReference(), spec["parts_x"], right))
        if k in HEIGHT:
            if HEIGHT[k] > tallest[0]: tallest = (HEIGHT[k], f.GetReference() + " " + k)
        else: unknown.add(k)
    print("   (16 spring pins on the front and the screw holes not listed; -v lists them)")
    print("tallest part on the back: %.1f mm (%s); limit %.1f mm. Heights: see the table in this script%s"
          % (tallest[0], tallest[1], spec["tallest"], "; no height known for: " + ", ".join(sorted(unknown)) if unknown else ""))
    need(tallest[0] <= spec["tallest"], "tallest part <= %.1f mm" % spec["tallest"]); need(not unknown, "height known for every footprint")
    # snap lines
    vs = pcbnew.User_1
    lines = sorted(xy(d.GetStart())[0] for d in board.GetDrawings() if d.GetLayer() == vs)
    ticks = sorted(set(round(xy(d.GetStart())[0], 3) for d in board.GetDrawings() if d.GetLayer() == pcbnew.F_SilkS and d.GetClass() == "PCB_SHAPE"))
    print("snap lines on layer '%s' at x = %s; front print ticks at x = %s" % (board.GetLayerName(vs), lines, ticks))
    need(len(lines) == len(spec["snaps"]) and all(near(a, b) for a, b in zip(lines, spec["snaps"])), "V-score lines at %s" % (spec["snaps"],))
    need(all(any(near(t, s) for t in ticks) for s in spec["snaps"]), "print tick at every snap line")
    for s in spec["snaps"]:
        X = FromMM(s); cross = {}
        for t in board.GetTracks():
            if t.GetClass() == "PCB_VIA":
                need(abs(t.GetPosition().x - X) >= FromMM(0.5) + t.GetWidth(pcbnew.F_Cu) // 2, "no via within 0.5 mm of the snap line x = %g" % s); continue
            a, b = t.GetStart(), t.GetEnd()
            if min(a.x, b.x) - t.GetWidth() // 2 > X or max(a.x, b.x) + t.GetWidth() // 2 < X: continue
            y = -ToMM(a.y + (b.y - a.y) * ((X - a.x) / (b.x - a.x) if b.x != a.x else 0)); w = ToMM(t.GetWidth()) / 2
            cross.setdefault(board.GetLayerName(t.GetLayer()), []).append((y - w, y + w, t.GetNetname()))
        gaps = []
        for layer, items in cross.items():
            items.sort()
            gaps += [b[0] - a[1] for a, b in zip(items, items[1:])]
        print("   x = %5.1f: %s; smallest gap on a layer %s mm" % (s, "; ".join("%s: %s" % (l, " ".join(n for _, _, n in sorted(i))) for l, i in sorted(cross.items())),
              "%.3f" % min(gaps) if gaps else "-"))
        need(not gaps or min(gaps) >= 0.3 - 1e-6, "tracks at least 0.3 mm apart at the snap line x = %g" % s)
        for z in board.Zones():
            if z.GetIsRuleArea(): continue
            bb = z.GetBoundingBox()
            need(not (bb.GetLeft() < X + FromMM(0.5) and bb.GetRight() > X - FromMM(0.5)), "no filled area within 0.5 mm of the snap line x = %g" % s)
    # supply along the strip
    for net in ("+5V", "GND"):
        ws = [ToMM(t.GetWidth()) for t in board.GetTracks() if t.GetClass() == "PCB_TRACK" and t.GetNetname() == net
              and max(t.GetStart().x, t.GetEnd().x) > FromMM(spec["parts_x"])]
        print("%s along the strip (x > %g): %d track pieces, narrowest %.2f mm" % (net, spec["parts_x"], len(ws), min(ws) if ws else 0))
        need(ws and min(ws) >= spec["supply"] - 1e-6, "%s at least %.1f mm wide along the strip" % (net, spec["supply"]))
    # the module's antenna
    for f in fps:
        if kind(f) != "ESP32-C3-WROOM-02": continue
        fab = [g.GetBoundingBox() for g in f.GraphicalItems() if g.GetClass() == "PCB_SHAPE" and g.GetLayer() == pcbnew.B_Fab]
        x0, x1 = min(ToMM(b.GetLeft()) for b in fab), max(ToMM(b.GetRight()) for b in fab)
        y0, y1 = min(-ToMM(b.GetBottom()) for b in fab), max(-ToMM(b.GetTop()) for b in fab)
        p1, p9 = xy(f.FindPadByNumber("1").GetPosition()), xy(f.FindPadByNumber("9").GetPosition())
        ant = "+y" if p1[1] > p9[1] + 1 else "-y" if p1[1] < p9[1] - 1 else "+x" if p1[0] > p9[0] else "-x"
        cx, cy = xy(f.GetPosition())
        ko = (cx - 14.25, cy + 6.85, cx + 14.25, cy + 18.35) if ant == "+y" else None
        print("radio module: body x %.2f..%.2f, y %.2f..%.2f, antenna toward %s; copper-free rectangle x %.2f..%.2f, y %.2f..%.2f (the part on the board)"
              % ((x0, x1, y0, y1, ant) + ((ko[0], ko[2], ko[1], ko[3]) if ko else (0, 0, 0, 0))))
        if not need(ko is not None, "antenna toward +y"): continue
        need(any(near(p[1], 23.0) for p in pts or []) and 0 <= 23.0 - y1 <= 0.5, "antenna end within 0.5 mm of the board edge y = 23")
        hits = 0
        for t in board.GetTracks():
            if t.GetClass() == "PCB_VIA": qs = [xy(t.GetPosition())]; r = ToMM(t.GetWidth(pcbnew.F_Cu)) / 2
            else:
                a, b = xy(t.GetStart()), xy(t.GetEnd()); r = ToMM(t.GetWidth()) / 2; k = max(1, int(math.dist(a, b) / 0.2))
                qs = [(a[0] + (b[0] - a[0]) * i / k, a[1] + (b[1] - a[1]) * i / k) for i in range(k + 1)]
            if any(ko[0] - r < x < ko[2] + r and ko[1] - r < y < ko[3] + r and pts and inside(pts, x, y) for x, y in qs): hits += 1
        for z in board.Zones():
            if z.GetIsRuleArea(): continue
            for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
                if not z.IsOnLayer(l): continue
                gx = ko[0] + 0.25
                while gx < ko[2]:
                    gy = ko[1] + 0.25
                    while gy < ko[3]:
                        if pts and inside(pts, gx, gy) and z.HitTestFilledArea(l, pcbnew.VECTOR2I(FromMM(gx), FromMM(-gy)), 0): hits += 1
                        gy += 0.5
                    gx += 0.5
        for g in fps:
            for p in g.Pads():
                x, y = xy(p.GetPosition())
                if ko[0] < x < ko[2] and ko[1] < y < ko[3]: hits += 1
        print("   copper found in that rectangle (tracks, vias, pads, filled areas sampled every 0.5 mm): %d" % hits)
        need(hits == 0, "no copper in the antenna rectangle")

if __name__ == "__main__":
    for name in SPEC: check(name)
    print("=" * 30)
    print("RESULT: %s" % ("all positions match the brief within %.2f mm" % TOL if not fails else "%d FAILURES" % len(fails)))
    for f in fails: print("   ", f)
    sys.exit(1 if fails else 0)
