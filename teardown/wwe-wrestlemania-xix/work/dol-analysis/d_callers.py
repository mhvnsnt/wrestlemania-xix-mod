#!/usr/bin/env python3
"""Disassemble around the 3 callers of constructor 0x80080170 and sole caller of consumer."""
import sys
sys.path.insert(0, "/home/hatch/workspace/wmxix-mod-testbed/teardown/wwe-wrestlemania-xix/work/dol-analysis")
from dol import disasm, fmt, va_to_file

# callers of 0x80080170: 0x8002d9b4, 0x80045df0, 0x8007c7d8 ; consumer caller 0x800813c4
for va, name in [(0x8002d9b4, "ctor-caller1"), (0x80045df0, "ctor-caller2"),
                 (0x8007c7d8, "ctor-caller3"), (0x800813c4, "consumer-caller")]:
    print(f"===== {name} around {va:#x} =====")
    ins = disasm(va - 0x120, va + 0x40)
    fmt(ins)
    print()
