#!/usr/bin/env python3
"""ngspice checks for the no-radio bin design: are the ID line and the LED data line
within their logic limits after the series resistor, the switch chip of the row, the spring
contact and the bin's own parts? And what happens if a signal pin touches the 5 V ring?"""
import subprocess, tempfile, os, re

def spice(text, wanted):
    with tempfile.NamedTemporaryFile("w", suffix=".cir", delete=False) as f:
        f.write(text); path = f.name
    out = subprocess.run(["ngspice", "-b", path], capture_output=True, text=True).stdout
    os.unlink(path)
    vals = {}
    for w in wanted:
        m = re.search(r"^%s\s*=\s*([-+0-9.eE]+)" % re.escape(w), out, re.M | re.I)
        assert m, "no value for %s\n%s" % (w, out[-800:])
        vals[w] = float(m.group(1))
    return vals

RSER, RMUX, RCONTACT = 220, 225, 0.5      # tile series resistor, switch chip (74HCT4052 worst case over temperature), pin on ring
ok = True
def check(label, value, unit, good):
    global ok
    ok &= good
    print("  %-58s %8.3g %-3s %s" % (label, value, unit, "ok" if good else "FAIL"))

print("ID line (1-Wire), 2.2k pull-up to 3.3 V at the first-row board, 1 nF at the bin")
net = """id line
V33 v33 0 3.3
Rpu v33 mcu 2.2k
Rs mcu com %g
Rm com pin %g
Rc pin id %g
Cid id 0 1n
* the chip pulls low through about 100 ohm from 10 us to 60 us
S1 id 0 ctl 0 sw
Vctl ctl 0 PULSE(0 1 10u 100n 100n 50u 1)
.model sw SW(Ron=100 Roff=10Meg Vt=0.5)
.tran 100n 120u
.meas tran vlow FIND v(mcu) AT=50u
.meas tran vhigh FIND v(mcu) AT=110u
.meas tran trise TRIG v(mcu) VAL=0.9 RISE=1 TARG v(mcu) VAL=2.4 RISE=1
.end
""" % (RSER, RMUX, RCONTACT)
v = spice(net, ["vlow", "vhigh", "trise"])
check("low level seen by the tile when the chip answers 0", v["vlow"], "V", v["vlow"] < 0.8)
check("high level", v["vhigh"], "V", v["vhigh"] > 2.6)
check("rise time (the tile samples 15 us after the edge)", v["trise"] * 1e6, "us", v["trise"] < 8e-6)

print("LED data line, 3.3 V from the first-row board, 100 ohm + 100k pull-down + 120 pF at the bin")
net = """led data
Vd mcu 0 PULSE(0 3.3 100n 5n 5n 400n 1250n)
Rs mcu com %g
Rm com pin %g
Rc pin ring %g
Rb ring din 100
Rpd din 0 100k
Cd din 0 120p
.tran 2n 2.5u
.meas tran vhigh MAX v(din)
.meas tran trise TRIG v(din) VAL=0.33 RISE=1 TARG v(din) VAL=2.7 RISE=1
.meas tran width TRIG v(din) VAL=2.7 RISE=1 TARG v(din) VAL=2.7 FALL=1
.end
""" % (RSER, RMUX, RCONTACT)
v = spice(net, ["vhigh", "trise", "width"])
check("high level at the LED (it needs 2.7 V or more)", v["vhigh"], "V", v["vhigh"] > 2.9)
check("rise time to 2.7 V", v["trise"] * 1e9, "ns", v["trise"] < 150e-9)
check("width of a 400 ns '0' pulse above 2.7 V (LED accepts 220-380)", v["width"] * 1e9, "ns", 220e-9 < v["width"] < 380e-9)

print("Fault: a signal pin touches the 5 V ring while a bin is being seated")
net = """5v on signal pin
V5 pin 0 5
V33 v33 0 3.3
Rm pin com 70
Rs com mcu %g
D1 mcu v33 sch
.model sch D(Is=2u N=1.05 Rs=1)
.op
.control
op
let iclamp = (v(com)-v(mcu))/%g
print iclamp v(mcu)
.endc
.end
""" % (RSER, RSER)
v = spice(net, ["iclamp", "v(mcu)"])
check("current into the clamp diode", v["iclamp"] * 1000, "mA", v["iclamp"] < 0.02)
check("voltage on the processor pin (limit 3.6 V)", v["v(mcu)"], "V", v["v(mcu)"] < 3.6)

print("Neighbour pin between two tiles: 100k pull-ups, 4.7k series per port on both sides")
net = """neighbour pin
V33a v33a 0 3.3
V33b v33b 0 3.3
Rpa v33a mcua 100k
Rsa mcua coma %g
Rma coma swa %g
Rna swa pin 4.7k
Rnb pin swb 4.7k
Rmb swb comb %g
Rsb comb mcub %g
Rpb v33b mcub 100k
Cpin pin 0 100p
* tile A talks: its processor pin pulls low through about 35 ohm from 20 us
S1 mcua 0 ctl 0 sw
Vctl ctl 0 PULSE(0 1 20u 100n 100n 104u 1)
.model sw SW(Ron=35 Roff=10Meg Vt=0.5)
.tran 200n 250u
.meas tran vlow FIND v(mcub) AT=100u
.meas tran vhigh FIND v(mcub) AT=240u
.meas tran trise TRIG v(mcub) VAL=0.8 RISE=1 TARG v(mcub) VAL=2.5 RISE=1
.end
""" % (RSER, RMUX, RMUX, RSER)
v = spice(net, ["vlow", "vhigh", "trise"])
check("low level heard by the other tile", v["vlow"], "V", v["vlow"] < 0.8)
check("high level", v["vhigh"], "V", v["vhigh"] > 2.6)
check("rise time (one bit at 9600 baud is 104 us)", v["trise"] * 1e6, "us", v["trise"] < 30e-6)

print("Fault: the neighbour pin touches the 24 V feed pin in an edge connector")
net = """24 V on neighbour pin
V24 pin 0 24
V5 v5 0 5
Rn pin sw 4.7k
* the switch's own input diode conducts into its 5 V supply
D1 sw v5 dsw
.model dsw D(Is=1n N=1.8 Rs=20)
.op
.control
op
let ifault = (v(pin)-v(sw))/4.7k
let pres = ifault*ifault*4.7k
print ifault pres
.endc
.end
"""
v = spice(net, ["ifault", "pres"])
check("current into the switch's input diode (rated 20 mA)", v["ifault"] * 1000, "mA", v["ifault"] < 0.015)
check("heat in the 4.7k resistor (0603 part is rated 0.1 W)", v["pres"], "W", v["pres"] < 0.1)

print("PASS" if ok else "FAIL"); raise SystemExit(0 if ok else 1)
