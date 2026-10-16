#!/usr/bin/env python3
"""Search .text for addi/ori with low16 matching the model-string VAs, and lis/addis high16 0x802d."""
import sys
sys.path.insert(0, "/home/hatch/workspace/wmxix-mod-testbed/teardown/wwe-wrestlemania-xix/work/dol-analysis")
from dol import d, text_offs, text_addrs, text_sizes
from capstone import Cs, CS_ARCH_PPC, CS_MODE_32, CS_MODE_BIG_ENDIAN

md = Cs(CS_ARCH_PPC, CS_MODE_32 | CS_MODE_BIG_ENDIAN)
md.skipdata = True
# string low16s: 0xeb90 (ymg), 0xebac (tex), 0xebc8 (ycg0), 0xebe4 (ycg1)
LO = {0xeb90, 0xebac, 0xebc8, 0xebe4}
n_lis = 0
for off, addr, sz in zip(text_offs, text_addrs, text_sizes):
    if not off or not addr or sz > 0x300000 or not (0x8001e5c0 <= addr < 0x80300000):
        continue
    code = d[off:off+sz]
    for ins in md.disasm(code, addr):
        if ins.mnemonic in ('lis', 'addis'):
            n_lis += 1
            try:
                imm = int(ins.op_str.split(',')[1].strip(), 0) & 0xFFFF
                if imm == 0x802d:
                    print(f"  {ins.address:#x}: {ins.mnemonic} {ins.op_str}")
            except Exception:
                pass
        elif ins.mnemonic in ('addi', 'ori', 'addis'):
            try:
                parts = ins.op_str.split(',')
                imm = int(parts[2].strip(), 0) & 0xFFFF
                if imm in LO:
                    print(f"  LOW16 HIT {ins.address:#x}: {ins.mnemonic} {ins.op_str}")
            except Exception:
                pass
print("total lis/addis:", n_lis)
