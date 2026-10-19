"""Shared DOL layout: main.dol sections with load addresses."""
import json, struct
DOL = '/home/hatch/workspace/agent-ops/worktrees/wrestling-teardown/wwe-wrestlemania-xix/work/main.dol'
M = json.load(open(DOL + '.map'))
SECS = sorted([(a, o, s) for o, a, s in M['text']] + [(a, o, s) for o, a, s in M['data']])
raw = open(DOL, 'rb').read()
def off_of(addr):
    for a, o, s in SECS:
        if a <= addr < a + s:
            return o + (addr - a)
    return None
def addr_of(off):
    for a, o, s in SECS:
        if o <= off < o + s:
            return a + (off - o)
    return None
def read_at(addr, n):
    o = off_of(addr)
    return raw[o:o+n] if o is not None else b''
def find_all(pat):
    out = []
    i = raw.find(pat)
    while i >= 0:
        out.append((i, addr_of(i)))
        i = raw.find(pat, i+1)
    return out
def dis(start, nbytes, limit=200):
    from capstone import Cs, CS_ARCH_PPC, CS_MODE_BIG_ENDIAN
    cs = Cs(CS_ARCH_PPC, CS_MODE_BIG_ENDIAN)
    code = read_at(start, nbytes)
    out = []
    for ins in cs.disasm(code, start):
        out.append((ins.address, ins.mnemonic, ins.op_str, ins.bytes.hex()))
        if len(out) >= limit: break
    return out
