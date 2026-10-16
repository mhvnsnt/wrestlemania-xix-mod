#!/usr/bin/env python3
"""Find lwz with offsets 0x5c/0x60/0x10 in .text, group by nearby context."""
import sys
sys.path.insert(0, "/home/hatch/workspace/wmxix-mod-testbed/teardown/wwe-wrestlemania-xix/work/dol-analysis")
from dol import d, text_offs, text_addrs, text_sizes
from capstone import Cs, CS_ARCH_PPC, CS_MODE_32, CS_MODE_BIG_ENDIAN
import re

md = Cs(CS_ARCH_PPC, CS_MODE_32 | CS_MODE_BIG_ENDIAN)
md.skipdata = True

hits = []
for off, addr, sz in zip(text_offs, text_addrs, text_sizes):
    if not off or not addr or not (0x8001e5c0 <= addr < 0x80300000):
        continue
    if sz > 0x300000: continue
    code = d[off:off+sz]
    for ins in md.disasm(code, addr):
        if ins.mnemonic in ('lwz','lhz','lbz'):
            m = re.match(r'r\d+,\s*(-?0x[0-9a-f]+|-?\d+)\((r\d+)\)', ins.op_str)
            if m:
                disp = int(m.group(1), 0)
                if disp in (0x5c, 0x60):
                    hits.append((ins.address, ins.mnemonic, ins.op_str))

print(len(hits), "hits for 0x5c/0x60")
# print those in the 0x8007xxxx-0x8009xxxx range (near consumer/ctor)
for a, m, o in hits:
    if 0x80070000 <= a < 0x800a0000:
        print(f"  {a:#x}: {m} {o}")
