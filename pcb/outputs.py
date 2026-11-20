#!/usr/bin/env python3
"""Checks and manufacturing files for one or more boards:
  python3 outputs.py row_main row_strip
Per board: erc.rpt, drc.rpt, <board>_top.png, <board>_bottom.png, bom.csv, fab/ (Gerber,
drill, placement). Prints the counts from the two reports as KiCad wrote them."""
import os, re, sys, subprocess, pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))

SAME = {"JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal": "JST SM04B-SRSS-TB socket (pins: GND 5V ID LED)",
        "SpringPin_MillMax0906": "Spring pin with solder tail, Mill-Max 0906 class, 2 A",
        "Hirose_FH12-12S-0.5SH_1x12-1MP_P0.50mm_Horizontal": "Hirose FH12-12S-0.5SH flat-cable socket, 12-way 0.5 mm, bottom contact"}

def run(*a): return subprocess.run(a, capture_output=True, text=True)

def outputs(name):
    d = os.path.join(HERE, name); pcb = os.path.join(d, name + ".kicad_pcb"); sch = os.path.join(d, name + ".kicad_sch")
    run("kicad-cli", "sch", "erc", "--severity-all", "-o", os.path.join(d, "erc.rpt"), sch)
    run("kicad-cli", "pcb", "drc", "--severity-all", "-o", os.path.join(d, "drc.rpt"), pcb)
    erc = re.search(r"ERC messages:.*", open(os.path.join(d, "erc.rpt")).read()).group()
    drc = re.findall(r"Found \d+ [^*]*", open(os.path.join(d, "drc.rpt")).read())
    print("%s\n  ERC: %s\n  DRC: %s" % (name, erc.strip(), "; ".join(s.strip() for s in drc)))
    for side in ("top", "bottom"):
        r = run("kicad-cli", "pcb", "render", "--side", side, "--quality", "basic", "-w", "1600", "-h", "900",
                "-o", os.path.join(d, "%s_%s.png" % (name, side)), pcb)
        if r.returncode: print("  render %s failed: %s" % (side, r.stderr.strip()[-200:]))
    board = pcbnew.LoadBoard(pcb)
    fab = os.path.join(d, "fab"); os.makedirs(fab, exist_ok=True)
    layers = ["F.Cu", "B.Cu", "F.Mask", "B.Mask", "F.Paste", "B.Paste", "F.SilkS", "B.SilkS", "Edge.Cuts"]
    if board.GetCopperLayerCount() == 4: layers[1:1] = ["In1.Cu", "In2.Cu"]
    if board.GetLayerName(pcbnew.User_1) == "V.Score": layers.append("User.1")      # row boards: the snap lines
    r = run("kicad-cli", "pcb", "export", "gerbers", "-o", fab + "/", "--layers", ",".join(layers), pcb)
    if r.returncode: print("  gerbers failed:", r.stderr.strip()[-200:])
    r = run("kicad-cli", "pcb", "export", "drill", "-o", fab + "/", "--format", "excellon", pcb)
    if r.returncode: print("  drill failed:", r.stderr.strip()[-200:])
    r = run("kicad-cli", "pcb", "export", "pos", "-o", os.path.join(fab, name + "-pos.csv"), "--format", "csv", "--units", "mm", "--side", "both", pcb)
    if r.returncode: print("  pos failed:", r.stderr.strip()[-200:])
    groups = {}
    for fp in board.GetFootprints():
        if fp.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_BOM: continue
        name_ = str(fp.GetFPID().GetLibItemName())
        key = (SAME.get(name_, fp.GetValue()), name_)      # one line for parts that differ only in what they are wired to
        groups.setdefault(key, []).append(fp.GetReference())
    q = lambda s: '"%s"' % s if "," in s else s
    with open(os.path.join(d, "bom.csv"), "w") as f:
        f.write("Qty,Value,Footprint,References\n")
        for (value, fpname), refs in sorted(groups.items(), key=lambda g: (re.sub(r"\d+$", "", min(g[1])), g[0])):
            f.write("%d,%s,%s,%s\n" % (len(refs), q(value), fpname, " ".join(sorted(refs))))
    print("  fab: %d files; bom: %d lines" % (len(os.listdir(fab)), len(groups)))

if __name__ == "__main__":
    for name in sys.argv[1:]: outputs(name)
