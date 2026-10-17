#!/usr/bin/env python3
"""Find lwz 0x60(rY) followed by add (YMG offset->pointer pattern)."""
import sys
sys.path.insert(0, "/home/hatch/workspace/wmxix-mod-testbed/teardown/wwe-wrestlemania-xix/work/dol-analysis")
from dol import d, text_offs, text_addrs, text_sizes
from capstone import Cs, CS_ARCH_PPC, CS_MODE_32, CS_MODE_BIG_ENDIAN
import re

md = Cs(CS_ARCH_PPC, CS_MODE_32 | CS_MODE_BIG_ENDIAN)
md.skipdata = True

for off, addr, sz in zip(text_offs, text_addrs, text_sizes):
    if not off or not addr or not (0x8001e5c0 <= addr < 0x80300000): continue
    if sz > 0x300000: continue
    code = d[off:off+sz]
    insns = [(i.address, i.mnemonic, i.op_str) for i in md.disasm(code, addr)]
    for j in range(len(insns)-1):
        a0,m0,o0 = insns[j]; a1,m1,o1 = insns[j+1]
        if m0=='lwz':
            mm = re.match(r'(r\d+),\s*0x60\((r\d+)\)', o0)
            if mm and m1=='add':
                dst, base = mm.group(1), mm.group(2)
                # check if add uses dst and base
                if dst in o1 and base in o1:
                    print(f"{a0:#x}: {m0} {o0} / {a1:#x}: {m1} {o1}")
