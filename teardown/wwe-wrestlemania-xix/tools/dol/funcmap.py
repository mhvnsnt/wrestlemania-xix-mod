"""Function boundary detection for DOL text sections."""
import sys, struct
sys.path.insert(0, '/home/hatch/workspace/agent-ops/worktrees/wrestling-teardown/wwe-wrestlemania-xix/tools/dol')
from dolmap import *
def w32(addr):
    o = off_of(addr)
    return struct.unpack('>I', raw[o:o+4])[0] if o is not None else 0
def find_prologues(ta):
    s = [x[2] for x in SECS if x[0] == ta][0]
    out = []
    for i in range(0, s, 4):
        w = struct.unpack('>I', raw[off_of(ta)+i:off_of(ta)+i+4])[0]
        if (w >> 26) == 37 and ((w >> 21) & 31) == 1 and ((w >> 16) & 31) == 1:
            d = w & 0xFFFF
            if d >= 0x8000:  # stwu r1, -N(r1)
                out.append(ta + i)
    return out
def func_range(ta, addr):
    """approx function containing addr: prev prologue .. next blr"""
    pros = find_prologues(ta)
    start = max([p for p in pros if p <= addr], default=addr)
    o = off_of(addr); end = addr
    for i in range(0, 0x8000, 4):
        a = addr + i
        w = w32(a)
        if w == 0x4E800020:  # blr
            end = a + 4; break
        # bail at next prologue
        if a > addr and (w >> 26) == 37 and ((w >> 21) & 31) == 1 and ((w >> 16) & 31) == 1 and (w & 0xFFFF) >= 0x8000:
            end = a; break
    return start, end
