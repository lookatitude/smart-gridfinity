#!/usr/bin/env python3
"""Board layout for the power bin board: DC input, fuse, feed contacts, and the hub radio.
  python3 layout_power.py place    -> power_board/power_board.kicad_pcb (unrouted) and .dsn
  python3 layout_power.py route    -> Freerouting, import, ground fill on both sides
34 x 38 mm, four layers, to lie flat in a 1x1 bin. Wires solder to flat pads."""
import os, re, sys, json, subprocess, pcbnew
from pcbnew import VECTOR2I, FromMM, ToMM
import boards
import layout_kit as kit       # shared ground and repair steps

HERE = os.path.dirname(os.path.abspath(__file__))
FP = "/usr/share/kicad/footprints"
OUT = os.path.join(HERE, "power_board", "power_board.kicad_pcb")
DSN, SES = OUT.replace(".kicad_pcb", ".dsn"), OUT.replace(".kicad_pcb", ".ses")
JAVA = "/usr/lib/jvm/java-25-openjdk/bin/java"
JAR = "/usr/lib/freerouting/freerouting-executable.jar"
W, H = 34.0, 38.0
EDGE = 0.5
P = lambda x, y: VECTOR2I(FromMM(x), FromMM(y))
POWER_NETS = ("DC_IN", "VIN", "HV", "SW", "+5V", "GND")
SWAP = {"Diode_SMD:D_SMA": "Diode_SMD:D_SOD-123F",
        "Inductor_SMD:L_Bourns_SRP5030T": "Inductor_SMD:L_APV_ANR4030",
        "Capacitor_SMD:C_1206_3216Metric": "Capacitor_SMD:C_0805_2012Metric"}

GROUND_OUTLINE = ((0.4, 0.4), (W - 0.4, 0.4), (W - 0.4, H - 0.4), (0.4, H - 0.4))
def inside(b): return b[0] >= EDGE and b[1] >= EDGE and b[2] <= W - EDGE and b[3] <= H - EDGE
# point the shared steps at this board
kit.inside, kit.GROUND_OUTLINE, kit.OUT, kit.SCHEMATIC = inside, GROUND_OUTLINE, OUT, boards.power_board

def build():
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(4)                       # same recipe as the first-row board:
    board.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)  # one inner layer is the ground plane
    ns = board.GetDesignSettings().m_NetSettings
    d = ns.GetDefaultNetclass()
    d.SetTrackWidth(FromMM(0.25)); d.SetClearance(FromMM(0.15)); d.SetViaDiameter(FromMM(0.6)); d.SetViaDrill(FromMM(0.3))
    pw = pcbnew.NETCLASS("Power")
    pw.SetTrackWidth(FromMM(0.5)); pw.SetClearance(FromMM(0.15)); pw.SetViaDiameter(FromMM(0.8)); pw.SetViaDrill(FromMM(0.4))
    ns.SetNetclass("Power", pw)
    for n in POWER_NETS: ns.SetNetclassPatternAssignment(n, "Power")
    nets = {}
    def net(name):
        if name not in nets:
            nets[name] = pcbnew.NETINFO_ITEM(board, name); board.Add(nets[name])
        return nets[name]
    placed = []
    def add(ref, fpname, value, pinnets, x, y, rot=0):
        lib, name = SWAP.get(fpname, fpname).split(":")
        libdir = os.path.join(HERE, "lib.pretty") if lib == "lib" else os.path.join(FP, lib + ".pretty")
        fp = pcbnew.FootprintLoad(libdir, name); assert fp, fpname
        fp.SetReference(ref); fp.SetValue(value); fp.SetPosition(P(x, y)); fp.SetOrientationDegrees(rot)
        fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
        board.Add(fp)
        for pad in fp.Pads():
            n = pinnets.get(pad.GetNumber())
            if n: pad.SetNet(net(n))
        return fp
    def box(fp):
        if "WirePad" in fp.GetFPIDAsString(): bb = fp.Pads()[0].GetBoundingBox(); m = 0.25
        else: bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox(); m = 0.05
        return (ToMM(bb.GetLeft()) - m, ToMM(bb.GetTop()) - m, ToMM(bb.GetRight()) + m, ToMM(bb.GetBottom()) + m)
    def free(b):
        return b[0] >= EDGE and b[1] >= EDGE and b[2] <= W - EDGE and b[3] <= H - EDGE and \
               all(b[2] <= o[0] or b[0] >= o[2] or b[3] <= o[1] or b[1] >= o[3] for o in placed)
    def fixed(*a, **k):
        fp = add(*a, **k); b = box(fp); assert free(b), (a[0], b); placed.append(b); return fp
    def pack(ref, fpname, value, pinnets, areas):
        for rot in (0, 90):
            fp = add(ref, fpname, value, pinnets, 0, 0, rot)
            for area in areas:
                y = area[1]
                while y <= area[3]:
                    x = area[0]
                    while x <= area[2]:
                        fp.SetPosition(P(x, y)); b = box(fp)
                        if free(b) and b[0] >= area[0] - 0.1 and b[1] >= area[1] - 0.1 and b[2] <= area[2] + 0.1 and b[3] <= area[3] + 0.1:
                            placed.append(b); return fp
                        x += 0.25
                    y += 0.25
            board.Remove(fp)
        raise SystemExit("no room for %s (%s)" % (ref, value))

    sch = boards.power_board().parts
    by_ref = {p[0]: p for p in sch}
    for a, b in (((0, 0), (W, 0)), ((W, 0), (W, H)), ((W, H), (0, H)), ((0, H), (0, 0))):
        s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
        s.SetStart(P(*a)); s.SetEnd(P(*b)); s.SetWidth(FromMM(0.1)); board.Add(s)

    # Radio module at the top, antenna toward the top edge. Its courtyard is T-shaped.
    cx, cy = 17.0, 19.0
    add("U1", by_ref["U1"][3], "ESP32-C3-WROOM-02", by_ref["U1"][4], cx, cy)
    placed.append((cx - 14.3, cy - 18.4, cx + 14.3, cy - 6.9))      # antenna zone
    placed.append((cx - 9.8, cy - 6.9, cx + 9.8, cy + 7.2))          # body

    # Wire pads. Feed contacts and DC input are large, on the bottom edge.
    BIG, PAD = "lib:WirePad_2.5", "lib:WirePad_1.0"
    for i, (ref, n) in enumerate((("DC+", "DC_IN"), ("DC-", "GND"), ("FEED+1", "VIN"), ("FEED+2", "VIN"), ("FEED-1", "GND"), ("FEED-2", "GND"))):
        fixed(ref, BIG, n, {"1": n}, 3.2 + 5.5 * i, 35.6)
    for i, n in enumerate(("+3V3", "GND", "TXD", "RXD", "EN", "BOOT")):
        fixed("PG%d" % (i + 1), PAD, n, {"1": n}, 1.6, 13.6 + 1.6 * i)
    for i, n in enumerate(("USB_DN", "USB_DP")):
        fixed("USB%d" % (i + 1), PAD, n, {"1": n}, 32.4, 13.6 + 1.6 * i)

    power = (0.5, 26.3, 33.5, 33.6)
    sides = [(3.0, 12.2, 7.0, 26.0), (27.0, 12.2, 31.2, 26.0), power]
    for ref, lib_id, value, fpname, pn in sch:
        if ref in ("U1", "J1", "J2") or ref.startswith("#") or ref.startswith("TP") or not fpname: continue
        nsn = set(v for v in pn.values() if v)
        if nsn & {"HV", "SW", "BST", "VIN", "DC_IN"} or ref in ("U2", "U6", "L1"):
            pack(ref, fpname, value, pn, [power] + sides[:2])
        else:
            pack(ref, fpname, value, pn, sides)
    print(kit.pre_ground(board, net("GND")))
    return board

def check_nets(board):
    sch = {p[0]: p[4] for p in boards.power_board().parts}
    bad = 0
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref in sch and not ref.startswith("TP"):
            for pad in fp.Pads():
                if (sch[ref].get(pad.GetNumber()) or "") != pad.GetNetname(): bad += 1; print("MISMATCH", ref, pad.GetNumber())
    return bad

def write_project():
    cls = lambda name, w, vd, vh: {"name": name, "clearance": 0.15, "track_width": w, "via_diameter": vd, "via_drill": vh,
                                   "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.2,
                                   "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25, "bus_width": 12, "wire_width": 6,
                                   "line_style": 0, "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)",
                                   "priority": 2147483647 if name == "Default" else 0}
    pro = {"board": {"design_settings": {"rules": {
               "min_clearance": 0.15, "min_track_width": 0.1, "min_through_hole_diameter": 0.2, "min_via_diameter": 0.5,
               "min_via_annular_width": 0.1, "min_copper_edge_clearance": 0.25, "min_hole_clearance": 0.25,
               "min_hole_to_hole": 0.25}}},
           "net_settings": {"classes": [cls("Default", 0.25, 0.6, 0.3), cls("Power", 0.5, 0.8, 0.4)],
                            "netclass_patterns": [{"netclass": "Power", "pattern": n} for n in POWER_NETS],
                            "meta": {"version": 4}},
           "meta": {"filename": "power_board.kicad_pro", "version": 3}}
    json.dump(pro, open(OUT.replace(".kicad_pcb", ".kicad_pro"), "w"), indent=2)

if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "place"
    if step == "place":
        board = build()
        pcbnew.SaveBoard(OUT, board)
        ok = pcbnew.ExportSpecctraDSN(board, DSN)
        write_project()
        print("placed %d footprints on %g x %g mm; net mismatches: %d; exported for routing: %s"
              % (len(board.GetFootprints()), W, H, check_nets(board), ok))
    elif step == "route":
        if "--keep" not in sys.argv or not os.path.exists(SES):
            if os.path.exists(SES): os.unlink(SES)
            subprocess.run([JAVA, "-jar", JAR, "-de", DSN, "-do", SES, "-mp", os.environ.get("ROUTE_PASSES", "100"), "-l", "en"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1500)
        board = pcbnew.LoadBoard(OUT)
        assert os.path.exists(SES), "the router wrote no result"
        ok = pcbnew.ImportSpecctraSES(board, SES)
        print("ground:", kit.ground(board, escape=False))
        pcbnew.SaveBoard(OUT, board)
        print("straggler links added:", kit.repair(board))
        print("imported routing: %s; %d tracks and vias; net mismatches: %d" % (ok, len(board.GetTracks()), check_nets(board)))
