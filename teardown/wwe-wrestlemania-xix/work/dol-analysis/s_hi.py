#!/usr/bin/env python3
"""Scan .text for addis/lis with high16 == 0x802d (data section base) and list nearby string refs."""
import sys
sys.path.insert(0, "/home/hatch/workspace/wmxix-mod-testbed/teardown/wwe-wrestlemania-xix/work/dol-analysis")
from dol import d, file_to_va, text_offs, text_addrs, text_sizes
from capstone import Cs, CS_ARCH_PPC, CS_MODE_32, CS_MODE_BIG_ENDIAN

md = Cs(CS_ARCH_PPC, CS_MODE_32 | CS_MODE_BIG_ENDIAN)
hits = []
for off, addr, sz in zip(text_offs, text_addrs, text_sizes):
    if not off or not addr or sz > 0x300000:
        continue
    code = d[off:off+sz]
    for ins in md.disasm(code, addr):
        if ins.mnemonic in ('lis', 'addis'):
            try:
                imm = int(ins.op_str.split(',')[1].strip(), 0)
                if imm == 0x802d or imm == -0x7fd3:  # 0x802d / sign-extended
                    hits.append((ins.address, ins.mnemonic, ins.op_str))
            except Exception:
                pass
print(len(hits), "hits with high16 0x802d")
for h in hits[:60]:
    print(f"  {h[0]:#x}: {h[1]} {h[2]}")
