#!/usr/bin/env python3
"""Find addi rX,rX,0x30 outside the constructor (sub-record writer candidates)."""
import sys
sys.path.insert(0, "/home/hatch/workspace/wmxix-mod-testbed/teardown/wwe-wrestlemania-xix/work/dol-analysis")
from dol import d, text_offs, text_addrs, text_sizes
from capstone import Cs, CS_ARCH_PPC, CS_MODE_32, CS_MODE_BIG_ENDIAN
import re
md = Cs(CS_ARCH_PPC, CS_MODE_32 | CS_MODE_BIG_ENDIAN); md.skipdata=True
for off, addr, sz in zip(text_offs, text_addrs, text_sizes):
    if not off or not addr or not (0x8001e5c0 <= addr < 0x80300000): continue
    if sz > 0x300000: continue
    code = d[off:off+sz]
    for ins in md.disasm(code, addr):
        if ins.mnemonic=='addi':
            m=re.match(r'(r\d+),\s*\1,\s*0x30$', ins.op_str)
            if m and not (0x800811e0 <= ins.address < 0x80081400):
                print(f"{ins.address:#x}: {ins.mnemonic} {ins.op_str}")
