#!/usr/bin/env python3
"""Schematics for the smart Gridfinity boards, written as KiCad files:
  bin_board/     in the foot of every smart bin
  row_main/      under the first row of a tile: pins, processor, 5 V converter
  row_strip/     under every further row: pins and one switch chip
  feed_board/    under the power cell of a starter tile: four feed pins
  power_board/   in the power bin
Run (all boards, or only the ones named: python3 boards.py row_main), then
check with:  kicad-cli sch erc --exit-code-violations <file>
Connections are net labels on the pin ends (no drawn wires)."""
import os
from kisch import Schematic

R0603 = "Resistor_SMD:R_0603_1608Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
C1206 = "Capacitor_SMD:C_1206_3216Metric"
PAD = "TestPoint:TestPoint_Pad_D2.0mm"
MODULE = ("RF_Module:ESP32-C3-WROOM-02", "ESP32-C3-WROOM-02", "RF_Module:ESP32-C3-WROOM-02")

SPRING = "lib:SpringPin_MillMax0906"
HOLE = "lib:MountHole_M2_HeadBack"
WIREPAD = "lib:WirePad_2.5"
UID_PINS = {"GND": "GND", "IO": "ID", "NC": None}

def grid(col, row): return (25.4 + col * 30.48, 25.4 + row * 25.4)

class Board(Schematic):
    def __init__(self, project, title):
        super().__init__(project, title); self.count = {}; self.slot = 0
        self.swap = {}                # footprint -> footprint used instead (row boards: wire pads for headers and test points)
    def part(self, ref, lib_id, value, footprint, x, y, nets, unit=1):
        super().part(ref, lib_id, value, self.swap.get(footprint, footprint), x, y, nets, unit)
    def ref(self, prefix):
        self.count[prefix] = self.count.get(prefix, 0) + 1
        return "%s%d" % (prefix, self.count[prefix])
    def place(self):
        self.slot += 1
        return grid(4 + (self.slot - 1) % 9, (self.slot - 1) // 9)
    def R(self, value, a, b): x, y = self.place(); self.part(self.ref("R"), "Device:R", value, R0603, x, y, {"1": a, "2": b})
    def C(self, value, a, b, fp=C0603): x, y = self.place(); self.part(self.ref("C"), "Device:C", value, fp, x, y, {"1": a, "2": b})
    def pad(self, net, what, fp=PAD):
        x, y = self.place(); self.part(self.ref("TP"), "Connector:TestPoint", what, fp, x, y, {"1": net})
    def flag(self, net): x, y = self.place(); self.part(self.ref("#FLG"), "power:PWR_FLAG", "PWR_FLAG", "", x, y, {"1": net})

    def core(self, io, hv=False):
        """Module, 3.3 V regulator, input diode, boot straps, programming header.
        With hv, the board is fed with 7-24 V and makes its own 5 V with a step-down converter."""
        nets = {"3V3": "+3V3", "GND": "GND", "EN": "EN", "IO8": "IO8", "IO9": "BOOT", "IO2": "IO2",
                "IO20/RXD": "RXD", "IO21/TXD": "TXD"}
        for pin in ("IO0", "IO1", "IO3", "IO4", "IO5", "IO6", "IO7", "IO10", "IO18", "IO19"):
            nets[pin] = io.get(pin)
        self.part("U1", MODULE[0], MODULE[1], MODULE[2], 60.96, 76.2, nets)
        self.part("U2", "Regulator_Linear:AP2112K-3.3", "AP2112K-3.3 (3.3 V LDO, >=500 mA)",
                  "Package_TO_SOT_SMD:SOT-23-5", 60.96, 139.7,
                  {"VIN": "+5V", "EN": "+5V", "GND": "GND", "VOUT": "+3V3", "NC": None})
        self.count["D"] = 1
        if hv:
            self.part("D1", "Device:D_Schottky", "SS34 (3 A, 40 V Schottky)", "Diode_SMD:D_SMA", 30.48, 139.7,
                      {"A": "VIN", "K": "HV"})
            self.part("U6", "Regulator_Switching:AP63205WU", "AP63205 class: 5 V out, 2 A, 3.8-32 V in",
                      "Package_TO_SOT_SMD:TSOT-23-6", 30.48, 170.18,
                      {"IN": "HV", "EN": "HV", "GND": "GND", "SW": "SW", "BST": "BST", "FB": "+5V"})
            x, y = self.place()
            self.part("L1", "Device:L", "4.7u, saturation 3.1 A or more", "Inductor_SMD:L_Bourns_SRP5030T", x, y, {"1": "SW", "2": "+5V"})
            x, y = self.place()
            self.part(self.ref("D"), "Device:D_TVS", "Surge diode, 24 V standoff, clamps below 40 V (SMAJ24A class)", "Diode_SMD:D_SMA", x, y, {"A1": "HV", "A2": "GND"})
            self.C("100n", "BST", "SW"); self.C("10u 50V", "HV", "GND", C1206); self.C("10u 50V", "HV", "GND", C1206)
            self.C("22u", "+5V", "GND", C0805); self.flag("HV")
        else:
            self.part("D1", "Device:D_Schottky", "SS14 (1 A Schottky)", "Diode_SMD:D_SMA", 30.48, 139.7,
                      {"A": "VIN", "K": "+5V"})
        self.C("22u", "+5V", "GND", C0805); self.C("1u", "+5V", "GND"); self.C("1u", "+3V3", "GND")
        self.C("10u", "+3V3", "GND", C0805); self.C("100n", "+3V3", "GND")
        self.R("10k", "+3V3", "EN"); self.C("1u", "EN", "GND")
        self.R("10k", "+3V3", "IO8"); self.R("10k", "+3V3", "BOOT"); self.R("10k", "+3V3", "IO2")
        x, y = self.place()
        self.part("J1", "Connector_Generic:Conn_01x06", "PROG: 3V3 GND TX RX EN BOOT",
                  "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical", x, y,
                  {"1": "+3V3", "2": "GND", "3": "TXD", "4": "RXD", "5": "EN", "6": "BOOT"})
        self.pad("VIN", "12-24 V in" if hv else "5V in"); self.pad("GND", "ground")
        self.flag("VIN"); self.flag("GND"); self.flag("+5V")

def bin_board():
    """No radio and no processor: contact rings, one ID chip, and the feed for the LED chain."""
    b = Board("bin_board", "Smart Gridfinity bin board (passive)")
    b.slot = 0
    b.pad("VIN", "5 V ring"); b.pad("GND", "ground ring"); b.pad("DATA", "LED data ring"); b.pad("ID", "ID centre pad")
    b.pad("ID", "ID pad of second foot (wire)")
    b.part("D1", "Device:D_Schottky", "SS14 (1 A Schottky)", "Diode_SMD:D_SMA", 30.48, 76.2, {"A": "VIN", "K": "+5V"})
    b.C("10u", "+5V", "GND", C0805); b.C("100n", "+5V", "GND")
    # LED data: series resistor, and a pull-down so the LEDs see a clean low when the
    # tile is talking to another cell.
    b.R("100", "DATA", "LED_DIN"); b.R("100k", "LED_DIN", "GND")
    b.part("J1", "Connector_Generic:Conn_01x03", "LED chain: 5V DATA GND",
           "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical", 60.96, 76.2,
           {"1": "+5V", "2": "LED_DIN", "3": "GND"})
    # Identity: a 1-Wire memory with a factory-set unique number, powered from the data line.
    b.part("U1", "Memory_EEPROM:DS2431P", "DS2431 class: 1-Wire, unique 64-bit ID, 5 V tolerant",
           "Package_SO_J-Lead:TSOC-6_3.76x3.94mm_P1.27mm", 91.44, 76.2, UID_PINS)
    b.flag("VIN"); b.flag("GND"); b.flag("+5V")
    b.note("Bin board. Four contact rings on the underside: ID (centre), LED data, 5 V, ground (outer).", 25.4, 120)
    return b

def power_board():
    """In the power bin: DC input, fuse, the high-voltage contacts that reach the recessed
    pins of the starter tile's power cell, and the hub radio."""
    b = Board("power_board", "Smart Gridfinity power bin board")
    b.core({"IO18": "USB_DN", "IO19": "USB_DP"}, hv=True)
    b.pad("USB_DN", "USB D-"); b.pad("USB_DP", "USB D+")
    x, y = b.place()
    b.part("J2", "Connector_Generic:Conn_01x02", "DC in, 12-24 V", "TerminalBlock:TerminalBlock_MaiXu_MX126-5.0-02P_1x02_P5.00mm",
           x, y, {"1": "DC_IN", "2": "GND"})
    x, y = b.place()
    b.part("F1", "Device:Polyfuse", "PTC 3 A hold, 30 V", "Fuse:Fuse_1812_4532Metric", x, y, {"1": "DC_IN", "2": "VIN"})
    b.pad("VIN", "feed contact +, second pin"); b.pad("GND", "feed contact -, second pin")
    b.note("Power bin board. VIN and GND pads are the contacts that reach down to the recessed pins of the power cell.", 25.4, 190)
    return b

def feed_board():
    """Under the power cell of a starter tile: four spring pins carry the 12-24 V feed.
    Two nets, two wire pads for the leads to the first-row board."""
    b = Board("feed_board", "Smart Gridfinity feed contact board")
    b.slot = 0
    for ref, net, what in (("P1", "GND", "feed pin -, x = -12"), ("P2", "VIN", "feed pin +, x = -5"),
                           ("P3", "VIN", "feed pin +, x = +5"), ("P4", "GND", "feed pin -, x = +12")):
        x, y = b.place(); b.part(ref, "Connector:TestPoint", what, SPRING, x, y, {"1": net})
    for ref, net, what in (("W1", "GND", "lead to row board GND"), ("W2", "VIN", "lead to row board VIN")):
        x, y = b.place(); b.part(ref, "Connector:TestPoint", what, WIREPAD, x, y, {"1": net})
    x, y = b.place(); b.part("H1", "Mechanical:MountingHole", "M2 screw, head on the back", HOLE, x, y, {})
    b.note("Feed contact board. 12-24 V on the two inner pins, ground on the two outer pins.", 25.4, 120)
    return b

# ---- row boards: one long board under every row of cells -------------------------------
FFC = "Connector_FFC-FPC:Hirose_FH12-12S-0.5SH_1x12-1MP_P0.50mm_Horizontal"
FFC_SYM = "Connector_Generic_MountingPin:Conn_01x12_MountingPin"
TSSOP16 = "Package_SO:TSSOP-16_4.4x5mm_P0.65mm"
TSSOP24 = "Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm"
ROW_CELLS = 4
# The flat cable between two row boards, by position p = 1..12 counted from the -x end of
# the connector in the board frame (not by pad number: IN and OUT connectors are turned
# 180 degrees to each other, so a straight same-side cable keeps p, not the pad number).
CABLE = ("+5V", "+5V", "GND", "GND", "LED_BUS", "GND", "ID_BUS", "A0", "A1", "EN_a", "EN_b", "EN_c")
def ffc_nets(by_position, reverse):
    """Pin nets of a flat-cable connector from the nets by position. On the board the OUT
    connector (mouth toward +y) has pad 1 at the -x end, the IN connector pad 12."""
    assert len(by_position) == 12
    nets = {str(13 - p if reverse else p): n for p, n in enumerate(by_position, 1)}
    nets["MP"] = None
    return nets

def row_cells(b):
    """Four spring pins and one screw hole per cell. Refs P<cell><1..4>: ID, LED data, +5V, GND."""
    for c in range(1, ROW_CELLS + 1):
        for i, (net, what) in enumerate((("ID%d" % c, "ID pin"), ("LED%d" % c, "LED data pin"), ("+5V", "5 V pin"), ("GND", "ground pin")), 1):
            x, y = b.place(); b.part("P%d%d" % (c, i), "Connector:TestPoint", "cell %d %s" % (c, what), SPRING, x, y, {"1": net})
        x, y = b.place(); b.part("H%d" % c, "Mechanical:MountingHole", "M2 screw, head on the back", HOLE, x, y, {})

def cell_switch(b, ref, a, bb, inhibit, x, y):
    """74HCT4052: X side switches LED data, Y side the ID line, to one of this row's four cells."""
    nets = {"X": "LED_BUS", "Y": "ID_BUS", "A": a, "B": bb, "INH": inhibit, "VDD": "+5V", "VSS": "GND", "VEE": "GND"}
    for c in range(ROW_CELLS): nets["X%d" % c] = "LED%d" % (c + 1); nets["Y%d" % c] = "ID%d" % (c + 1)
    b.part(ref, "Analog_Switch:CD4052B", "74HCT4052", TSSOP16, x, y, nets)
    b.C("100n", "+5V", "GND")

def row_strip():
    """Rows 2 to 4 of a tile: a strip with the pins of four cells, one 74HCT4052 and two
    flat-cable connectors. No processor. The row is selected by its EN_THIS line (low = on);
    the two remaining enable lines move up one position on the way to the next row."""
    b = Board("row_strip", "Smart Gridfinity row strip (rows 2 to 4)")
    b.slot = 0
    into = list(CABLE); into[9:] = ["EN_THIS", "EN_N1", "EN_N2"]
    out = list(CABLE); out[9:] = ["EN_N1", "EN_N2", None]
    b.part("J_IN", FFC_SYM, "from the previous row (FH12-12S-0.5SH)", FFC, 30.48, 76.2, ffc_nets(into, True))
    b.part("J_OUT", FFC_SYM, "to the next row (FH12-12S-0.5SH)", FFC, 106.68, 76.2, ffc_nets(out, False))
    cell_switch(b, "U1", "A0", "A1", "EN_THIS", 68.58, 76.2)
    b.R("100k", "EN_THIS", "+5V")                      # an undriven row stays off
    row_cells(b)
    b.flag("+5V"); b.flag("GND")
    b.note("Row strip. Cable positions 1-12 from the -x end: 5V 5V GND GND LED_BUS GND ID_BUS A0 A1 EN EN EN.", 25.4, 150)
    return b

def row_main():
    """First row of a tile, and the tile's processor board. One
    74HCT4052 per row switches LED data and the ID line to a cell; a 74HCT139 enables one
    row. Cell number = SEL3..SEL0 = row * 4 + column."""
    b = Board("row_main", "Smart Gridfinity row board with processor (row 1)")
    b.swap = {PAD: WIREPAD, "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical": "lib:WirePads_1x06_P1.5mm"}
    b.core({"IO4": "SEL0", "IO5": "SEL1", "IO6": "SEL2", "IO7": "SEL3",
            "IO0": "LED_IO", "IO1": "OW_IO", "IO3": "NB_IO", "IO18": "USB_DN", "IO19": "USB_DP"}, hv=True)
    small = "lib:WirePad_1.0"
    b.pad("USB_DN", "USB D-", small); b.pad("USB_DP", "USB D+", small)
    b.R("2k2", "+3V3", "OW_IO"); b.R("100k", "+3V3", "NB_IO")
    clamp = lambda io: b.part(b.ref("D"), "Diode:BAT54S", "BAT54S clamp", "Package_TO_SOT_SMD:SOT-23", *b.place(),
                              {"A": "GND", "K": "+3V3", "COM": io})
    b.R("220", "LED_IO", "LED_BUS"); clamp("LED_IO")
    b.R("220", "OW_IO", "ID_BUS"); clamp("OW_IO")
    # this row's four cells
    cell_switch(b, "U3", "SEL0", "SEL1", "EN0", 45.72, 228.6)
    # row enables: one half of a 74HCT139, the other half parked
    dec = ("U4", "74xx:74LS139", "74HCT139", TSSOP16)
    b.part(*dec, 30.48, 304.8, {"E": "GND", "A0": "SEL2", "A1": "SEL3", "O0": "EN0", "O1": "EN1", "O2": "EN2", "O3": "EN3"}, unit=1)
    b.part(*dec, 68.58, 304.8, {"E": "+5V", "A0": "GND", "A1": "GND", "O0": None, "O1": None, "O2": None, "O3": None}, unit=2)
    b.part(*dec, 106.68, 304.8, {"VCC": "+5V", "GND": "GND"}, unit=3)
    b.C("100n", "+5V", "GND")
    # neighbouring tiles
    nets = {"VCC": "+5V", "GND": "GND", "~{E}": "GND", "COM": "NB_COM", "S0": "SEL0", "S1": "SEL1", "S2": "SEL2", "S3": "SEL3"}
    for ch in range(16): nets["I%d" % ch] = "N%d_SW" % (ch + 1)
    b.part("U5", "74xx:CD74HC4067M", "74HCT4067 (5 V supply, 3.3 V control)", TSSOP24, 106.68, 228.6, nets)
    b.R("220", "NB_IO", "NB_COM"); b.C("100n", "+5V", "GND"); clamp("NB_IO")
    for ch in range(16): b.R("4k7", "N%d_SW" % (ch + 1), "N%d" % (ch + 1))
    for ch in range(16): b.pad("N%d" % (ch + 1), "neighbour pin, port %d" % (ch + 1), small)
    out = list(CABLE); out[7:] = ["SEL0", "SEL1", "EN1", "EN2", "EN3"]
    b.part("J_OUT", FFC_SYM, "to row 2 (FH12-12S-0.5SH)", FFC, 121.92, 304.8, ffc_nets(out, False))
    row_cells(b)
    x, y = b.place(); b.part("H5", "Mechanical:MountingHole", "M2 screw, head on the back", HOLE, x, y, {})
    b.note("Row 1 board. Fed with 12-24 V; makes 5 V for all rows. Cable positions 1-12: 5V 5V GND GND LED_BUS GND ID_BUS SEL0 SEL1 EN1 EN2 EN3.", 25.4, 345)
    return b

ALL = (bin_board, power_board, feed_board, row_strip, row_main)

if __name__ == "__main__":
    import sys
    here = os.path.dirname(os.path.abspath(__file__))
    chosen = [m for m in ALL if not sys.argv[1:] or m.__name__ in sys.argv[1:]]
    for make in chosen:
        b = make()
        d = os.path.join(here, b.project); os.makedirs(d, exist_ok=True)
        b.write(os.path.join(d, b.project + ".kicad_sch"))
        with open(os.path.join(d, b.project + "_parts.csv"), "w") as f:
            f.write("Reference,Value,Footprint\n")
            for ref, lib_id, value, fp, nets in b.parts:
                if not ref.startswith("#"): f.write('%s,"%s",%s\n' % (ref, value, fp))
        print(b.project, len([p for p in b.parts if not p[0].startswith("#")]), "parts")
    # project-local library tables, so the rule check finds every part
    import re
    for name in [m.__name__ for m in chosen]:
        d = os.path.join(here, name); text = open(os.path.join(d, name + ".kicad_sch")).read()
        for table, key, pat, uri in (("sym-lib-table", "sym_lib_table", r'\(lib_id "([^:"]+):', "/usr/share/kicad/symbols/%s.kicad_sym"),
                                     ("fp-lib-table", "fp_lib_table", r'"Footprint" "([^:"]+):', "/usr/share/kicad/footprints/%s.pretty")):
            libs = sorted(set(re.findall(pat, text)))
            local = lambda n: "${KIPRJMOD}/../lib.pretty" if (n, key) == ("lib", "fp_lib_table") else uri % n
            open(os.path.join(d, table), "w").write("(%s\n  (version 7)\n%s)\n" % (key, "".join(
                '  (lib (name "%s")(type "KiCad")(uri "%s")(options "")(descr ""))\n' % (n, local(n)) for n in libs)))
