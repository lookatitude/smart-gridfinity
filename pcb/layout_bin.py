#!/usr/bin/env python3
"""Board layout for the passive bin board, written with KiCad's pcbnew scripting.
Round, 28.6 mm. Back: four bare contact rings. Front: the parts, a ground fill and wire
pads for the LED chain and the second-foot ID wire. Vias sit on the diagonals, where the
socket pins (on the axes) never land. Check with: kicad-cli pcb drc bin_board/bin_board.kicad_pcb"""
import os, math, pcbnew
from pcbnew import VECTOR2I, FromMM

HERE = os.path.dirname(os.path.abspath(__file__))
FP = "/usr/share/kicad/footprints"
P = lambda x, y: VECTOR2I(FromMM(x), FromMM(y))
BOARD_D = 28.6

board = pcbnew.BOARD()
nets = {}
def net(name):
    if name not in nets:
        nets[name] = pcbnew.NETINFO_ITEM(board, name); board.Add(nets[name])
    return nets[name]

parts = {}
def place(ref, lib, name, x, y, rot, pinnets, value=""):
    fp = pcbnew.FootprintLoad(lib if os.path.isabs(lib) else os.path.join(FP, lib + ".pretty"), name)
    assert fp, (lib, name)
    fp.SetReference(ref); fp.SetValue(value or name); fp.SetPosition(P(x, y)); fp.SetOrientationDegrees(rot)
    fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
    board.Add(fp)
    for pad in fp.Pads():
        n = pinnets.get(pad.GetNumber())
        if n: pad.SetNet(net(n))
    parts[ref] = fp
    return fp

def pad_xy(ref, num):
    p = parts[ref].FindPadByNumber(num).GetPosition()
    return (pcbnew.ToMM(p.x), pcbnew.ToMM(p.y))

def track(netname, points, width=0.3, layer=pcbnew.F_Cu):
    for a, b in zip(points, points[1:]):
        t = pcbnew.PCB_TRACK(board); t.SetStart(P(*a)); t.SetEnd(P(*b)); t.SetWidth(FromMM(width))
        t.SetLayer(layer); t.SetNet(net(netname)); board.Add(t)

def via(netname, x, y):
    v = pcbnew.PCB_VIA(board); v.SetPosition(P(x, y)); v.SetDrill(FromMM(0.3))
    try: v.SetWidth(pcbnew.F_Cu, FromMM(0.6))
    except TypeError: v.SetWidth(FromMM(0.6))
    v.SetNet(net(netname)); board.Add(v)
    return (x, y)

# outline
edge = pcbnew.PCB_SHAPE(board); edge.SetShape(pcbnew.SHAPE_T_CIRCLE); edge.SetLayer(pcbnew.Edge_Cuts)
edge.SetCenter(P(0, 0)); edge.SetEnd(P(BOARD_D / 2, 0)); edge.SetWidth(FromMM(0.1)); board.Add(edge)

# back: contact rings
place("RING1", os.path.join(HERE, "lib.pretty"), "ContactRings", 0, 0, 0,
      {"1": "ID", "2": "DATA", "3": "VIN", "4": "GND"}, "contact rings")

# front: parts
PADFP = "TestPoint_Pad_2.0x2.0mm"
place("D1", "Diode_SMD", "D_SMA", 3.0, 6.3, 0, {"1": "+5V", "2": "VIN"}, "SS14")
place("C1", "Capacitor_SMD", "C_0805_2012Metric", -3.2, 6.3, 180, {"1": "+5V", "2": "GND"}, "10u")
place("C2", "Capacitor_SMD", "C_0603_1608Metric", -2.0, 8.9, 180, {"1": "+5V", "2": "GND"}, "100n")
place("R1", "Resistor_SMD", "R_0603_1608Metric", -6.6, 3.2, 270, {"1": "DATA", "2": "LED_DIN"}, "100")
place("R2", "Resistor_SMD", "R_0603_1608Metric", -9.4, 4.6, 90, {"1": "LED_DIN", "2": "GND"}, "100k")
place("U1", "Package_SO_J-Lead", "TSOC-6_3.76x3.94mm_P1.27mm", 0, -6.8, 0, {"1": "GND", "2": "ID"}, "DS2431P")
place("J1A", "TestPoint", PADFP, -5.4, 11.0, 0, {"1": "LED_DIN"}, "LED data")
place("J1B", "TestPoint", PADFP, 0.0, 11.6, 0, {"1": "GND"}, "LED gnd")
place("J1C", "TestPoint", PADFP, 5.4, 11.0, 0, {"1": "+5V"}, "LED 5V")
place("TP5", "TestPoint", PADFP, 8.2, -6.0, 0, {"1": "ID"}, "ID foot 2")

# vias from the rings up to the front, on the diagonals
d = lambda r, deg: (round(r * math.cos(math.radians(deg)), 3), round(r * math.sin(math.radians(deg)), 3))
v_id = via("ID", *d(1.95, -45))
v_data = via("DATA", *d(5.4, 135))
v_vin = via("VIN", *d(9.2, 45))
for deg in (45, 135, 225, 315): via("GND", *d(12.9, deg))

# tracks (front)
k, a = pad_xy("D1", "1"), pad_xy("D1", "2")
track("VIN", [a, v_vin], 0.5)
c1, c2 = pad_xy("C1", "1"), pad_xy("C2", "1")
track("+5V", [k, c1], 0.5); track("+5V", [c1, c2], 0.4)
j5 = pad_xy("J1C", "1")
track("+5V", [k, (k[0], 8.9), (j5[0], 8.9), j5], 0.5)
r1a, r1b, r2a = pad_xy("R1", "1"), pad_xy("R1", "2"), pad_xy("R2", "1")
track("DATA", [v_data, r1a])
jd = pad_xy("J1A", "1")
track("LED_DIN", [r1b, r2a]); track("LED_DIN", [r2a, (-8.2, 8.6), jd])
u_io = pad_xy("U1", "2"); tp5 = pad_xy("TP5", "1")
track("ID", [v_id, (-3.3, -3.6), (-3.3, u_io[1]), u_io])
track("ID", [v_id, (6.5, -3.4), tp5])

# ground fill on the front
zone = pcbnew.ZONE(board); zone.SetLayer(pcbnew.F_Cu); zone.SetNet(net("GND"))
zone.SetMinThickness(FromMM(0.25))
outline = zone.Outline(); outline.NewOutline()
for i in range(72):
    x, y = d(BOARD_D / 2 - 0.3, i * 5); outline.Append(FromMM(x), FromMM(y))
board.Add(zone)

if __name__ == "__main__":
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    out = os.path.join(HERE, "bin_board", "bin_board.kicad_pcb")
    pcbnew.SaveBoard(out, board)
    print("wrote", out, "-", len(parts), "footprints,", len(board.GetTracks()), "tracks and vias")
