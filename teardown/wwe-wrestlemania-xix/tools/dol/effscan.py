"""Scan text for addis/addi and addis/ori pairs, record effective addresses."""
import sys, struct, json
sys.path.insert(0, '/home/hatch/workspace/agent-ops/worktrees/wrestling-teardown/wwe-wrestlemania-xix/tools/dol')
from dolmap import *
def sext16(x): return x - 0x10000 if x >= 0x8000 else x
pairs = []
for ta in (0x80003100, 0x8001E5C0):
    o = off_of(ta); s = [x[2] for x in SECS if x[0] == ta][0]
    def w(i, o=o): return struct.unpack('>I', raw[o+i:o+i+4])[0]
    for i in range(0, s, 4):
        w0 = w(i)
        if (w0 >> 26) == 15:
            imm = w0 & 0xFFFF; rt = (w0 >> 21) & 31
            base = imm << 16
            for j in range(i+4, min(i+4+96, s), 4):
                w2 = w(j); op = w2 >> 26
                rt2 = (w2 >> 21) & 31; ra2 = (w2 >> 16) & 31
                if op == 14 and ra2 == rt:
                    pairs.append((ta+i, (w2>>21)&31, (base + sext16(w2 & 0xFFFF)) & 0xFFFFFFFF)); break
                if op == 24 and ra2 == rt:
                    pairs.append((ta+i, (w2>>21)&31, (base | (w2 & 0xFFFF)) & 0xFFFFFFFF)); break
json.dump(pairs, open('/home/hatch/workspace/agent-ops/worktrees/wrestling-teardown/wwe-wrestlemania-xix/work/effpairs.json', 'w'))
print('total eff pairs:', len(pairs))
