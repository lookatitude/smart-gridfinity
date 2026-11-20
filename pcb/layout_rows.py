#!/usr/bin/env python3
"""Board layouts for the two row boards (one long board under every row of cells).
  python3 layout_rows.py strip          -> row_strip/row_strip.kicad_pcb   (2 layers, drawn by hand in this script)
  python3 layout_rows.py main           -> row_main/row_main.kicad_pcb     (4 layers: place, autoroute, finish)
  python3 layout_rows.py main --keep    -> the same, reusing the saved routing row_main/row_main.ses
  python3 layout_rows.py                -> both (main with --keep if a saved routing exists)
Frame (both boards): mm, origin at the centre of the ID pin of the board's first cell, +x along
the row, +y toward the next row, seen from the side the pins stand on. That side is KiCad's
front; KiCad y = -y. Everything except the spring pins is on the back.
The outline, pins, holes and connector positions are fixed by the printed tile: do not change
them here without changing the 3D model. check_rows.py verifies them from the board files."""
import os, re, sys, json, math, subprocess, pcbnew
from pcbnew import VECTOR2I, FromMM, ToMM
import boards
from layout_contact import Layout, P, HERE, FP, HEAD_KEEPOUT

JAVA = "/usr/lib/jvm/java-25-openjdk/bin/java"
JAR = "/usr/lib/freerouting/freerouting-executable.jar"
F, B, IN1, IN2 = pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu
VSCORE_LAYER, VSCORE_NAME = pcbnew.User_1, "V.Score"

# ---- fixed by the tile (board frame) ---------------------------------------------------
PITCH = 42.0
PIN_X = (0.0, 5.4, 9.2, 12.9)             # ID, LED data, +5V, GND
HOLE_X = -3.6
FFC_X = 8.0                               # centre of every flat-cable connector
FFC_MOUTH = 4.4                           # footprint origin to cable mouth
STRIP_OUTLINE = [(-7.5, -10.25), (15, -10.25), (15, -3), (141.5, -3), (141.5, 3), (15, 3), (15, 10.25), (-7.5, 10.25)]
STRIP_SNAPS = (15.5, 57.5, 99.5)
MAIN_OUTLINE = [(-12, -7), (54, -7), (54, -3), (141.5, -3), (141.5, 3), (54, 3), (54, 37.5), (34.5, 37.5),
                (34.5, 23), (17, 23), (17, 10.25), (-12, 10.25)]
MAIN_SNAPS = (57.5, 99.5)
MAIN_HOLE = (48.0, 33.0)
SNAP_GAP = 0.3                            # copper to copper where tracks cross a snap line
SNAP_ZONE = 0.5                           # filled areas stay this far from a snap line

SIG = 0.15                                # signal track
VIA, VIA_DRILL = 0.5, 0.25                # signal via
PVIA, PVIA_DRILL = 0.8, 0.4               # supply via

class Rows(Layout):
    """Layout from layout_contact.py, plus what the row boards need."""
    def __init__(self, name, schematic, layers=2):
        super().__init__(name, schematic)
        self.board.SetCopperLayerCount(layers)
        en = self.board.GetEnabledLayers(); en.AddLayer(VSCORE_LAYER); self.board.SetEnabledLayers(en)
        self.board.SetLayerName(VSCORE_LAYER, VSCORE_NAME)
        self.snaps = ()
    def turned(self, ref, x, y, pad, toward, back=True):
        """Place a part with the rotation that brings the given pad nearest to the point `toward`."""
        best = None
        for rot in (0, 90, 180, 270):
            fp = self.place(ref, x, y, rot, back)
            px, py = self.pad(ref, pad)
            d = math.hypot(px - toward[0], py - toward[1])
            if best is None or d < best[0] - 1e-6: best = (d, rot)
            self.board.Remove(fp)
        return self.place(ref, x, y, best[1], back)
    def ffc(self, ref, mouth_y, toward, expect):
        """Flat-cable connector on the back, centred on FFC_X, its cable mouth on the edge
        y = mouth_y and facing `toward` (+1 or -1). Checks from the pad coordinates that each
        position p = 1..12 (counted from the -x end) carries the net in `expect`."""
        for rot in (0, 180):
            fp = self.place(ref, FFC_X, mouth_y - toward * FFC_MOUTH, rot, back=True)
            mp = [p for p in fp.Pads() if p.GetNumber() == "MP"]
            sig = [p for p in fp.Pads() if p.GetNumber() != "MP"]
            if all((-ToMM(m.GetPosition().y) - -ToMM(sig[0].GetPosition().y)) * toward > 0 for m in mp): break
            self.board.Remove(fp)
        else: raise SystemExit(ref + ": cannot face the mouth that way")
        fab = fp.GetLayer() == B and [g for g in fp.GraphicalItems() if g.GetLayer() == pcbnew.B_Fab and g.GetClass() == "PCB_SHAPE"]
        ys = [-ToMM(v) for g in fab for v in (g.GetStart().y, g.GetEnd().y)]
        mouth = max(ys) if toward > 0 else min(ys)
        assert abs(mouth - mouth_y) < 0.06, (ref, "mouth at", mouth, "wanted", mouth_y)
        for g in list(fp.GraphicalItems()):         # the printed outline runs past the mouth, over the board edge: drop those lines
            bb = g.GetBoundingBox()
            if g.GetLayer() == pcbnew.B_SilkS and g.GetClass() == "PCB_SHAPE" and \
               max(-ToMM(bb.GetTop()) * toward, -ToMM(bb.GetBottom()) * toward) > abs(mouth_y) - 0.3: fp.Remove(g)
        byx = sorted(sig, key=lambda p: p.GetPosition().x)
        assert len(byx) == 12
        pos = {}
        for p, pad in enumerate(byx, 1):
            x, y = ToMM(pad.GetPosition().x), -ToMM(pad.GetPosition().y)
            assert abs(x - (FFC_X + (p - 6.5) * 0.5)) < 1e-3, (ref, p, x)
            assert pad.GetNetname() == (expect[p - 1] or ""), "%s position %d carries %r, wanted %r" % (ref, p, pad.GetNetname(), expect[p - 1])
            pos[p] = (x, y)
        return pos
    def cells(self, first=0):
        """Spring pins and screw holes of the four cells, with the screw-head keep-out."""
        for c in range(4):
            for i, dx in enumerate(PIN_X, 1): self.place("P%d%d" % (c + 1, i), PITCH * c + dx, 0)
            self.place("H%d" % (c + 1), PITCH * c + HOLE_X, 0); self.head_keepout(PITCH * c + HOLE_X, 0)
            want = ("ID%d" % (c + 1), "LED%d" % (c + 1), "+5V", "GND")
            assert [self.parts["P%d%d" % (c + 1, i)].Pads()[0].GetNetname() for i in (1, 2, 3, 4)] == list(want)
    def vscore(self, xs, half=3.0):
        """V-score line across the strip on its own user layer, and a short tick in the front print."""
        self.snaps = tuple(xs)
        for x in xs:
            for layer, a, b, w in ((VSCORE_LAYER, -half, half, 0.1), (pcbnew.F_SilkS, 0.35, 1.0, 0.15), (pcbnew.F_SilkS, -1.0, -0.35, 0.15)):
                s = pcbnew.PCB_SHAPE(self.board); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(layer)
                s.SetStart(P(x, a)); s.SetEnd(P(x, b)); s.SetWidth(FromMM(w)); self.board.Add(s)
    def check_snaps(self):
        """Tracks that cross a snap line are at least SNAP_GAP apart on their layer; no via and
        no filled area within SNAP_ZONE of it."""
        bad = 0
        for xs in self.snaps:
            X = FromMM(xs); cross = {}
            for t in self.board.GetTracks():
                if t.GetClass() == "PCB_VIA":
                    if abs(t.GetPosition().x - X) < FromMM(SNAP_ZONE) + t.GetWidth(F) // 2: bad += 1; print("VIA AT SNAP LINE", xs)
                    continue
                a, b = t.GetStart(), t.GetEnd()
                if min(a.x, b.x) - t.GetWidth() // 2 > X or max(a.x, b.x) + t.GetWidth() // 2 < X: continue
                y = a.y if a.x == b.x else a.y + (b.y - a.y) * (X - a.x) / (b.x - a.x)
                if a.y != b.y: bad += 1; print("TRACK NOT STRAIGHT ACROSS SNAP LINE", xs, t.GetNetname())
                cross.setdefault(t.GetLayer(), []).append((-ToMM(y) - ToMM(t.GetWidth()) / 2, -ToMM(y) + ToMM(t.GetWidth()) / 2, t.GetNetname()))
            for layer, items in cross.items():
                items = sorted(set(items))
                for (a0, a1, an), (b0, b1, bn) in zip(items, items[1:]):
                    if an != bn and b0 - a1 < SNAP_GAP - 1e-6: bad += 1; print("TOO CLOSE AT SNAP LINE", xs, an, bn, round(b0 - a1, 3))
            for z in self.board.Zones():
                if z.GetIsRuleArea(): continue
                bb = z.GetBoundingBox()
                if bb.GetLeft() < X + FromMM(SNAP_ZONE) and bb.GetRight() > X - FromMM(SNAP_ZONE): bad += 1; print("AREA AT SNAP LINE", xs, z.GetNetname())
        return bad
    def keepout(self, name, pts, layers, vias=True):
        z = pcbnew.ZONE(self.board); z.SetIsRuleArea(True); z.SetZoneName(name)
        ls = pcbnew.LSET()
        for l in layers: ls.AddLayer(l)
        z.SetLayerSet(ls)
        z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(vias); z.SetDoNotAllowPads(False)
        z.SetDoNotAllowZoneFills(True); z.SetDoNotAllowFootprints(False)
        o = z.Outline(); o.NewOutline()
        for x, y in pts: o.Append(FromMM(x), FromMM(-y))
        self.board.Add(z); return z
    def write(self, rules, default, classes=()):
        """Project file (design rules, net classes), zone fill, board file."""
        out = write_project(self.name, rules, default, classes)
        bds = self.board.GetDesignSettings()
        bds.m_CopperEdgeClearance = FromMM(rules["min_copper_edge_clearance"]); bds.m_HoleClearance = FromMM(rules["min_hole_clearance"])
        bds.m_MinClearance = FromMM(rules["min_clearance"]); bds.m_TrackMinWidth = FromMM(rules["min_track_width"])
        ns = bds.m_NetSettings; dn = ns.GetDefaultNetclass()
        dn.SetTrackWidth(FromMM(default[0])); dn.SetClearance(FromMM(default[1])); dn.SetViaDiameter(FromMM(default[2])); dn.SetViaDrill(FromMM(default[3]))
        for n, w, cl, vd, vh, nets in classes:
            c = pcbnew.NETCLASS(n); c.SetTrackWidth(FromMM(w)); c.SetClearance(FromMM(cl)); c.SetViaDiameter(FromMM(vd)); c.SetViaDrill(FromMM(vh))
            ns.SetNetclass(n, c)
            for net in nets: ns.SetNetclassPatternAssignment(net, n)
        pcbnew.ZONE_FILLER(self.board).Fill(self.board.Zones())
        pcbnew.SaveBoard(out, self.board)
        return out

def write_project(name, rules, default, classes=()):
    """Design rules and net classes live in the project file, not in the board file."""
    d = os.path.join(HERE, name); os.makedirs(d, exist_ok=True)
    out = os.path.join(d, name + ".kicad_pcb")
    cls = lambda n, w, cl, vd, vh: {"name": n, "clearance": cl, "track_width": w, "via_diameter": vd, "via_drill": vh,
           "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25,
           "bus_width": 12, "wire_width": 6, "line_style": 0, "pcb_color": "rgba(0, 0, 0, 0.000)",
           "schematic_color": "rgba(0, 0, 0, 0.000)", "priority": 2147483647 if n == "Default" else 0}
    pro = {"board": {"design_settings": {"rules": rules}},
           "net_settings": {"classes": [cls("Default", *default)] + [cls(n, w, cl, vd, vh) for n, w, cl, vd, vh, nets in classes],
                            "netclass_patterns": [{"netclass": n, "pattern": net} for n, w, cl, vd, vh, nets in classes for net in nets],
                            "meta": {"version": 4}},
           "meta": {"filename": name + ".kicad_pro", "version": 3}}
    json.dump(pro, open(out.replace(".kicad_pcb", ".kicad_pro"), "w"), indent=2)
    return out

# ---- the strip part shared by both boards ------------------------------------------------
# Along the strip the tracks keep to three patterns (|y| in mm, + side: +5V and the ID lines,
# - side: GND and the LED data lines):
#   past a screw hole and the four pins:  supply at HOLE_Y[0], two signals at 2.395 and 2.705
#   in the free stretch between cells:    supply at FREE_Y[0], signals at 1.53, 2.0, 2.65
# A signal for cell k leaves the front through a via in the free stretch before that cell and
# passes the screw head on the back at |y| = 2.6, just outside the head's keep-out.
SIG_HOLE = (2.395, 2.705, 3.05)           # third value: only beside cell 1 of the strip board, where the board is wide
SIG_FREE = (1.53, 2.0, 2.65)
SIG_OUT = (14.0, 14.2, 14.35)             # where each signal starts to move inward after a cell's GND pin
DROP_X, DROP_Y, BACK_Y = -14.0, 2.5, 2.6

def lane_signal(L, net, side, slot, first, dest, start, pin_dx):
    """One signal from `start` (beside cell `first`, on the front) to the pin of cell `dest`."""
    pts = [start]; y = SIG_HOLE[slot]; j = first
    assert abs(abs(start[1]) - y) < 1e-6
    while True:
        xo = PITCH * j + SIG_OUT[slot]
        pts += [(xo, y), (xo + (y - SIG_FREE[slot]), SIG_FREE[slot])]; y = SIG_FREE[slot]
        if dest == j + 1:
            xv = PITCH * dest + DROP_X
            pts += [(xv - 0.3 - abs(DROP_Y - y), y), (xv - 0.3, DROP_Y), (xv, DROP_Y)]; break
        assert slot < 2
        j += 1; xi = PITCH * j - 9.0 + (0.1 if slot == 0 else 0.0)
        pts += [(xi, y), (xi + (SIG_HOLE[slot] - y), SIG_HOLE[slot])]; y = SIG_HOLE[slot]
    sy = lambda q: [(x, side * abs(yy)) if k else (x, yy) for k, (x, yy) in enumerate(q)]
    L.track(net, sy(pts), SIG, F)
    L.via(net, xv, side * DROP_Y, VIA, VIA_DRILL)
    xp = PITCH * dest + pin_dx
    L.track(net, [(xv, side * DROP_Y), (xv + 0.1, side * BACK_Y), (xp, side * BACK_Y), (xp, 0)], SIG, B)

def lane_supply(L, net, side, layer, width, y_hole, y_free, first, start_x, pin_dx, spur_first):
    """Supply track along the strip from beside cell `first` to the last cell, with a branch
    to that net's pin in every cell."""
    dy = y_hole - y_free
    pts = [(start_x, y_hole)]
    for j in range(first, 4):
        if j < 3:
            pts += [(PITCH * j + 13.6, y_hole), (PITCH * j + 13.6 + dy, y_free),
                    (PITCH * (j + 1) - 8.6, y_free), (PITCH * (j + 1) - 8.6 + dy, y_hole)]
        else: pts.append((PITCH * j + pin_dx, y_hole))
    L.track(net, [(x, side * y) for x, y in pts], width, layer)
    for j in range(first if spur_first else first + 1, 4):
        L.track(net, [(PITCH * j + pin_dx, side * y_hole), (PITCH * j + pin_dx, 0)], width, layer)

# ---- row_strip ---------------------------------------------------------------------------
STRIP_RULES = {"min_clearance": 0.15, "min_track_width": 0.15, "min_silk_clearance": 0.0, "min_through_hole_diameter": 0.25,
               "min_via_diameter": 0.5, "min_via_annular_width": 0.1, "min_copper_edge_clearance": 0.2,
               "min_hole_clearance": 0.25, "min_hole_to_hole": 0.25}

def row_strip():
    L = Rows("row_strip", boards.row_strip, 2)
    L.outline(STRIP_OUTLINE)
    L.cells()
    cable = list(boards.CABLE)
    L.ffc("J_IN", -10.25, -1, cable[:9] + ["EN_THIS", "EN_N1", "EN_N2"])
    L.ffc("J_OUT", 10.25, +1, cable[:9] + ["EN_N1", "EN_N2", None])
    # The switch sits beside the screw hole, clear of the head; its pins run along y.
    UX, UY = -2.4, 7.0
    L.turned("U1", UX, UY, "16", (UX + 2.86, UY - 2.275))
    row = lambda n: UY - 2.275 + 0.65 * ((n - 1) if n <= 8 else (16 - n))        # y of pin n
    lx, rx = UX - 2.8625, UX + 2.8625                                             # pins 1-8, pins 9-16
    for n in range(1, 17):
        px, py = L.pad("U1", str(n)); assert abs(px - (lx if n <= 8 else rx)) < 1e-3 and abs(py - row(n)) < 1e-3, n
    L.turned("C1", 0.2, 3.3, "1", (-1, 3.3))            # +5V pad toward -x
    L.turned("R1", 1.0, -4.95, "2", (1.0, -4))          # +5V pad toward the pins, EN_THIS pad toward the edge
    c5, cg = L.pad("C1", "1"), L.pad("C1", "2")
    r5, re_ = L.pad("R1", "2"), L.pad("R1", "1")
    W = SIG
    # -- cable pass-through, back, between the two rows of connector pads --
    # +5V goes round the LED pin on its -x side, 0.8 mm, both pins of each connector.
    L.track("+5V", [(5.5, -3.9), (5.5, -2.5), (3.4, -2.5), (3.4, 2.5), (5.5, 2.5), (5.5, 3.9)], 0.8, B)
    # GND: both pins 3 and 4 drop to the front, which carries 0.8 mm between the LED and +5V pins;
    # pin 6 runs straight through on the back and is tied to it in the middle.
    for s in (-1, 1):
        L.track("GND", [(6.5, s * 3.9), (6.5, s * 2.6)], 0.8, B); L.via("GND", 6.5, s * 2.6, PVIA, PVIA_DRILL)
    L.track("GND", [(6.5, -2.6), (7.3, -1.8), (7.3, 1.8), (6.5, 2.6)], 0.8, F)
    L.track("GND", [(7.75, -3.9), (7.75, -2.2), (7.3, -1.75), (7.3, 1.75), (7.75, 2.2), (7.75, 3.9)], 0.2, B)
    L.via("GND", 7.3, 0, VIA, VIA_DRILL)
    L.track("LED_BUS", [(7.25, -3.9), (7.25, -2.3), (6.7, -1.75), (6.7, 1.75), (7.25, 2.3), (7.25, 3.9)], W, B)
    L.track("ID_BUS", [(8.25, -3.9), (8.25, -2.2), (7.875, -1.825), (7.875, 1.825), (8.25, 2.2), (8.25, 3.9)], W, B)
    # A0, A1 and the two enables for the rows further on pass between the +5V and GND pins.
    for net, x_in, x_mid, x_out in (("A0", 8.75, 10.525, 8.75), ("A1", 9.25, 10.875, 9.25),
                                    ("EN_N1", 10.25, 11.225, 9.75), ("EN_N2", 10.75, 11.575, 10.25)):
        L.track(net, [(x_in, -3.9), (x_in, -2.3), (x_mid, -2.3 + (x_mid - x_in)), (x_mid, 2.3 - (x_mid - x_out)), (x_out, 2.3), (x_out, 3.9)], W, B)
    # -- to the switch, back, under the rear of the connector bodies --
    L.track("+5V", [(5.5, 4.3), (5.5, 4.91), (1.35, 4.91), (0.9, row(16))], 0.2, B)
    L.track("LED_BUS", [(7.25, 4.3), (7.25, 5.245), (1.55, 5.245), (1.55, row(13)), (rx, row(13))], W, B)
    L.track("A0", [(8.75, 4.3), (8.75, 5.555), (1.85, 5.555), (1.85, row(10)), (rx, row(10))], W, B)
    L.track("A1", [(9.25, 4.3), (9.25, 5.865), (2.15, 5.865), (2.15, row(9)), (rx, row(9))], W, B)
    L.track("ID_BUS", [(8.25, -4.3), (8.25, -4.95), (-6.35, -4.95), (-6.35, row(3)), (lx, row(3))], W, B)       # between R1's pads
    L.track("EN_THIS", [(9.75, -4.3), (9.75, re_[1]), (-6.7, re_[1]), (-6.7, row(6)), (lx, row(6))], W, B)      # through R1's pad
    L.track("+5V", [(3.4, -2.5), (1.8, -2.5), (1.0, -3.3), r5], 0.3, B)
    # -- supply of the switch --
    L.track("+5V", [(-0.1, row(16)), (-0.1, 4.0), (c5[0], 3.5), c5], 0.3, B)
    L.via("GND", 2.6, 3.2, 0.6, 0.3)
    L.track("GND", [(6.5, -2.6), (3.9, -2.6), (3.9, 1.9), (2.6, 3.2)], 0.3, F)
    L.track("GND", [(2.6, 3.2), cg, (cg[0], 2.4), (-1.5, 2.4), (-2.15, 3.05), (-2.15, 9.75), (lx, 9.75), (lx, row(7))], 0.3, B)
    # -- the eight switched lines: a via under the chip each, then on the front --
    under = {"1": -2.9, "2": -3.4, "4": -2.9, "5": -3.95, "15": -0.7, "14": -1.4, "12": -0.7, "11": -1.4}
    v = {}
    for n, vx in under.items():
        net = L.parts["U1"].FindPadByNumber(n).GetNetname()
        L.track(net, [(lx if int(n) <= 8 else rx, row(int(n))), (vx, row(int(n)))], W, B)
        v[net] = L.via(net, vx, row(int(n)), VIA, VIA_DRILL)
    assert set(v) == {"ID1", "ID2", "ID3", "ID4", "LED1", "LED2", "LED3", "LED4"}
    L.track("ID1", [v["ID1"], (0, 0)], W, F)
    L.track("LED1", [v["LED1"], (0.6, 7.325), (0.6, 5.0), (1.2, 4.4), (4.6, 4.4), (4.6, 1.2), (5.4, 0)], W, F)
    # ID lines for cells 2-4: up and over the LED vias, then down to the + side of the pins
    id4 = [v["ID4"], (-2.9, 8.2), (-2.6, 8.5), (5.3, 8.5), (11.405, SIG_HOLE[0])]
    id3 = [v["ID3"], (-3.4, 8.35), (-2.9, 8.85), (5.455, 8.85), (11.6, SIG_HOLE[1])]
    id2 = [v["ID2"], (-3.95, 8.6), (-3.35, 9.2), (5.65, 9.2), (11.8, SIG_HOLE[2])]
    # LED lines for cells 2-4: down between the ID pin and the LED pin to the - side
    led4 = [v["LED4"], (-1.4, 6.675), (0.2, 6.675), (0.2, 4.0), (2.2, 2.0), (2.2, -3.0), (2.5, -3.3), (8.2, -3.3), (9.105, -SIG_HOLE[0])]
    led3 = [v["LED3"], (-0.7, 4.2), (1.8, 1.7), (1.8, -3.35), (2.1, -3.65), (8.6, -3.65), (9.545, -SIG_HOLE[1])]
    led2 = [v["LED2"], (-1.4, 4.2), (1.4, 1.4), (1.4, -3.7), (1.7, -4.0), (9.0, -4.0), (9.95, -SIG_HOLE[2])]
    for side, group in ((1, (("ID4", id4, 3), ("ID3", id3, 2), ("ID2", id2, 1))), (-1, (("LED4", led4, 3), ("LED3", led3, 2), ("LED2", led2, 1)))):
        for slot, (net, pts, dest) in enumerate(group):
            L.track(net, pts, W, F)
            lane_signal(L, net, side, slot, 0, dest, pts[-1], PIN_X[0] if side > 0 else PIN_X[1])
    # -- supply along the strip, front, 0.8 mm --
    L.via("+5V", 5.5, 2.5, PVIA, PVIA_DRILL)
    L.track("+5V", [(5.5, 2.5), (5.5, 3.7), (8.3, 3.7), (9.2, 2.8), (9.2, 0)], 0.8, F)
    lane_supply(L, "+5V", 1, F, 0.8, 1.76, 0.75, 0, 9.2, PIN_X[2], False)
    lane_supply(L, "GND", -1, F, 0.8, 1.76, 0.75, 0, 7.3, PIN_X[3], True)
    L.vscore(STRIP_SNAPS)
    L.text("ROW", -5.6, -8.6, 1.0); L.text("IN", -5.6, -6.9, 0.8); L.text("OUT", -5.6, 3.6, 0.8)
    for c in range(4): L.text(str(c + 1), PITCH * c + 2.7, 0.0, 0.9)
    bad = L.check_snaps()
    out = L.write(STRIP_RULES, (SIG, 0.15, VIA, VIA_DRILL))
    print("row_strip: %d footprints, %d tracks and vias; net mismatches: %d; snap-line faults: %d"
          % (len(L.parts), len(L.board.GetTracks()), L.check_nets(), bad))
    return L


# ---- geometry helper: is there room for a via or a track here? ------------------------------
ALL = "all"
class Room:
    """Everything on the board that new copper must keep away from, in the board frame."""
    def __init__(self, board, outline, edge=0.3):
        self.board, self.outline, self.edge = board, outline, edge
        self.rects, self.segs, self.discs, self.areas = [], [], [], []      # copper pads, tracks, vias and holes, keep-outs
        for fp in board.GetFootprints():
            for p in fp.Pads():
                bb = p.GetBoundingBox(); c = p.GetPosition()
                layers = ALL if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH) else (B if p.IsOnLayer(B) else F)
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    self.discs.append((ToMM(c.x), -ToMM(c.y), ToMM(p.GetDrillSize().x) / 2, None, ToMM(p.GetDrillSize().x) / 2)); continue
                if p.GetShape(pcbnew.F_Cu if layers == ALL else layers) == pcbnew.PAD_SHAPE_CIRCLE:
                    self.discs.append((ToMM(c.x), -ToMM(c.y), ToMM(p.GetSize(F).x) / 2, p.GetNetname(), ToMM(p.GetDrillSize().x) / 2)); continue
                self.rects.append((ToMM(bb.GetLeft()), -ToMM(bb.GetBottom()), ToMM(bb.GetRight()), -ToMM(bb.GetTop()), layers, p.GetNetname()))
        for t in board.GetTracks(): self.add(t)
        for z in board.Zones():
            if not z.GetIsRuleArea(): continue
            o = z.Outline().Outline(0)
            self.areas.append(([(ToMM(o.CPoint(i).x), -ToMM(o.CPoint(i).y)) for i in range(o.PointCount())],
                               [l for l in (F, IN1, IN2, B) if z.IsOnLayer(l)]))
    def add(self, t):
        if t.GetClass() == "PCB_VIA":
            p = t.GetPosition(); self.discs.append((ToMM(p.x), -ToMM(p.y), ToMM(t.GetWidth(F)) / 2, t.GetNetname(), ToMM(t.GetDrill()) / 2))
        else:
            a, b = t.GetStart(), t.GetEnd()
            self.segs.append((ToMM(a.x), -ToMM(a.y), ToMM(b.x), -ToMM(b.y), ToMM(t.GetWidth()) / 2, t.GetLayer(), t.GetNetname()))
    @staticmethod
    def inside(pts, x, y):
        n, c = len(pts), False
        for i in range(n):
            (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
            if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0): c = not c
        return c
    @staticmethod
    def seg_d(px, py, x0, y0, x1, y1):
        dx, dy = x1 - x0, y1 - y0; L = dx * dx + dy * dy
        t = 0 if L == 0 else max(0, min(1, ((px - x0) * dx + (py - y0) * dy) / L))
        return math.hypot(px - (x0 + t * dx), py - (y0 + t * dy))
    def disc(self, x, y, r, layers, net, gap=0.2, drill=0.0):
        """Room for a disc of copper (radius r) on these layers? With a drill, also for its hole."""
        if not self.inside(self.outline, x, y): return False
        n = len(self.outline)
        if min(self.seg_d(x, y, *self.outline[i], *self.outline[(i + 1) % n]) for i in range(n)) < r + self.edge: return False
        for pts, ls in self.areas:
            if any(l in ls for l in layers) and (self.inside(pts, x, y) or
               min(self.seg_d(x, y, *pts[i], *pts[(i + 1) % len(pts)]) for i in range(len(pts))) < r + 0.02): return False
        for x0, y0, x1, y1, l, n_ in self.rects:
            if l != ALL and l not in layers: continue
            d = math.hypot(max(x0 - x, 0, x - x1), max(y0 - y, 0, y - y1))
            if n_ != net and d < r + gap: return False
        for cx, cy, cr, n_, hole in self.discs:
            d = math.hypot(x - cx, y - cy)
            if n_ != net and d < r + cr + (gap if n_ is not None else 0.3): return False
            if drill and hole and d < drill + hole + 0.3: return False
        for x0, y0, x1, y1, hw, l, n_ in self.segs:
            if l in layers and n_ != net and self.seg_d(x, y, x0, y0, x1, y1) < r + hw + gap: return False
        return True
    def line(self, a, b, half, layer, net, gap=0.2):
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 0.06))
        return all(self.disc(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n, half, [layer], net, gap) for k in range(n + 1))

# ---- row_main ----------------------------------------------------------------------------
MAIN_RULES = {"min_clearance": 0.125, "min_track_width": 0.15, "min_silk_clearance": 0.0, "min_through_hole_diameter": 0.2,
              "min_via_diameter": 0.5, "min_via_annular_width": 0.1, "min_copper_edge_clearance": 0.2,
              "min_hole_clearance": 0.25, "min_hole_to_hole": 0.25}
ROUTE_GAP = 0.165                         # the autorouter works with this clearance (its results come out up to 0.02 mm tighter)
def main_classes(gap):
    return (SIG, gap, VIA, VIA_DRILL), (("Supply", 0.3, gap, 0.6, 0.3, ("+5V", "+3V3", "GND")),
                                        ("Power", 0.8, 0.2, PVIA, PVIA_DRILL, ("VIN", "HV", "SW")))
CHECK_GAP = 0.125                         # the rule the finished board is checked with
MAIN_DEFAULT, MAIN_CLASSES = main_classes(CHECK_GAP)
HAND_NETS = ("VIN", "HV", "SW", "BST")     # drawn completely by hand in main_place
HELPER = "router only"                    # name of the keep-outs that exist only while the autorouter runs
MAIN_DIR = os.path.join(HERE, "row_main")
MAIN_PCB = os.path.join(MAIN_DIR, "row_main.kicad_pcb")
MAIN_PLACED = MAIN_PCB.replace(".kicad_pcb", "_placed.kicad_pcb")
MAIN_DSN, MAIN_SES = MAIN_PCB.replace(".kicad_pcb", ".dsn"), MAIN_PCB.replace(".kicad_pcb", ".ses")
MODULE_AT = (26.8, 9.65)                  # antenna end 0.2 mm inside the board edge y = 23
ELECTRONICS_X = 54.0
# Filled ground areas: the part of the board with the electronics, 0.35 mm inside the outline,
# and ending 3.9 mm before the first snap line.
MAIN_FILL = [(-11.65, -6.65), (53.6, -6.65), (53.6, 37.15), (34.85, 37.15), (34.85, 22.65), (17.35, 22.65), (17.35, 9.9), (-11.65, 9.9)]

def main_place():
    """Placement and everything drawn by hand: the supply paths, the converter, the tracks
    along the strip. Saved as row_main_placed.kicad_pcb and exported for the autorouter."""
    L = Rows("row_main", boards.row_main, 4)
    L.board.SetLayerType(IN1, pcbnew.LT_POWER)            # unbroken ground layer, no tracks on it
    L.outline(MAIN_OUTLINE)
    L.cells()
    L.place("H5", *MAIN_HOLE); L.head_keepout(*MAIN_HOLE)
    cable = list(boards.CABLE)
    ffc = L.ffc("J_OUT", 10.25, +1, cable[:7] + ["SEL0", "SEL1", "EN1", "EN2", "EN3"])
    # Radio module: antenna toward +y, its end at the board edge y = 23.
    cx, cy = MODULE_AT
    L.turned("U1", cx, cy, "1", (cx + 8.75, cy + 6.0))
    fab = [g.GetBoundingBox() for g in L.parts["U1"].GraphicalItems() if g.GetLayer() == pcbnew.B_Fab and g.GetClass() == "PCB_SHAPE"]
    top = max(-ToMM(b.GetTop()) for b in fab); left = min(ToMM(b.GetLeft()) for b in fab); right = max(ToMM(b.GetRight()) for b in fab)
    assert abs(top - 22.85) < 0.06 and left > 17.6 and right < 36.0, (top, left, right)
    assert L.pad("U1", "9")[1] < L.pad("U1", "1")[1] and L.pad("U1", "18")[0] < cx          # antenna at the pin-1 end
    # No copper on any layer where the module's footprint asks for none (its drawing on Cmts.User:
    # 28.5 x 11.5 mm at the antenna end). The part of that rectangle past the board edge is air.
    L.keepout("antenna", [(cx - 14.25, cy + 6.85), (cx + 14.25, cy + 6.85), (cx + 14.25, cy + 18.35), (cx - 14.25, cy + 18.35)], (F, IN1, IN2, B))
    # -- 12-24 V in, and the step-down converter, in the order of the current --
    L.place("TP1", 37.2, -5.0, back=True)               # VIN wire pad
    L.place("TP2", 40.4, -5.0, back=True)               # GND wire pad
    L.turned("D1", 32.5, -4.9, "2", (40, -4.9))          # anode (VIN) toward the wire pad
    L.turned("D2", 32.5, -1.3, "1", (20, -1.3))          # surge diode: HV end beside D1's cathode
    L.turned("C2", 27.4, -3.1, "1", (27.4, -9)); L.turned("C3", 25.0, -3.1, "1", (25.0, -9))
    L.turned("U6", 21.5, -4.3, "3", (30, -9))            # IN and EN toward the input capacitors
    L.turned("C1", 20.8, -1.6, "1", (30, -1.6))          # BST pad toward +x
    L.turned("L1", 15.5, -4.0, "1", (30, -4.0))
    L.turned("C4", 10.6, -3.55, "1", (10.6, -9)); L.turned("C5", 8.2, -3.55, "1", (8.2, -9))
    hv = "HV"
    assert L.pad("U6", "3")[0] > 22 and L.pad("U6", "3")[1] < L.pad("U6", "1")[1]
    L.track("VIN", [L.pad("TP1", "1"), (L.pad("D1", "2")[0], -5.0)], 1.5, B)
    L.track(hv, [(L.pad("D1", "1")[0], -4.775), (L.pad("U6", "3")[0], -4.775)], 1.5, B)
    L.track(hv, [(30.5, -4.775), L.pad("D2", "1")], 1.5, B)
    L.track("SW", [L.pad("U6", "5"), (18.0, L.pad("U6", "5")[1])], 0.8, B)
    L.track("SW", [L.pad("C1", "2"), (19.4, -2.2), (18.3, -3.3), (18.3, -3.8)], 0.3, B)
    L.track("BST", [L.pad("U6", "6"), (21.0, -2.7), (L.pad("C1", "1")[0], -2.7), L.pad("C1", "1")], 0.3, B)
    # -- +5V: from the inductor past the two output capacitors, between the ID and LED pins of
    #    cell 1 to the cable connector (back, 1.2 mm; 0.8 mm across the two connector pads) --
    L.track("+5V", [(13.25, -4.5), (2.7, -4.5), (2.7, 2.6), (4.9, 2.6)], 1.2, B)
    L.track("+5V", [(4.9, 2.6), (5.5, 2.6), (5.5, 3.9)], 0.8, B)
    assert ffc[1][0] == 5.25 and ffc[2][0] == 5.75
    # ... and on the second inner layer under the pins to the strip, 1.2 mm, with a branch to the
    # +5V pin of cells 1 and 2 and one to the 3.3 V regulator.
    for x in (3.9, 5.3, 6.7): L.via("+5V", x, -4.5, PVIA, PVIA_DRILL)
    # (along the board edge under cell 2, so that vias fit under the cell switch)
    L.track("+5V", [(3.9, -4.5), (34.0, -4.5), (35.65, -6.15), (51.2, -6.15)], 1.2, IN2); L.track("+5V", [(51.2, -6.15), (51.2, 0)], 1.0, IN2)
    L.track("+5V", [(9.2, -4.5), (9.2, 0)], 1.0, IN2)
    L.track("+5V", [(51.2, 0), (51.2, 1.9)], 1.0, IN2)
    lane_supply(L, "+5V", 1, IN2, 1.0, 1.9, 0.9, 1, 51.2, PIN_X[2], False)
    L.track("GND", [(53.0, -1.9), (PITCH + 12.9, -1.9)], 1.0, IN1)
    lane_supply(L, "GND", -1, IN1, 1.0, 1.9, 0.9, 1, PITCH + 12.9, PIN_X[3], True)
    # 3.3 V regulator beside the module's supply pin
    L.turned("U2", 43.0, 5.0, "5", (30, 9))
    p1, p2, p3 = L.pad("U2", "1"), L.pad("U2", "2"), L.pad("U2", "3")
    L.track("+5V", [(45.8, -6.15), (45.8, 5.0)], 0.6, IN2); L.via("+5V", 45.8, 5.0, PVIA, PVIA_DRILL)
    for p in (p1, p3): L.track("+5V", [(45.8, 5.0), (45.3, p[1]), p], 0.5, B)
    L.via("GND", 43.0, 5.0, VIA, VIA_DRILL); L.track("GND", [p2, (43.0, 5.0)], 0.3, B)
    # 3.3 V from the regulator to the module's supply pin: second inner layer, 0.5 mm
    p5, m1 = L.pad("U2", "5"), L.pad("U1", "1")
    assert p5[0] < 42.5 and m1[0] > cx
    L.via("+3V3", 40.6, p5[1], PVIA, PVIA_DRILL); L.track("+3V3", [p5, (40.6, p5[1])], 0.5, B)
    L.via("+3V3", 37.3, m1[1], PVIA, PVIA_DRILL); L.track("+3V3", [m1, (37.3, m1[1])], 0.5, B)
    L.track("+3V3", [(40.6, p5[1]), (40.6, m1[1] - 1.15), (39.45, m1[1]), (37.3, m1[1])], 0.5, IN2)
    # -- ground pins of the cable connector --
    L.track("GND", [(6.5, 3.9), (6.5, 2.75)], 0.8, B); L.via("GND", 6.5, 2.75, 0.6, 0.3)
    L.track("GND", [(7.75, 3.9), (7.75, 2.6)], 0.25, B); L.via("GND", 7.75, 2.6, VIA, VIA_DRILL)
    # -- the cell switch under cell 2, the row decoder, the neighbour switch --
    L.turned("U3", 46.7, -4.2, "1", (36.7, -7.2)); L.turned("C11", 52.2, -6.0, "1", (40, -6.0))      # LED side of the switch toward the strip
    L.turned("U4", -6.5, 6.5, "1", (-16.5, 3.5))
    L.turned("U5", 44.5, 11.5, "1", (34.5, 8.5))         # below the antenna area, so both rows of pins can be reached
    chans = sorted((p for p in L.parts["U5"].Pads() if re.fullmatch(r"N\d+_SW", p.GetNetname())), key=lambda p: int(p.GetNetname()[1:-3]))
    series = {v["1"]: r for r, (_, _, val, _, v) in L.sch.items() if val == "4k7"}
    for i, p in enumerate(chans):                      # N1 nearest the pins, N16 at the far end
        y = 5.0 + 1.55 * i; n = i + 1
        rref = series["N%d_SW" % n]; tref = next(r for r, q in L.sch.items() if r.startswith("TP") and q[4].get("1") == "N%d" % n)
        L.turned(rref, 50.5, y, "2", (60, y)); L.place(tref, 53.2, y, back=True)
        L.track("N%d" % n, [L.pad(rref, "2"), L.pad(tref, "1")], 0.25, B)
    # programming pads and USB pads on the far edge
    L.turned("J1", 36.6, 36.2, "6", (60, 36.2))
    L.place("TP3", 51.2, 36.2, back=True); L.place("TP4", 52.8, 36.2, back=True)
    # -- the tracks to cells 3 and 4 start at vias beside cell 2's GND pin --
    START = {1: ((49.4, 2.95), (48.6, 3.6)), -1: ((52.4, 2.95), (52.3, 3.75))}        # (inner, outer) via of each side, |y|
    for side, group in ((1, (("ID4", 3), ("ID3", 2))), (-1, (("LED4", 3), ("LED3", 2)))):
        for slot, (net, dest) in enumerate(group):
            vx, vy = START[side][slot]
            L.via(net, vx, side * vy, VIA, VIA_DRILL)
            bend = (52.4, 53.0) if side > 0 else (52.4, 52.8)   # the outer one stays wide of the inner one until both are on the strip
            pts = [(vx, side * vy), (bend[slot], side * vy), (bend[slot] + (vy - SIG_HOLE[slot]), side * SIG_HOLE[slot])]
            if pts[0] == pts[1]: del pts[1]
            L.track(net, pts, SIG, F)
            lane_signal(L, net, side, slot, 1, dest, pts[-1], PIN_X[0] if side > 0 else PIN_X[1])
    # LED data for cells 3 and 4: from the switch straight to their vias, on the back
    l4, l3 = L.pad("U3", "11"), L.pad("U3", "15")
    assert L.parts["U3"].FindPadByNumber("11").GetNetname() == "LED4" and l4[0] > 49 and l3[1] < l4[1]
    L.track("LED4", [l4, (51.9, l4[1]), (52.175, -2.95), (52.4, -2.95)], SIG, B)
    L.track("LED3", [l3, (50.6, l3[1]), (51.0, -5.2), (51.6, -4.6), (52.3, -4.2), (52.3, -3.75)], SIG, B)
    L.vscore(MAIN_SNAPS)
    # -- small parts: packed into free areas near what they belong to --
    taken = []
    def court(fp):
        bb = fp.GetCourtyard(B).BBox()
        if bb.GetWidth() <= 0: bb = fp.Pads()[0].GetBoundingBox(); bb.Inflate(FromMM(0.25))
        return (ToMM(bb.GetLeft()) - 0.02, -ToMM(bb.GetBottom()) - 0.02, ToMM(bb.GetRight()) + 0.02, -ToMM(bb.GetTop()) + 0.02)
    for ref, fp in L.parts.items():
        if fp.GetLayer() == B and ref != "U1": taken.append(court(fp))
    taken += [(cx - 9.85, cy - 7.2, cx + 9.85, cy + 13.4), (cx - 14.3, cy + 6.8, cx + 14.3, cy + 18.4)]       # module body, antenna area
    for t in L.board.GetTracks():                       # hand-drawn copper on the back, and every via
        if t.GetClass() == "PCB_VIA":
            p = t.GetPosition(); r = ToMM(t.GetWidth(F)) / 2 + 0.2
            taken.append((ToMM(p.x) - r, -ToMM(p.y) - r, ToMM(p.x) + r, -ToMM(p.y) + r))
        elif t.GetLayer() == B:
            a, b = t.GetStart(), t.GetEnd(); w = ToMM(t.GetWidth()) / 2 + 0.2
            taken.append((ToMM(min(a.x, b.x)) - w, -ToMM(max(a.y, b.y)) - w, ToMM(max(a.x, b.x)) + w, -ToMM(min(a.y, b.y)) + w))
    for c in range(4):
        for dx in PIN_X: taken.append((PITCH * c + dx - 1.3, -1.3, PITCH * c + dx + 1.3, 1.3))             # solder tails of the pins
        taken.append((PITCH * c + HOLE_X - 2.4, -2.4, PITCH * c + HOLE_X + 2.4, 2.4))                       # screw heads
    taken.append((MAIN_HOLE[0] - 2.4, MAIN_HOLE[1] - 2.4, MAIN_HOLE[0] + 2.4, MAIN_HOLE[1] + 2.4))
    def pack(ref, areas):
        for area in areas:
            for rot in (0, 90):
                fp = L.place(ref, 0, 0, rot, back=True)
                y = area[1]
                while y <= area[3]:
                    x = area[0]
                    while x <= area[2]:
                        fp.SetPosition(P(x, y)); b = court(fp)
                        if b[0] >= area[0] and b[1] >= area[1] and b[2] <= area[2] and b[3] <= area[3] and \
                           all(b[2] <= o[0] or b[0] >= o[2] or b[3] <= o[1] or b[1] >= o[3] for o in taken):
                            taken.append(b); return fp
                        x += 0.25
                    y += 0.25
                L.board.Remove(fp); del L.parts[ref]
        raise SystemExit("no room for %s" % ref)
    tower = (36.8, 2.75, 48.9, 16.3); tower_hi = (41.3, 16.0, 48.9, 30.4); top = (35.0, 28.4, 53.6, 35.3)
    left_hi = (-11.6, 2.7, 1.75, 9.95); left_lo = (-11.6, -6.7, 2.0, -2.7); mid = (14.2, -0.75, 36.0, 2.4)
    near = {"C6": [tower], "C7": [tower], "C8": [tower], "C9": [tower, tower_hi], "R1": [tower, tower_hi], "C10": [tower, tower_hi],
            "R2": [tower, tower_hi, mid], "R3": [tower, tower_hi, mid],
            "R4": [mid, left_lo], "C13": [tower_hi, tower], "C12": [left_hi], "R9": [tower_hi, tower, top], "D5": [tower_hi, tower, top], "R6": [tower_hi, tower, top],
            "R7": [mid, left_lo], "R8": [mid, left_lo], "R5": [mid, left_lo], "D3": [left_lo, left_hi], "D4": [left_lo, left_hi]}
    for ref in L.sch:
        if ref.startswith("#") or ref in L.parts: continue
        pack(ref, near.get(ref, [tower, mid, left_lo, left_hi, top]))
    room = Room(L.board, MAIN_OUTLINE)
    # -- +5V to every part that is not on the hand-drawn copper: a via beside the pad and a
    #    0.4 mm track on the second inner layer to the nearest +5V already there --
    anchors = [(cx_, cy_) for cx_, cy_, cr, n, hole in room.discs if n == "+5V" and hole and cr >= 0.9]
    def sample(x0, y0, x1, y1):
        k = max(1, int(math.hypot(x1 - x0, y1 - y0) / 0.25))
        return [(x0 + (x1 - x0) * i / k, y0 + (y1 - y0) * i / k) for i in range(k + 1)]
    for x0, y0, x1, y1, hw, l, n in room.segs:
        if l == IN2 and n == "+5V": anchors += sample(x0, y0, x1, y1)
    fed, unfed, fed_at = 0, [], []
    for ref, fp in L.parts.items():
        for pad in fp.Pads():
            if pad.GetNetname() != "+5V" or pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD: continue
            bb = pad.GetBoundingBox(); r4 = (ToMM(bb.GetLeft()), -ToMM(bb.GetBottom()), ToMM(bb.GetRight()), -ToMM(bb.GetTop()))
            if any(l == B and n == "+5V" and any(math.hypot(max(r4[0] - qx, 0, qx - r4[2]), max(r4[1] - qy, 0, qy - r4[3])) < hw
                                                  for qx, qy in sample(x0, y0, x1, y1))
                   for x0, y0, x1, y1, hw, l, n in room.segs): continue                 # already on the hand-drawn copper
            px, py = ToMM(pad.GetPosition().x), -ToMM(pad.GetPosition().y); done = False
            for r in (0.9, 1.1, 1.3, 1.5, 1.8, 2.1, 2.5, 3.0):
                for a in range(0, 360, 15):
                    x, y = px + r * math.cos(math.radians(a)), py + r * math.sin(math.radians(a))
                    if not (room.disc(x, y, 0.3, [F, IN1, IN2, B], "+5V", 0.2, 0.15) and room.line((px, py), (x, y), 0.15, B, "+5V")): continue
                    for ax, ay in sorted(anchors, key=lambda q: abs(q[0] - x) + abs(q[1] - y))[:40]:
                        for corner in ((ax, y), (x, ay)):
                            if room.line((x, y), corner, 0.2, IN2, "+5V") and room.line(corner, (ax, ay), 0.2, IN2, "+5V"):
                                L.via("+5V", x, y, 0.6, 0.3); room.discs.append((x, y, 0.3, "+5V", 0.15))
                                L.track("+5V", [(px, py), (x, y)], 0.3, B); room.segs.append((px, py, x, y, 0.15, B, "+5V"))
                                for p0, p1 in (((x, y), corner), (corner, (ax, ay))):
                                    if math.dist(p0, p1) > 0.25:      # (a shorter piece would end inside the track it joins)
                                        L.track("+5V", [p0, p1], 0.4, IN2); room.segs.append((*p0, *p1, 0.2, IN2, "+5V")); anchors += sample(*p0, *p1)
                                done = True; break
                        if done: break
                    if done: break
                if done: break
            if done: fed += 1; fed_at.append((px, py))
            else: unfed.append((ref + "." + pad.GetNumber(), px, py))
    for name, px, py in list(unfed):                    # no room for a via: join a +5V pad beside it that has one
        for qx, qy in sorted(fed_at, key=lambda q: math.hypot(q[0] - px, q[1] - py)):
            if math.hypot(qx - px, qy - py) >= 3.0: break
            for path, w in (([(px, py), (qx, qy)], 0.3), ([(px, py), (qx, py), (qx, qy)], 0.2), ([(px, py), (px, qy), (qx, qy)], 0.2)):
                if all(room.line(p0, p1, w / 2, B, "+5V", 0.16) for p0, p1 in zip(path, path[1:])):
                    L.track("+5V", path, w, B); room.segs += [(*p0, *p1, w / 2, B, "+5V") for p0, p1 in zip(path, path[1:])]
                    unfed.remove((name, px, py)); fed += 1; break
            else: continue
            break
    unfed = [u[0] for u in unfed]
    # -- ground: one unbroken layer, and a via down to it beside every ground pad on the back --
    L.zone("GND", IN1, MAIN_FILL, clearance=0.2)
    made, missed, joined = 0, [], []
    for ref, fp in L.parts.items():
        for pad in fp.Pads():
            if pad.GetNetname() != "GND" or pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD: continue
            px, py = ToMM(pad.GetPosition().x), -ToMM(pad.GetPosition().y)
            big = ToMM(min(pad.GetSize(B).x, pad.GetSize(B).y)) >= 1.7
            if ref == "U1" and pad.GetNumber() == "19": continue                    # the module's ground pad has its own drilled pads
            if any(l == B and n == "GND" and Room.seg_d(px, py, x0, y0, x1, y1) < 0.3 for x0, y0, x1, y1, hw, l, n in room.segs): continue   # already has its via
            spot = None
            for r in ((0.0,) if big else ()) + (0.8, 0.95, 1.1, 1.3, 1.5, 1.8, 2.1, 2.5, 3.0):
                for a in range(0, 360, 15 if r else 360):
                    x, y = px + r * math.cos(math.radians(a)), py + r * math.sin(math.radians(a))
                    if room.disc(x, y, VIA / 2, [F, IN1, IN2, B], "GND", 0.2, VIA_DRILL / 2) and (r == 0 or room.line((px, py), (x, y), 0.125, B, "GND")):
                        spot = (x, y); break
                if spot: break
            if not spot:                                # no room for a via: join the nearest ground pad that has one
                for qx, qy in sorted(joined, key=lambda q: math.hypot(q[0] - px, q[1] - py)):
                    if math.hypot(qx - px, qy - py) < 2.5 and room.line((px, py), (qx, qy), 0.125, B, "GND", 0.16):
                        L.track("GND", [(px, py), (qx, qy)], 0.25, B); room.segs.append((px, py, qx, qy, 0.125, B, "GND")); spot = (qx, qy); break
                if not spot: missed.append(ref + "." + pad.GetNumber())
                continue
            L.via("GND", spot[0], spot[1], VIA, VIA_DRILL); made += 1; joined.append((px, py))
            room.discs.append((spot[0], spot[1], VIA / 2, "GND", VIA_DRILL / 2))
            if spot != (px, py):
                L.track("GND", [(px, py), spot], 0.25, B); room.segs.append((px, py, spot[0], spot[1], 0.125, B, "GND"))
    for t in L.board.GetTracks(): t.SetLocked(True)
    bad = L.check_snaps()
    # Keep-outs that exist only for the autorouter (removed again in main_finish): nothing of its
    # own within 0.3 mm (plus its clearance) of a board edge, nothing on the strip, and no front track where the
    # tracks to cells 3 and 4 begin (so it has to arrive at their vias on another layer;
    # without this it joined them on the strip, 0.6 mm before the first snap line).
    L.keepout(HELPER, [(ELECTRONICS_X, -3.3), (142, -3.3), (142, 3.3), (ELECTRONICS_X, 3.3)], (F, IN1, IN2, B))
    for s_, x0 in ((1, 48.1), (-1, 51.8)): L.keepout(HELPER, [(x0, s_ * 2.2), (ELECTRONICS_X, s_ * 2.2), (ELECTRONICS_X, s_ * 4.3), (x0, s_ * 4.3)], (F,), vias=False)
    n_ = len(MAIN_OUTLINE)
    for i in range(n_):
        (x0, y0), (x1, y1) = MAIN_OUTLINE[i], MAIN_OUTLINE[(i + 1) % n_]
        if max(x0, x1) > ELECTRONICS_X + 1e-6: continue
        d = math.hypot(x1 - x0, y1 - y0); nx, ny = -(y1 - y0) / d, (x1 - x0) / d          # inward (the outline runs anticlockwise)
        L.keepout(HELPER, [(x0 + nx * 0.3, y0 + ny * 0.3), (x1 + nx * 0.3, y1 + ny * 0.3), (x1 - nx * 0.3, y1 - ny * 0.3), (x0 - nx * 0.3, y0 - ny * 0.3)], (F, IN1, IN2, B))

    for z in L.board.Zones():
        if z.GetZoneName() == HELPER: z.SetDoNotAllowZoneFills(False)
    L.write(MAIN_RULES, *main_classes(ROUTE_GAP))
    pcbnew.SaveBoard(MAIN_PLACED, L.board)
    json.dump([_describe(t) for t in L.board.GetTracks()], open(MAIN_HAND, "w"))
    ok = pcbnew.ExportSpecctraDSN(L.board, MAIN_DSN)
    print("row_main placed: %d footprints; +5V pads fed on the inner layer %d, not fed: %s; ground vias %d, ground pads with no room: %s; net mismatches: %d; snap-line faults: %d; exported: %s"
          % (len(L.parts), fed, unfed or "none", made, missed or "none", L.check_nets(), bad, ok))
    return L


def _describe(t):
    via = t.GetClass() == "PCB_VIA"
    ends = tuple(sorted(((t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y))))
    return (via, t.GetNetname(), -1 if via else t.GetLayer(), t.GetWidth(F) if via else t.GetWidth(), ends, t.GetDrill() if via else 0)

def _open_links(pcb):
    """Connections KiCad still finds open: [(net, (x0, y0), (x1, y1))] in the board frame."""
    rpt = pcb.replace(".kicad_pcb", "_tmp.rpt")
    subprocess.run(["kicad-cli", "pcb", "drc", "--severity-all", "-o", rpt, pcb], capture_output=True)
    text = open(rpt).read(); os.unlink(rpt)
    pairs = re.findall(r"\[unconnected_items\][^\n]*\n[^\n]*\n\s+@\(([-\d.]+) mm, ([-\d.]+) mm\): [^\n]*?\[([^\]]+)\][^\n]*\n\s+@\(([-\d.]+) mm, ([-\d.]+) mm\):", text)
    return [(n, (float(x0), -float(y0)), (float(x1), -float(y1))) for x0, y0, n, x1, y1 in pairs]

def main_take(ses, dsn=None):
    """Import one autorouter result onto the board as it is; keep the hand-drawn copper exactly
    as drawn, and fixed. With a dsn name, also export the board for another round."""
    before = list(_hand())
    board = pcbnew.LoadBoard(MAIN_PCB)
    ok = pcbnew.ImportSpecctraSES(board, ses)
    seen, twice = set(), []
    for t in board.GetTracks():
        d = _describe(t)
        if d in seen: twice.append(t)
        seen.add(d)
    for t in twice: board.Remove(t)
    back = 0
    for d in before:
        if d in seen: continue
        via, netname, layer, width, ends, drill = d; back += 1
        if via:
            t = pcbnew.PCB_VIA(board); t.SetPosition(VECTOR2I(*ends[0])); t.SetDrill(drill); t.SetWidth(F, width)
        else:
            t = pcbnew.PCB_TRACK(board); t.SetStart(VECTOR2I(*ends[0])); t.SetEnd(VECTOR2I(*ends[1])); t.SetWidth(width); t.SetLayer(layer)
        t.SetNet(board.FindNet(netname)); board.Add(t)
    fixed = set(before)
    for t in board.GetTracks(): t.SetLocked(_describe(t) in fixed)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(MAIN_PCB, board)
    still = sorted(n for n, a, b in _open_links(MAIN_PCB))
    if dsn: pcbnew.ExportSpecctraDSN(board, dsn)
    print("imported %s: %s; hand-drawn pieces put back: %d; duplicates removed: %d; open: %d %s"
          % (os.path.basename(ses), ok, back, len(twice), len(still), still))
    return min(len(still), 100)

MAIN_HAND = MAIN_PCB.replace(".kicad_pcb", "_hand.json")      # what main_place drew, as _describe() tuples

def _hand():
    tup = lambda x: tuple(tup(i) for i in x) if isinstance(x, list) else x
    return set(tup(d) for d in json.load(open(MAIN_HAND)))

def _drc(pcb):
    rpt = pcb.replace(".kicad_pcb", "_tmp.rpt")
    subprocess.run(["kicad-cli", "pcb", "drc", "--severity-all", "-o", rpt, pcb], capture_output=True)
    text = open(rpt).read(); os.unlink(rpt)
    return text

# The steps after routing each run in a process of their own and work on the saved board:
# pcbnew does not reliably survive a second board, or a fill after removals, in one process.
def finish_clean():
    """Router-only keep-outs off; tracks the router narrowed below the rule widened; vias and
    track ends it left unused (KiCad names them) removed. Returns how many were removed."""
    board = pcbnew.LoadBoard(MAIN_PCB); hand = _hand()
    thin = 0
    for t in board.GetTracks():
        if t.GetClass() == "PCB_TRACK" and t.GetWidth() < FromMM(SIG): t.SetWidth(FromMM(SIG)); thin += 1
    helpers = [z for z in board.Zones() if z.GetIsRuleArea() and z.GetZoneName() == HELPER]
    for z in helpers: board.Remove(z)
    # The converter's nets are drawn completely by hand. The router still lays its own 0.8 mm
    # pieces from pad centre to pad centre on top of that copper; they go again.
    extra = [t for t in board.GetTracks() if t.GetNetname() in HAND_NETS and _describe(t) not in hand]
    for t in extra: board.Remove(t)
    if thin or helpers or extra: pcbnew.SaveBoard(MAIN_PCB, board)
    text = _drc(MAIN_PCB)
    spots = [(FromMM(float(x)), FromMM(float(y)), k) for k, x, y in re.findall(r"\[(via_dangling|track_dangling)\][^\n]*\n[^\n]*\n\s+@\(([-\d.]+) mm, ([-\d.]+) mm\)", text)]
    gone = []
    for t in board.GetTracks():
        for x, y, k in spots:
            near_ = lambda q: abs(q.x - x) < 2000 and abs(q.y - y) < 2000
            if (k == "via_dangling" and t.GetClass() == "PCB_VIA" and near_(t.GetPosition())) or \
               (k == "track_dangling" and t.GetClass() == "PCB_TRACK" and _describe(t) not in hand and (near_(t.GetStart()) or near_(t.GetEnd()))): gone.append(t); break
    for t in gone: board.Remove(t)
    if gone: pcbnew.SaveBoard(MAIN_PCB, board)
    print("  clean: tracks widened to %.2f mm: %d; router pieces on hand-drawn nets removed: %d; unused vias and track ends removed: %d" % (SIG, thin, len(extra), len(gone)))
    return min(len(gone), 100)

def finish_flood():
    """Ground areas on both outer layers of the electronics part."""
    board = pcbnew.LoadBoard(MAIN_PCB)
    old = [z for z in board.Zones() if z.GetZoneName() == "ground"]
    for z in old: board.Remove(z)
    gnd = board.FindNet("GND")
    for layer in (F, B):
        z = pcbnew.ZONE(board); z.SetLayer(layer); z.SetNet(gnd); z.SetMinThickness(FromMM(0.2)); z.SetLocalClearance(FromMM(0.2))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL); z.SetZoneName("ground")
        o = z.Outline(); o.NewOutline()
        for x, y in MAIN_FILL: o.Append(FromMM(x), FromMM(-y))
        board.Add(z)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(MAIN_PCB, board)
    return 0

def finish_repair():
    """Join connections that are still open with a straight track where one is clear.
    Returns how many were added."""
    links = _open_links(MAIN_PCB)
    if not links: return 0
    board = pcbnew.LoadBoard(MAIN_PCB)
    room = Room(board, MAIN_OUTLINE); added = 0
    for net, a, b in links:
        def reach(q):                                   # layers on which there is copper of this net at q
            ls = set()
            for cx, cy, cr, n, hole in room.discs:
                if n == net and math.hypot(q[0] - cx, q[1] - cy) < 0.02: ls |= {F, IN2, B}
            for x0, y0, x1, y1, l, n in room.rects:
                if n == net and x0 <= q[0] <= x1 and y0 <= q[1] <= y1: ls |= ({F, IN2, B} if l == ALL else {l})
            for x0, y0, x1, y1, hw, l, n in room.segs:
                if n == net and Room.seg_d(q[0], q[1], x0, y0, x1, y1) < 0.02: ls.add(l)
            return ls
        for layer in sorted(reach(a) & reach(b) - {IN1}):
            if room.line(a, b, SIG / 2, layer, net, 0.17):
                t = pcbnew.PCB_TRACK(board); t.SetStart(P(*a)); t.SetEnd(P(*b)); t.SetWidth(FromMM(SIG)); t.SetLayer(layer)
                t.SetNet(board.FindNet(net)); board.Add(t); room.segs.append((*a, *b, SIG / 2, layer, net)); added += 1; break
    if added:
        pcbnew.ZONE_FILLER(board).Fill(board.Zones()); pcbnew.SaveBoard(MAIN_PCB, board)
    print("  repair: open %d, straight links added %d" % (len(links), added))
    return min(added, 100)

def finish_report():
    board = pcbnew.LoadBoard(MAIN_PCB); hand = _hand()
    widths, routed = {}, {}
    for t in board.GetTracks():
        if t.GetClass() != "PCB_TRACK": continue
        d = widths if _describe(t) in hand else routed
        d[t.GetNetname()] = min(d.get(t.GetNetname(), 99), ToMM(t.GetWidth()))
    sch = {p[0]: p[4] for p in boards.row_main().parts}
    bad = sum(1 for fp in board.GetFootprints() for pad in fp.Pads()
              if (sch.get(fp.GetReference(), {}).get(pad.GetNumber()) or "") != pad.GetNetname())
    bad += sum(1 for r in sch if not r.startswith("#") and board.FindFootprintByReference(r) is None)
    inner = sum(1 for t in board.GetTracks() if t.GetClass() == "PCB_TRACK" and t.GetLayer() == IN1 and _describe(t) not in hand)
    stray = sum(1 for t in board.GetTracks() if _describe(t) not in hand and max(t.GetStart().x, t.GetEnd().x) > FromMM(ELECTRONICS_X))
    write_project("row_main", MAIN_RULES, MAIN_DEFAULT, MAIN_CLASSES)        # checked with the board's rule, not the router's margin
    still = _open_links(MAIN_PCB)
    print("row_main finished: %d tracks and vias; still open: %d %s; net mismatches: %d; autorouted tracks on the ground layer: %d; autorouted copper on the strip: %d"
          % (len(board.GetTracks()), len(still), sorted(n for n, a, b in still), bad, inner, stray))
    print("  narrowest hand-drawn track, mm:", {n: widths.get(n) for n in ("+5V", "+3V3", "VIN", "HV", "SW", "GND")})
    print("  narrowest autorouted track, mm:", {n: routed.get(n) for n in ("+5V", "+3V3", "GND", "VIN", "HV", "SW")})
    return 1 if still or bad or inner or stray else 0

def main_finish():
    me = [sys.executable, os.path.abspath(__file__)]
    for _ in range(8):
        if subprocess.run(me + ["finish_clean"]).returncode == 0: break
    subprocess.run(me + ["finish_flood"])
    for _ in range(6):
        if subprocess.run(me + ["finish_repair"]).returncode == 0: break
    return subprocess.run(me + ["finish_report"]).returncode

def main_route(keep):
    """place -> autoroute (Freerouting; further rounds while connections stay open) -> finish.
    The router's result differs from run to run and often leaves one or two connections open,
    so the whole thing is tried up to ROUTE_TRIES times and stops at the first board that
    KiCad passes with nothing open. Every import and every finishing step runs in a process
    of its own: pcbnew is not reliable after a second import in the same process."""
    import shutil
    me = [sys.executable, os.path.abspath(__file__)]
    def router(dsn, ses):
        if os.path.exists(ses): os.unlink(ses)
        subprocess.run([JAVA, "-jar", JAR, "-de", dsn, "-do", ses, "-mp", os.environ.get("ROUTE_PASSES", "40"), "-l", "en"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2400)
        assert os.path.exists(ses), "the router wrote no result"
    def verdict():
        text = _drc(MAIN_PCB)
        return sum(int(n) for n in re.findall(r"Found (\d+) (?:DRC violations|unconnected pads)", text))
    more_dsn, more_ses = MAIN_DSN.replace(".dsn", "_more.dsn"), MAIN_SES.replace(".ses", "_more.ses")
    if keep and os.path.exists(MAIN_SES):
        if subprocess.run(me + ["place"]).returncode: raise SystemExit(1)
        subprocess.run(me + ["take", MAIN_SES])
        raise SystemExit(main_finish())
    for attempt in range(1, int(os.environ.get("ROUTE_TRIES", "4")) + 1):
        if subprocess.run(me + ["place"]).returncode: raise SystemExit(1)
        router(MAIN_DSN, MAIN_SES)
        left = subprocess.run(me + ["take", MAIN_SES, more_dsn]).returncode
        for again in range(int(os.environ.get("ROUTE_ROUNDS", "5"))):
            if not left: break
            router(more_dsn, more_ses)
            before, left = left, subprocess.run(me + ["take", more_ses, more_dsn]).returncode
            os.replace(more_ses, MAIN_SES)
            if left >= before: break                    # another round brings nothing; main_finish tries the rest
        if os.path.exists(more_dsn): os.unlink(more_dsn)
        rc = main_finish(); faults = verdict()
        print("attempt %d: KiCad finds %d violations and open connections" % (attempt, faults), flush=True)
        if not faults and not rc: raise SystemExit(0)
    raise SystemExit(1)

if __name__ == "__main__":
    what = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not what: row_strip(); main_route(os.path.exists(MAIN_SES))
    elif what[0] == "strip": row_strip()
    elif what[0] == "main": main_route("--keep" in sys.argv)
    elif what[0] == "place": main_place()
    elif what[0] == "take": raise SystemExit(main_take(*what[1:3]))
    elif what[0] == "finish": raise SystemExit(main_finish())
    elif what[0].startswith("finish_"): raise SystemExit(globals()[what[0]]())
