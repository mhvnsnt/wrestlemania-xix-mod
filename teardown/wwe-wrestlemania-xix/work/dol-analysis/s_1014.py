#!/usr/bin/env python3
"""Find functions reading YMG header 0x10 (bone count) and 0x14 (skeleton)."""
import sys
sys.path.insert(0, "/home/hatch/workspace/wmxix-mod-testbed/teardown/wwe-wrestlemania-xix/work/dol-analysis")
from dol import d, text_offs, text_addrs, text_sizes
from capstone import Cs, CS_ARCH_PPC, CS_MODE_32, CS_MODE_BIG_ENDIAN
import re

md = Cs(CS_ARCH_PPC, CS_MODE_32 | CS_MODE_BIG_ENDIAN)
md.skipdata = True

hits10, hits14 = [], []
for off, addr, sz in zip(text_offs, text_addrs, text_sizes):
    if not off or not addr or not (0x8001e5c0 <= addr < 0x80300000): continue
    if sz > 0x300000: continue
    code = d[off:off+sz]
    for ins in md.disasm(code, addr):
        if ins.mnemonic in ('lwz','lhz'):
            m = re.match(r'r\d+,\s*(-?0x[0-9a-f]+|-?\d+)\((r\d+)\)', ins.op_str)
            if m:
                disp = int(m.group(1), 0); base = m.group(2)
                if disp == 0x10: hits10.append((ins.address, base))
                if disp == 0x14: hits14.append((ins.address, base))

print(len(hits10), "hits for 0x10,", len(hits14), "for 0x14")
# find addresses where both appear within 0x200 bytes with same base
for a10, b10 in hits10:
    for a14, b14 in hits14:
        if b10 == b14 and abs(a10 - a14) < 0x300 and 0x80070000 <= a10 < 0x800a0000:
            print(f"  0x10@{a10:#x} 0x14@{a14:#x} base={b10}")
            break
