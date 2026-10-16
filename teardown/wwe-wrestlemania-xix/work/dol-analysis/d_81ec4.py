#!/usr/bin/env python3
"""Disassemble 0x80081ec4 (called just before ctor at caller1) and find its end."""
import sys
sys.path.insert(0, "/home/hatch/workspace/wmxix-mod-testbed/teardown/wwe-wrestlemania-xix/work/dol-analysis")
from dol import disasm, save
# disassemble generously; find blr
ins = disasm(0x80081ec4, 0x80083000)
# trim at first blr after start (function end)
end = None
for i, (a, m, o) in enumerate(ins):
    if m == 'blr' and a > 0x80081ec4 + 16:
        end = i + 1
        break
ins = ins[:end]
print(f"{len(ins)} insns, ends at {ins[-1][0]:#x}")
save(ins, "/home/hatch/workspace/wmxix-mod-testbed/teardown/wwe-wrestlemania-xix/work/dol-analysis/func_80081ec4.txt")
