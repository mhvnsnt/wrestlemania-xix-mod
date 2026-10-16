#!/usr/bin/env python3
"""Find functions that read YMG header offsets 0x10/0x5c/0x60 from the same base register.
These are candidate YMG parser/loaders."""
import sys
sys.path.insert(0, "/home/hatch/workspace/wmxix-mod-testbed/teardown/wwe-wrestlemania-xix/work/dol-analysis")
from dol import d, text_offs, text_addrs, text_sizes
from capstone import Cs, CS_ARCH_PPC, CS_MODE_32, CS_MODE_BIG_ENDIAN
import re

md = Cs(CS_ARCH_PPC, CS_MODE_32 | CS_MODE_BIG_ENDIAN)
md.skipdata = True

# gather all load instructions with their VA, mnemonic, base reg, offset
# We'll chunk .text into functions by prologue (stwu r1, -X(r1)) as approximate boundaries
LOAD = ('lwz','lhz','lbz','lha','lwzx','lhax')

cands = {}  # func_va -> list of (va, mnem, base, off)
for off, addr, sz in zip(text_offs, text_addrs, text_sizes):
    if not off or not addr or sz > 0x300000 or addr < 0x80010000 or addr > 0x80400000:
        continue
    # only scan the main .text (0x8001e5c0..)
    if not (0x8001e5c0 <= addr < 0x80300000):
        continue
    code = d[off:off+sz]
    insns = [(i.address, i.mnemonic, i.op_str) for i in md.disasm(code, addr)]
    # find function starts via stwu r1
    starts = [i for i,(a,m,o) in enumerate(insns) if m=='stwu' and o.startswith('r1, -')]
    starts.append(len(insns))
    for s in range(len(starts)-1):
        fva = insns[starts[s]][0]
        body = insns[starts[s]:starts[s+1]]
        seen = []
        for (a,m,o) in body:
            if m in ('lwz','lhz','lbz','lha'):
                mm = re.match(r'r\d+,\s*(-?0x[0-9a-f]+|-?\d+)\((r\d+)\)', o)
                if mm:
                    disp = int(mm.group(1),0); base = mm.group(2)
                    if disp in (0x10,0x5c,0x60,0x54,0x14,0x18,0x1c,0x24,0x38):
                        seen.append((a,m,base,disp))
        # check if same base used for 0x5c and 0x60 (or 0x10 and 0x5c)
        bases_5c = {b for _,_,b,dp in seen if dp==0x5c}
        bases_60 = {b for _,_,b,dp in seen if dp==0x60}
        bases_10 = {b for _,_,b,dp in seen if dp==0x10}
        hit = (bases_5c & bases_60) or (bases_10 & bases_5c) or (bases_10 & bases_60)
        if hit:
            cands[fva] = (seen, hit)

print(len(cands), "candidate functions")
for fva,(seen,hit) in sorted(cands.items())[:40]:
    print(f"\nfunc {fva:#x} shared base {hit}:")
    for (a,m,b,dp) in seen[:12]:
        print(f"    {a:#x}: {m} base={b} off={dp:#x}")
