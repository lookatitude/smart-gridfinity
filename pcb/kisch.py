#!/usr/bin/env python3
"""Minimal KiCad schematic writer. Parts are taken from the installed KiCad symbol
libraries and connected by net labels placed on the pin ends (no drawn wires), so the
result is electrically complete and can be rule-checked with `kicad-cli sch erc`."""
import uuid, os

SYMDIR = "/usr/share/kicad/symbols"

class Q(str):
    """A quoted string atom."""

def parse(text):
    pos, n = 0, len(text)
    def node():
        nonlocal pos
        out = []
        while pos < n:
            c = text[pos]
            if c in " \t\r\n": pos += 1
            elif c == "(": pos += 1; out.append(node())
            elif c == ")": pos += 1; return out
            elif c == '"':
                pos += 1; buf = []
                while text[pos] != '"':
                    if text[pos] == "\\": buf.append(text[pos:pos + 2]); pos += 2
                    else: buf.append(text[pos]); pos += 1
                pos += 1; out.append(Q("".join(buf)))
            else:
                j = pos
                while text[j] not in " \t\r\n()": j += 1
                out.append(text[pos:j]); pos = j
        return out
    return node()[0]

def dump(x, depth=0):
    if isinstance(x, Q): return '"%s"' % x
    if isinstance(x, str): return x
    inner = " ".join(dump(c, depth + 1) for c in x)
    return ("\n" + "\t" * depth if depth else "") + "(" + inner + ")"

_libs = {}
def lib(name):
    if name not in _libs:
        _libs[name] = parse(open(os.path.join(SYMDIR, name + ".kicad_sym")).read())
    return _libs[name]

def find(tree, key, name=None):
    return [c for c in tree if isinstance(c, list) and c and c[0] == key and (name is None or (len(c) > 1 and c[1] == name))]

def load_symbol(lib_id):
    """Return the flattened symbol tree named 'Lib:Name' (parents of `extends` merged in)."""
    libname, name = lib_id.split(":")
    sym = find(lib(libname), "symbol", name)[0]
    ext = find(sym, "extends")
    if ext:
        parent = load_symbol(libname + ":" + ext[0][1])
        props = {p[1]: p for p in find(sym, "property")}
        out = []
        for c in parent:
            if isinstance(c, list) and c and c[0] == "property" and c[1] in props: out.append(props.pop(c[1]))
            elif isinstance(c, list) and c and c[0] == "symbol":
                out.append(["symbol", Q(name + c[1][len(ext[0][1]):])] + c[2:])
            else: out.append(c)
        out[1] = Q(lib_id)
        return out
    return ["symbol", Q(lib_id)] + sym[2:]

def pins_of(sym, unit=1):
    """{number: (x, y, name, type)} for one unit (and the shared unit 0)."""
    pins = {}
    for sub in find(sym, "symbol"):
        u = sub[1].rsplit("_", 2)[1]
        if u not in ("0", str(unit)): continue
        for p in find(sub, "pin"):
            at = find(p, "at")[0]
            pins[str(find(p, "number")[0][1])] = (float(at[1]), float(at[2]), str(find(p, "name")[0][1]), p[1])
    return pins

def uid(): return Q(str(uuid.uuid4()))
def fx(hide=False):
    e = ["effects", ["font", ["size", "1.27", "1.27"]]]
    return e + [["hide", "yes"]] if hide else e

class Schematic:
    def __init__(self, project, title):
        self.project, self.title, self.root = project, title, uid()
        self.libsyms, self.items, self.parts = {}, [], []

    def part(self, ref, lib_id, value, footprint, x, y, nets, unit=1):
        """nets: {pin number or pin name: net name, or None for 'not connected'}.
        A part with several units (gates) is placed once per unit, with the same ref."""
        if lib_id not in self.libsyms: self.libsyms[lib_id] = load_symbol(lib_id)
        pins = pins_of(self.libsyms[lib_id], unit)
        byname = {}
        for num, (_, _, pname, _) in pins.items(): byname.setdefault(pname, []).append(num)
        resolved = {}
        for key, net in nets.items():
            nums = [key] if key in pins else byname.get(key)
            assert nums, "%s: no pin %s (have %s)" % (ref, key, sorted(byname))
            for num in nums: resolved[num] = net
        missing = set(pins) - set(resolved)
        assert not missing, "%s: pins not assigned: %s" % (ref, sorted((m, pins[m][2]) for m in missing))
        inst = ["symbol", ["lib_id", Q(lib_id)], ["at", x, y, 0], ["unit", unit], ["exclude_from_sim", "no"],
                ["in_bom", "yes"], ["on_board", "yes"], ["dnp", "no"], ["uuid", uid()],
                ["property", Q("Reference"), Q(ref), ["at", x, y - 2.54, 0], fx()],
                ["property", Q("Value"), Q(value), ["at", x, y + 2.54, 0], fx()],
                ["property", Q("Footprint"), Q(footprint), ["at", x, y, 0], fx(True)]]
        for num in pins: inst.append(["pin", Q(num), ["uuid", uid()]])
        inst.append(["instances", ["project", Q(self.project), ["path", Q("/" + self.root),
                     ["reference", Q(ref)], ["unit", unit]]]])
        self.items.append(inst)
        for num, net in resolved.items():
            px, py = round(x + pins[num][0], 4), round(y - pins[num][1], 4)
            if net is None: self.items.append(["no_connect", ["at", px, py], ["uuid", uid()]])
            else: self.items.append(["label", Q(net), ["at", px, py, 0], fx(), ["uuid", uid()]])
        mine = {n: resolved[n] for n in pins}
        for i, p in enumerate(self.parts):           # a further unit of a part already placed
            if p[0] == ref: self.parts[i] = p[:4] + ({**p[4], **mine},); return
        self.parts.append((ref, lib_id, value, footprint, mine))

    def note(self, text, x, y):
        self.items.append(["text", Q(text), ["exclude_from_sim", "no"], ["at", x, y, 0],
                           ["effects", ["font", ["size", "2", "2"]], ["justify", "left"]], ["uuid", uid()]])

    def write(self, path):
        tree = ["kicad_sch", ["version", "20250114"], ["generator", Q("eeschema")], ["generator_version", Q("9.0")],
                ["uuid", self.root], ["paper", Q("A3")],
                ["title_block", ["title", Q(self.title)]],
                ["lib_symbols"] + list(self.libsyms.values())] + self.items + [
                ["sheet_instances", ["path", Q("/"), ["page", Q("1")]]], ["embedded_fonts", "no"]]
        open(path, "w").write(dump([str(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else v for v in tree]
                                   if False else _stringify(tree)) + "\n")

def _stringify(x):
    if isinstance(x, list): return [_stringify(c) for c in x]
    if isinstance(x, Q): return x
    return str(x)

if __name__ == "__main__":
    import sys
    for lib_id in sys.argv[1:]:
        p = pins_of(load_symbol(lib_id))
        print(lib_id, len(p), "pins")
        for num in sorted(p, key=lambda s: (len(s), s)): print("   %3s %-12s %-14s at %s,%s" % (num, p[num][2], p[num][3], p[num][0], p[num][1]))
