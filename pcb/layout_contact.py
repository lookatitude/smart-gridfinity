#!/usr/bin/env python3
"""Board layout for the feed contact board, and the Layout helper the row boards also use.
Placed and routed by hand in this script (straight tracks, vias and filled areas); no autorouter.
  python3 layout_contact.py            -> feed_board/feed_board.kicad_pcb
Coordinates: the board's own frame in mm, origin at the centre of the mounting hole, x to the
right and y up, seen from the side the pins stand on (KiCad's front). KiCad's y runs downward,
so KiCad y = -y."""
import os, json, math, pcbnew
from pcbnew import VECTOR2I, FromMM, ToMM
import boards

HERE = os.path.dirname(os.path.abspath(__file__))
FP = "/usr/share/kicad/footprints"
P = lambda x, y: VECTOR2I(FromMM(x), FromMM(-y))
HEAD_KEEPOUT = 4.2 / 2 + 0.3            # back copper stays this far from the screw centre

# ---- feed board ---------------------------------------------------------------------
FEED_PINS = (("P1", "GND", -12.0), ("P2", "VIN", -5.0), ("P3", "VIN", 5.0), ("P4", "GND", 12.0))
FEED_PADS = (("W1", "GND", -8.5), ("W2", "VIN", 8.5))
FEED_OUTLINE = [(-15.0, -3.0), (15.0, -3.0), (15.0, 3.0), (-15.0, 3.0)]

class Layout:
    def __init__(self, name, schematic):
        self.name = name; self.board = pcbnew.BOARD(); self.board.SetCopperLayerCount(2)
        self.nets = {}; self.parts = {}
        self.sch = {p[0]: p for p in schematic().parts}
        d = self.board.GetDesignSettings().m_NetSettings.GetDefaultNetclass()
        d.SetTrackWidth(FromMM(0.25)); d.SetClearance(FromMM(0.15)); d.SetViaDiameter(FromMM(0.6)); d.SetViaDrill(FromMM(0.3))
    def net(self, name):
        if name not in self.nets:
            self.nets[name] = pcbnew.NETINFO_ITEM(self.board, name); self.board.Add(self.nets[name])
        return self.nets[name]
    def place(self, ref, x, y, rot=0, back=False):
        """Footprint, value and nets all come from the schematic."""
        _, _, value, fpname, pinnets = self.sch[ref]
        lib, name = fpname.split(":")
        fp = pcbnew.FootprintLoad(os.path.join(HERE, "lib.pretty") if lib == "lib" else os.path.join(FP, lib + ".pretty"), name)
        assert fp, fpname
        fp.SetReference(ref); fp.SetValue(value); fp.SetPosition(P(x, y))
        self.board.Add(fp)
        if back: fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        fp.SetOrientationDegrees(rot)
        fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
        for pad in fp.Pads():
            n = pinnets.get(pad.GetNumber())
            if n: pad.SetNet(self.net(n))
        self.parts[ref] = fp
        return fp
    def pad(self, ref, num):
        p = self.parts[ref].FindPadByNumber(num).GetPosition(); return (ToMM(p.x), -ToMM(p.y))
    def outline(self, pts):
        for a, b in zip(pts, pts[1:] + pts[:1]):
            s = pcbnew.PCB_SHAPE(self.board); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
            s.SetStart(P(*a)); s.SetEnd(P(*b)); s.SetWidth(FromMM(0.1)); self.board.Add(s)
    def track(self, netname, pts, width, layer):
        for a, b in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(self.board); t.SetStart(P(*a)); t.SetEnd(P(*b)); t.SetWidth(FromMM(width))
            t.SetLayer(layer); t.SetNet(self.net(netname)); self.board.Add(t)
    def via(self, netname, x, y, dia=0.6, drill=0.3):
        v = pcbnew.PCB_VIA(self.board); v.SetPosition(P(x, y)); v.SetDrill(FromMM(drill))
        v.SetWidth(pcbnew.F_Cu, FromMM(dia)); v.SetNet(self.net(netname)); self.board.Add(v)
        return (x, y)
    def zone(self, netname, layer, pts, priority=0, clearance=0.25):
        z = pcbnew.ZONE(self.board); z.SetLayer(layer); z.SetNet(self.net(netname))
        z.SetMinThickness(FromMM(0.25)); z.SetLocalClearance(FromMM(clearance))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL); z.SetAssignedPriority(priority)
        o = z.Outline(); o.NewOutline()
        for x, y in pts: o.Append(FromMM(x), FromMM(-y))
        self.board.Add(z); return z
    def head_keepout(self, x, y):
        """No back copper under the screw head: 4.2 mm circle plus 0.3 mm."""
        z = pcbnew.ZONE(self.board); z.SetLayer(pcbnew.B_Cu); z.SetIsRuleArea(True)
        z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowPads(False)
        z.SetDoNotAllowZoneFills(True); z.SetDoNotAllowFootprints(False)
        z.SetZoneName("screw head")
        o = z.Outline(); o.NewOutline()
        for i in range(72):
            a = math.radians(i * 5); o.Append(FromMM(x + HEAD_KEEPOUT * math.cos(a)), FromMM(-(y + HEAD_KEEPOUT * math.sin(a))))
        self.board.Add(z)
    def text(self, s, x, y, size=0.8, layer=pcbnew.F_SilkS):
        t = pcbnew.PCB_TEXT(self.board); t.SetText(s); t.SetPosition(P(x, y)); t.SetLayer(layer)
        t.SetTextSize(VECTOR2I(FromMM(size), FromMM(size))); t.SetTextThickness(FromMM(0.13))
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
        if layer == pcbnew.B_SilkS: t.SetMirrored(True)
        self.board.Add(t)
    def check_nets(self):
        bad = 0
        for ref, fp in self.parts.items():
            for pad in fp.Pads():
                if (self.sch[ref][4].get(pad.GetNumber()) or "") != pad.GetNetname(): bad += 1; print("MISMATCH", ref, pad.GetNumber())
        missing = [r for r in self.sch if not r.startswith("#") and r not in self.parts]
        if missing: print("NOT PLACED", missing)
        return bad + len(missing)
    def save(self, edge_clearance):
        d = os.path.join(HERE, self.name); os.makedirs(d, exist_ok=True)
        out = os.path.join(d, self.name + ".kicad_pcb")
        pro = {"board": {"design_settings": {"rules": {
                   "min_clearance": 0.15, "min_track_width": 0.2, "min_silk_clearance": 0.0, "min_through_hole_diameter": 0.3,
                   "min_via_diameter": 0.5, "min_via_annular_width": 0.1, "min_copper_edge_clearance": edge_clearance,
                   "min_hole_clearance": 0.25, "min_hole_to_hole": 0.25}}},
               "net_settings": {"classes": [{"name": "Default", "clearance": 0.15, "track_width": 0.25, "via_diameter": 0.6,
                    "via_drill": 0.3, "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.25,
                    "diff_pair_via_gap": 0.25, "bus_width": 12, "wire_width": 6, "line_style": 0,
                    "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)", "priority": 2147483647}],
                    "netclass_patterns": [], "meta": {"version": 4}},
               "meta": {"filename": self.name + ".kicad_pro", "version": 3}}
        json.dump(pro, open(out.replace(".kicad_pcb", ".kicad_pro"), "w"), indent=2)
        bds = self.board.GetDesignSettings()           # the fill uses these, not the project file
        bds.m_CopperEdgeClearance = FromMM(edge_clearance); bds.m_HoleClearance = FromMM(0.25)
        pcbnew.ZONE_FILLER(self.board).Fill(self.board.Zones())
        pcbnew.SaveBoard(out, self.board)
        print("%s: %d footprints, %d tracks and vias, %d areas; net mismatches: %d"
              % (self.name, len(self.parts), len(self.board.GetTracks()), len(self.board.Zones()), self.check_nets()))

def feed_board():
    L = Layout("feed_board", boards.feed_board)
    F, B = pcbnew.F_Cu, pcbnew.B_Cu
    L.outline(FEED_OUTLINE)
    for ref, netname, x in FEED_PINS:
        assert L.sch[ref][4]["1"] == netname
        L.place(ref, x, 0)
    for ref, netname, x in FEED_PADS:
        assert L.sch[ref][4]["1"] == netname
        L.place(ref, x, 0, back=True)
    L.place("H1", 0, 0); L.head_keepout(0, 0)
    box = lambda x0, y0, x1, y1: [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    # Front: ground everywhere, except a 12-24 V area that joins the two inner pins and passes
    # the screw hole on the +y side. Ground passes the inner pins and the hole on the -y side.
    L.zone("GND", F, box(-15, -3, 15, 3), priority=0)
    L.zone("VIN", F, [(-6.3, -1.1), (-3.7, -1.1), (-3.7, 0.3), (3.7, 0.3), (3.7, -1.1), (7.5, -1.1), (7.5, 3), (-6.3, 3)], priority=1)
    # Back: 12-24 V from the inner pins to its wire pad; ground round the other wire pad.
    # The screw head's keep-out leaves almost nothing across the middle on this side.
    L.zone("VIN", B, box(-6.3, -3, 10.05, 3), priority=1)
    L.zone("GND", B, box(-15, -3, -6.75, 3), priority=0)
    for x, y in ((-10.4, 2.0), (-10.4, 1.0), (-10.4, 0.0), (-10.4, -1.0), (-10.4, -2.0), (-8.5, 2.1), (-8.5, -2.1), (-7.4, 2.1), (-7.4, -2.1)):
        L.via("GND", x, y, 0.8, 0.4)
    for x, y in ((-3.2, 1.3), (-3.2, 2.2), (3.2, 1.3), (3.2, 2.2), (6.9, 2.0), (6.9, 1.0), (6.9, 0.0)):
        L.via("VIN", x, y, 0.8, 0.4)
    L.text("FEED", -8.3, 0.0, 0.9)
    L.text("24V", 8.6, 0.0, 0.8)
    for x in (-5, 5): L.text("+", x, -2.0, 1.0)
    for x in (-12, 12): L.text("-", x + (1.9 if x > 0 else -1.9), 0.0, 1.0)
    L.save(edge_clearance=0.25)
    return L

if __name__ == "__main__":
    feed_board()
