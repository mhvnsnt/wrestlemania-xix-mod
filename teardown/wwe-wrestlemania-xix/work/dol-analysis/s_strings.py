#!/usr/bin/env python3
"""Find .text references to model path strings via addis/ori or lis/addi pairs."""
import sys
sys.path.insert(0, "/home/hatch/workspace/wmxix-mod-testbed/teardown/wwe-wrestlemania-xix/work/dol-analysis")
from dol import d, file_to_va, text_offs, text_addrs, text_sizes
from capstone import Cs, CS_ARCH_PPC, CS_MODE_32, CS_MODE_BIG_ENDIAN

targets = {0x2dbb90: 'ymg', 0x2dbbac: 'tex', 0x2dbbc8: 'ycg0', 0x2dbbe4: 'ycg1'}
sva = {fo: file_to_va(fo) for fo in targets}
print("string VAs:", {hex(k): (hex(v) if v else None) for k, v in sva.items()})

md = Cs(CS_ARCH_PPC, CS_MODE_32 | CS_MODE_BIG_ENDIAN)
for off, addr, sz in zip(text_offs, text_addrs, text_sizes):
    if not off or not addr or sz > 0x300000:
        continue
    code = d[off:off+sz]
    insns = list(md.disasm(code, addr))
    for j in range(len(insns)-1):
        a, b = insns[j], insns[j+1]
        if a.mnemonic in ('lis', 'addis') and b.mnemonic in ('ori', 'addi'):
            try:
                pa = a.op_str.split(','); pb = b.op_str.split(',')
                if pb[0].strip() != pa[0].strip():
                    continue
                hai = int(pa[1].strip(), 0); loi = int(pb[2].strip(), 0)
                va = ((hai << 16) + (loi if loi < 0x8000 else loi - 0x10000)) & 0xFFFFFFFF
                for fo, sv in sva.items():
                    if sv and abs(va - sv) < 0x400:
                        print(f"  text VA {a.address:#x}: {a.mnemonic} {a.op_str} / {b.mnemonic} {b.op_str} -> {va:#x} ({targets[fo]}+{va-sv:#x})")
            except Exception:
                pass
print("done")
