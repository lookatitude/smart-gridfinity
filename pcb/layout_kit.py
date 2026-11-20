#!/usr/bin/env python3
"""Shared steps for the boards that are routed with Freerouting: ground areas before and
after routing, and repair of connections the router left open. Used by layout_power.py,
which sets inside, GROUND_OUTLINE, OUT and SCHEMATIC for its own board before calling in."""
import os, re, sys, subprocess, pcbnew
from pcbnew import VECTOR2I, FromMM, ToMM

HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda x, y: VECTOR2I(FromMM(x), FromMM(y))
EDGE = 0.5
# Set by the board script that uses this module:
inside = None            # function: is the box (x0, y0, x1, y1) inside the board outline?
GROUND_OUTLINE = None    # corner points of the ground areas
OUT = None               # path of the .kicad_pcb file
SCHEMATIC = None         # function from boards.py that returns the board's circuit

def pre_ground(board, gnd, skip=(), obstacles=(), back=()):
    """Ground plane on the first inner layer, and a via down to it beside every surface
    ground pad. Run after placement and before routing. Shared with layout_power.py."""
    # Ground: the first inner layer is one ground plane, and every surface ground pad gets a
    # via down to it, placed now, before routing, while there is still room to choose a spot.
    # The router sees the plane, leaves ground alone, and routes the signals round the vias.
    import math
    plane = pcbnew.ZONE(board); plane.SetLayer(pcbnew.In1_Cu); plane.SetNet(gnd)
    plane.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL); plane.SetMinThickness(FromMM(0.2))
    po = plane.Outline(); po.NewOutline()
    for x, y in GROUND_OUTLINE: po.Append(FromMM(x), FromMM(y))
    board.Add(plane)
    pads = [(p, p.GetBoundingBox()) for f in board.GetFootprints() for p in f.Pads()]
    rects = [(ToMM(b.GetLeft()), ToMM(b.GetTop()), ToMM(b.GetRight()), ToMM(b.GetBottom()), p.GetNetname() == "GND") for p, b in pads]
    rects += [tuple(o) + (False,) for o in obstacles]       # vias and stubs of other nets already on the board
    def gap(x, y, r): return math.hypot(max(r[0] - x, 0, x - r[2]), max(r[1] - y, 0, y - r[3]))
    vias, missed = [], []
    for p, b in pads:
        if p.GetNetname() != "GND" or p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH: continue
        if (p.GetParentFootprint().GetReference(), p.GetNumber()) in skip: continue
        px, py = ToMM(p.GetPosition().x), ToMM(p.GetPosition().y)
        best = None
        for r in (0.0, 0.75, 0.9, 1.05, 1.2, 1.4, 1.6, 1.9, 2.2, 2.6, 3.0):
            for a in range(0, 360, 15 if r else 360):
                x, y = px + r * math.cos(math.radians(a)), py + r * math.sin(math.radians(a))
                if not inside((x - 0.3, y - 0.3, x + 0.3, y + 0.3)): continue
                if any(not g and gap(x, y, q) < 0.25 + 0.3 for *q, g in rects): continue      # other pads
                if any(gap(x, y, q) < 0.25 + 0.3 for q in back): continue                      # other nets' tracks on the back
                if any(math.hypot(x - vx, y - vy) < 0.9 for vx, vy in vias): continue          # other vias
                n = max(1, int(r / 0.1))
                if any(not g and gap(px + (x - px) * k / n, py + (y - py) * k / n, q) < 0.075 + 0.2
                       for k in range(n + 1) for *q, g in rects): continue                    # the stub
                best = (x, y); break
            if best: break
        if not best: missed.append(p.GetParentFootprint().GetReference() + "." + p.GetNumber()); continue
        vias.append(best)
        v = pcbnew.PCB_VIA(board); v.SetPosition(P(*best)); v.SetDrill(FromMM(0.25))
        v.SetWidth(pcbnew.F_Cu, FromMM(0.5)); v.SetNet(gnd); board.Add(v)
        if best != (px, py):
            t = pcbnew.PCB_TRACK(board); t.SetStart(P(px, py)); t.SetEnd(P(*best)); t.SetWidth(FromMM(0.15))
            t.SetLayer(pcbnew.F_Cu); t.SetNet(gnd); board.Add(t)
    return "ground vias placed before routing: %d; pads with no room: %s" % (len(vias), missed or "none")

def ground(board, flood=True, escape=True, layers=(pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu), pitch=0.8):
    """Ground is wired after routing. Every ground pad gets its net back and, where there is
    room, its own via beside it; then all four layers are flooded with ground and stitching
    vias tie the floods together."""
    import math
    gnd = board.FindNet("GND")
    if gnd is None:                      # an unused net is dropped when the board is saved
        gnd = pcbnew.NETINFO_ITEM(board, "GND"); board.Add(gnd)
    want = {p[0]: p[4] for p in SCHEMATIC().parts}
    gpads = []
    for fp in board.GetFootprints():
        ref, val = fp.GetReference(), fp.GetValue()
        for pad in fp.Pads():
            if want.get(ref, {}).get(pad.GetNumber()) == "GND" or val == "GND":
                pad.SetNet(gnd); gpads.append(pad)

    # Everything a new via or stub must keep away from: (x0, y0, x1, y1, is_ground, has_hole, front_only)
    obstacles = []
    def note(x0, y0, x1, y1, g, hole, front): obstacles.append((x0, y0, x1, y1, g, hole, front))
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            bb = pad.GetBoundingBox(); th = pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
            note(ToMM(bb.GetLeft()), ToMM(bb.GetTop()), ToMM(bb.GetRight()), ToMM(bb.GetBottom()),
                 pad.GetNetname() == "GND", th, not th)
    for t in board.GetTracks():
        g = t.GetNetname() == "GND"
        if t.GetClass() == "PCB_VIA":
            p = t.GetPosition(); r = 0.3
            note(ToMM(p.x) - r, ToMM(p.y) - r, ToMM(p.x) + r, ToMM(p.y) + r, g, True, False)
        else:
            a, b, w = t.GetStart(), t.GetEnd(), ToMM(t.GetWidth()) / 2
            n = max(1, int(math.hypot(ToMM(b.x - a.x), ToMM(b.y - a.y)) / 0.15))
            for k in range(n + 1):
                x, y = ToMM(a.x + (b.x - a.x) * k / n), ToMM(a.y + (b.y - a.y) * k / n)
                note(x - w, y - w, x + w, y + w, g, False, t.GetLayer() == pcbnew.F_Cu)
    def gap(x, y, o):
        dx = max(o[0] - x, 0, x - o[2]); dy = max(o[1] - y, 0, y - o[3]); return math.hypot(dx, dy)
    def via_ok(x, y):
        if not inside((x - 0.25, y - 0.25, x + 0.25, y + 0.25)): return False
        for o in obstacles:
            d = gap(x, y, o)
            if o[5] and d < 0.25 + 0.3: return False            # hole to hole
            if not o[4] and d < 0.25 + 0.17: return False       # other nets, any layer (a via spans all)
        return True
    def stub_ok(x0, y0, x1, y1):
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / 0.1))
        for k in range(n + 1):
            x, y = x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n
            if not inside((x - 0.1, y - 0.1, x + 0.1, y + 0.1)): return False
            # front copper of other nets: surface pads and tracks, and anything with a hole
            if any((o[6] or o[5]) and not o[4] and gap(x, y, o) < 0.075 + 0.17 for o in obstacles): return False
        return True
    def add_via(x, y):
        v = pcbnew.PCB_VIA(board); v.SetPosition(P(x, y)); v.SetDrill(FromMM(0.25))
        v.SetWidth(pcbnew.F_Cu, FromMM(0.5)); v.SetNet(gnd); board.Add(v)
        note(x - 0.25, y - 0.25, x + 0.25, y + 0.25, True, True, False)

    escaped = 0
    with_via, without = [], []
    for pad in (gpads if escape else []):
        if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH: continue
        px, py = ToMM(pad.GetPosition().x), ToMM(pad.GetPosition().y)
        done = False
        def stub(a, b):
            t = pcbnew.PCB_TRACK(board); t.SetStart(P(*a)); t.SetEnd(P(*b)); t.SetWidth(FromMM(0.15))
            t.SetLayer(pcbnew.F_Cu); t.SetNet(gnd); board.Add(t)
            n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 0.15))
            for k in range(n + 1):
                x, y = a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n
                note(x - 0.075, y - 0.075, x + 0.075, y + 0.075, True, False, True)
        for r in (0.0, 0.7, 0.9, 1.1, 1.3, 1.5, 1.8, 2.1, 2.4, 2.8, 3.2, 3.6, 4.0):
            for a in range(0, 360, 10 if r else 360):
                x, y = px + r * math.cos(math.radians(a)), py + r * math.sin(math.radians(a))
                if via_ok(x, y) and stub_ok(px, py, x, y):
                    add_via(x, y)
                    if r: stub((px, py), (x, y))
                    escaped += 1; done = True; break
            if done: break
        if not done:                     # no straight way out: try one bend
            spots = [(px + 0.3 * i, py + 0.3 * j) for i in range(-10, 11) for j in range(-10, 11)]
            vias = sorted((q for q in spots if via_ok(*q)), key=lambda q: math.hypot(q[0] - px, q[1] - py))[:60]
            mids = [q for q in spots if stub_ok(px, py, *q)]
            for vx, vy in vias:
                m = next((q for q in mids if stub_ok(q[0], q[1], vx, vy)), None)
                if m:
                    add_via(vx, vy); stub((px, py), m); stub(m, (vx, vy))
                    escaped += 1; done = True; break
        (with_via if done else without).append((px, py))
    # A pad with no room for a via is tied to the nearest ground pad that has one.
    for px, py in without:
        for qx, qy in sorted(with_via, key=lambda q: math.hypot(q[0] - px, q[1] - py)):
            if math.hypot(qx - px, qy - py) > 4.0: break
            if stub_ok(px, py, qx, qy):
                t = pcbnew.PCB_TRACK(board); t.SetStart(P(px, py)); t.SetEnd(P(qx, qy)); t.SetWidth(FromMM(0.15))
                t.SetLayer(pcbnew.F_Cu); t.SetNet(gnd); board.Add(t); with_via.append((px, py)); break

    if not flood: return "%d of %d ground pads got their own via" % (escaped, len(gpads))
    zones = [(z, z.GetLayer()) for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname() == "GND"]
    for layer in layers:
        z = pcbnew.ZONE(board); z.SetLayer(layer); z.SetNet(gnd); z.SetMinThickness(FromMM(0.2))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        o = z.Outline(); o.NewOutline()
        for x, y in GROUND_OUTLINE: o.Append(FromMM(x), FromMM(y))
        board.Add(z); zones.append((z, layer))
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    ring = [(0, 0)] + [(0.5 * math.cos(a * math.pi / 4), 0.5 * math.sin(a * math.pi / 4)) for a in range(8)]
    # Stitching: wherever a via fits and at least one other layer has ground copper under it,
    # drop a via. The unbroken inner layer then ties that piece of copper to everything else.
    stitched, y = 0, 0.6
    while y < 32.0:
        x = 0.6
        while x < 65.5:
            if via_ok(x, y):
                hits = sum(all(z.HitTestFilledArea(layer, P(x + dx, y + dy), 0) for dx, dy in ring) for z, layer in zones)
                if hits >= 2: add_via(x, y); stitched += 1
            x += pitch
        y += pitch
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    return "%d of %d ground pads got their own via, %d stitching vias" % (escaped, len(gpads), stitched)

def link_clear(board, layer, a, b, netname, half=0.075, clearance=0.17):
    """Can a straight track from a to b on this layer keep its distance from all other nets?"""
    import math
    def seg_point(px, py, x0, y0, x1, y1):
        dx, dy = x1 - x0, y1 - y0; L = dx * dx + dy * dy
        t = 0 if L == 0 else max(0, min(1, ((px - x0) * dx + (py - y0) * dy) / L))
        return math.hypot(px - (x0 + t * dx), py - (y0 + t * dy))
    n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 0.08))
    pts = [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(n + 1)]
    if not all(inside((x - 0.3, y - 0.3, x + 0.3, y + 0.3)) for x, y in pts): return False
    for t in board.GetTracks():
        if t.GetNetname() == netname: continue
        if t.GetClass() == "PCB_VIA":
            p = t.GetPosition(); r = ToMM(t.GetWidth(pcbnew.F_Cu)) / 2
            if any(math.hypot(x - ToMM(p.x), y - ToMM(p.y)) < r + half + clearance for x, y in pts): return False
        elif t.GetLayer() == layer:
            s0, s1, w = t.GetStart(), t.GetEnd(), ToMM(t.GetWidth()) / 2
            if any(seg_point(x, y, ToMM(s0.x), ToMM(s0.y), ToMM(s1.x), ToMM(s1.y)) < w + half + clearance for x, y in pts): return False
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() == netname: continue
            if pad.GetAttribute() != pcbnew.PAD_ATTRIB_PTH and layer != pcbnew.F_Cu: continue
            bb = pad.GetBoundingBox()
            r = (ToMM(bb.GetLeft()), ToMM(bb.GetTop()), ToMM(bb.GetRight()), ToMM(bb.GetBottom()))
            if any(math.hypot(max(r[0] - x, 0, x - r[2]), max(r[1] - y, 0, y - r[3])) < half + clearance for x, y in pts): return False
    return True

def repair(board):
    """Join the last stragglers. KiCad's own check names each pair of items that should be
    connected; where a straight track between them is clear on some layer, add it."""
    added = 0
    for _ in range(6):
        rpt = OUT.replace(".kicad_pcb", "_tmp.rpt")
        pcbnew.SaveBoard(OUT, board)
        subprocess.run(["kicad-cli", "pcb", "drc", "--severity-all", "-o", rpt, OUT], capture_output=True)
        text = open(rpt).read(); os.unlink(rpt)
        pairs = re.findall(r"\[unconnected_items\][^\n]*\n[^\n]*\n\s+@\(([-\d.]+) mm, ([-\d.]+) mm\): (?:PTH pad|Pad|Track|Via)[^\n]*?\[([^\]]+)\][^\n]*\n\s+@\(([-\d.]+) mm, ([-\d.]+) mm\): (?:PTH pad|Pad|Track|Via)", text)
        progress = False
        for x0, y0, netname, x1, y1 in pairs:
            a, b = (float(x0), float(y0)), (float(x1), float(y1))
            both_through = False
            for layer in (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In2_Cu):
                # an inner or back track only helps if both ends reach that layer (vias or through pads)
                if layer != pcbnew.F_Cu:
                    ends = 0
                    for t in board.GetTracks():
                        if t.GetClass() == "PCB_VIA" and any(abs(ToMM(t.GetPosition().x) - q[0]) < 0.01 and abs(ToMM(t.GetPosition().y) - q[1]) < 0.01 for q in (a, b)): ends += 1
                    if ends < 2: continue
                if link_clear(board, layer, a, b, netname):
                    t = pcbnew.PCB_TRACK(board); t.SetStart(P(*a)); t.SetEnd(P(*b)); t.SetWidth(FromMM(0.15))
                    t.SetLayer(layer); t.SetNet(board.FindNet(netname)); board.Add(t); added += 1; progress = True; break
        if not progress: break
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(OUT, board)
    return added
