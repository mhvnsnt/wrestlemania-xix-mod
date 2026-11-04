"""Experiment A scanner: find the 16-byte runtime draw-record writer + 256-byte bonemap init
in the YOBJ parser region 0x80072000-0x80074000.

Record writer signature: stores to a common base at offsets
  stb +0, +1, +2 (bone bytes), stb +3 (type), stw +4 (count),
  stw +8 (aux), stb +12 (count), stb +13 (flag)
within a tight instruction window (~40 insns).

Bonemap signature: 256-byte zero-init loop (mtctr 0x100 / li rX,0x100 then
stb/stw loop), or a call into a memset with size 0x100.

Usage: python3 tools/dol/recwriter_scan.py
"""
import sys, struct
sys.path.insert(0, '/home/hatch/workspace/agent-ops/worktrees/wrestling-teardown/wwe-wrestlemania-xix/tools/dol')
from dolmap import *
from capstone import Cs, CS_ARCH_PPC, CS_MODE_32, CS_MODE_BIG_ENDIAN

LO, HI = 0x80072000, 0x80074000

def dis_range(lo, hi):
    md = Cs(CS_ARCH_PPC, CS_MODE_32 | CS_MODE_BIG_ENDIAN)
    md.detail = True
    buf = bytearray()
    for a in range(lo, hi, 4):
        o = off_of(a)
        buf += raw[o:o+4] if o is not None else b'\0\0\0\0'
    return list(md.disasm(bytes(buf), lo))

def imm(insn):
    """immediate displacement of mem operand, if any"""
    try:
        for op in insn.operands:
            if op.type == 3:  # PPC_OP_MEM in this capstone build
                return op.mem.disp
    except Exception:
        pass
    return None

def basereg(insn):
    try:
        for op in insn.operands:
            if op.type == 3:
                return op.mem.base
    except Exception:
        pass
    return None

def main():
    insns = dis_range(LO, HI)
    print(f"disassembled {len(insns)} insns in [{LO:#x},{HI:#x})")

    # ---- pass 1: find candidate record writers ----
    # collect (idx, disp, base, mnemonic) for store insns
    stores = []
    for i, ins in enumerate(insns):
        m = ins.mnemonic
        if m in ('stb', 'sth', 'stw', 'stbu'):
            d = imm(ins)
            b = basereg(ins)
            if d is not None and b is not None:
                stores.append((i, d, b, m, ins.address))

    print("\n== candidate 16-byte record writers ==")
    print("windowed store-cluster analysis: base regs with stores at offsets 0..15")
    hits = []
    # sliding window of 60 insns over the store list
    for s in range(len(stores)):
        i0 = stores[s][0]
        base = stores[s][2]
        cluster = {}
        for j in range(s, len(stores)):
            if stores[j][0] - i0 > 80:
                break
            if stores[j][2] != base:
                continue
            d = stores[j][3] if False else stores[j][1]
            cluster.setdefault(d, []).append(stores[j])
        offs = sorted(cluster)
        # record layout: bytes at 0,1,2,3 ; word at 4 ; word at 8 ; bytes at 12,13
        want = {0: {'stb'}, 1: {'stb'}, 2: {'stb'}, 3: {'stb'},
                4: {'stw'}, 8: {'stw'}, 12: {'stb'}, 13: {'stb'}}
        score = 0
        for d, ms in want.items():
            if d in cluster and any(c[3] in ms for c in cluster[d]):
                score += 1
        if score >= 5 and len(cluster) >= 5:
            hits.append((score, i0, base, insns[i0].address, sorted(cluster.items())))
    hits.sort(reverse=True)
    for score, i0, base, addr, cl in hits[:20]:
        regs = {ins.reg_name(b) for b in [base]}
        print(f"\nscore {score}/8 @ insn {i0} addr {addr:#x} base=r{base}")
        for d, cs in cl:
            for (_, _, _, m, a) in cs:
                print(f"   {a:#x}  {m} +{d}")
    if not hits:
        print("(no store cluster matching record layout found)")

    # ---- pass 2: 256-byte zero-init loops (bonemap candidate) ----
    print("\n== 256-byte memset/zero-init candidates ==")
    for i, ins in enumerate(insns):
        if ins.mnemonic == 'mtctr':
            # look back for li rX,0x100 within 12 insns
            for k in range(max(0, i-12), i):
                p = insns[k]
                if p.mnemonic == 'li':
                    try:
                        immv = int(p.op_str.split(',')[1].strip(), 0)
                    except Exception:
                        continue
                    if immv == 0x100:
                        print(f"{p.address:#x}: {p.mnemonic} {p.op_str}  ...  {ins.address:#x}: mtctr (ctr=0x100 loop; bonemap-init candidate)")
    # ---- pass 3: calls with r5=0x100 (memset arg) ----
    print("\n== bl with li r5,0x100 within 20 insns before (memset size arg) ==")
    for i, ins in enumerate(insns):
        if ins.mnemonic == 'bl':
            for k in range(max(0, i-20), i):
                p = insns[k]
                if p.mnemonic == 'li' and p.op_str.startswith('r5,'):
                    try:
                        immv = int(p.op_str.split(',')[1].strip(), 0)
                    except Exception:
                        continue
                    if immv == 0x100:
                        print(f"{p.address:#x}: li r5,0x100  ->  {ins.address:#x}: bl {ins.op_str}")

if __name__ == '__main__':
    main()
