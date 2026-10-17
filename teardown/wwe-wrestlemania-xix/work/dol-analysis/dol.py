#!/usr/bin/env python3
"""DOL harness: parse main.dol, disassemble ranges with capstone (PPC32 BE)."""
import struct
from capstone import Cs, CS_ARCH_PPC, CS_MODE_32, CS_MODE_BIG_ENDIAN

DOL = "/home/hatch/workspace/wmxix-mod-testbed/teardown/wwe-wrestlemania-xix/work/dol-re/main.dol"
_d = open(DOL, "rb").read()
d = _d

def u32(o): return struct.unpack(">I", _d[o:o+4])[0]

text_offs = [u32(0x00 + 4*i) for i in range(18)]
text_addrs = [u32(0x48 + 4*i) for i in range(18)]
text_sizes = [u32(0x90 + 4*i) for i in range(18)]

def va_to_file(va):
    for off, addr, sz in zip(text_offs, text_addrs, text_sizes):
        if addr and addr <= va < addr + sz:
            return off + (va - addr)
    return None

def file_to_va(fo):
    for off, addr, sz in zip(text_offs, text_addrs, text_sizes):
        if off and off <= fo < off + sz:
            return addr + (fo - off)
    return None

_md = Cs(CS_ARCH_PPC, CS_MODE_32 | CS_MODE_BIG_ENDIAN)
_md.skipdata = True  # don't stop on paired-single/data words

def disasm(va_start, va_end):
    fo = va_to_file(va_start)
    assert fo is not None, f"VA {va_start:#x} not in any section"
    code = _d[fo:fo + (va_end - va_start)]
    return [(i.address, i.mnemonic, i.op_str) for i in _md.disasm(code, va_start)]

def fmt(insns, highlight=None):
    for a, m, o in insns:
        mark = " >>" if highlight and a == highlight else ""
        print(f"  {a:08x}: {m:10s} {o}{mark}")

def save(insns, path):
    with open(path, 'w') as f:
        for a, m, o in insns:
            f.write(f"  {a:08x}: {m:10s} {o}\n")
