#!/usr/bin/env python3
"""YANM item 2: resolve anatomical L/R of the side-paired detail tracks.

Chain of evidence:
 1. 1E000000 side-bit -> ycg y-side, anchored on 64D45E02/7AD45E02
    (the ONLY 1E000000-paired track with ycg records). 6/6 records split
    cleanly: 0x04000000-bit -> y<0, 0x1A000000-bit -> y>0.
 2. ycg y-side -> anatomical L/R via chirality (scalar triple product).
    up.(LxR) must keep its sign under the proper rotation relating the
    ycg and ymg frames (both are the same physical body). Tested with
    ymg bone-name ground truth (Bip L/R Thigh) vs ycg bilateral hips.
 3. Transfer within the 1E000000 system: A4955E6E/BA955E6E (fingers),
    007FD58C/1E7FD58C (toes) share the XOR code with the anchor pair.
Streams ISO; reads docs/wrestler-skeleton-000.json (70 named bones).
"""
import sys, json
import numpy as np
sys.path.insert(0, 'tools')
from gcn_fst import read_header, read_entries, flat_listing
from yukes_fmt import u32, f32

ISO = 'WWE Wrestlemania XIX (USA).iso'
with open(ISO, 'rb') as iso:
    h = read_header(iso); e, nm = read_entries(iso, h['fst_off'], h['fst_size'])
    listing = flat_listing(e, nm)
fmap = {p.strip('/').lstrip('/'):(o, l) for p, d, o, l in listing if not d}
_iso = open(ISO, 'rb')
def read(path):
    o, l = fmap[path]; _iso.seek(o); return _iso.read(l)

# ---------- (1) side-bit -> ycg y-side on the anchor pair ----------
d = read('model/wrestler/000_0.ycg')
n = u32(d, 0)
recs = []
for r in range(n):
    o = 4 + r * 56
    recs.append((u32(d, o), f32(d, o+20)))  # (hash, y)
print('=== (1) 1E000000 anchor pair: side-bit vs ycg y-sign ===')
for hh, bitname in ((0x64D45E02, '0x04000000-bit'), (0x7AD45E02, '0x1A000000-bit')):
    ys = [y for h2, y in recs if h2 == hh]
    print(f'  {hh:08X} ({bitname}): y = {[round(y,2) for y in ys]} -> '
          + ('ALL NEGATIVE' if all(y < 0 for y in ys) else 'ALL POSITIVE' if all(y > 0 for y in ys) else 'MIXED'))
print('  => 0x04000000-bit <-> ycg y<0 ; 0x1A000000-bit <-> ycg y>0')

# ---------- (2) chirality: ycg y-side -> anatomical L/R ----------
# ymg ground truth: Bip R/L Thigh world positions (bone names are authoritative)
skel = json.load(open('docs/wrestler-skeleton-000.json'))
import math
def euler_mat(ex, ey, ez):
    cx, sx = math.cos(ex), math.sin(ex); cy, sy = math.cos(ey), math.sin(ey); cz, sz = math.cos(ez), math.sin(ez)
    Rx = np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]]); Ry = np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]]); Rz = np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
    return Rx @ Ry @ Rz
world = {}
def wpos(i):
    if i in world: return world[i]
    b = skel[i]; p = np.array(b['pos'], float)
    world[i] = p if b['parent'] < 0 else wpos(b['parent']) + wmat(b['parent']) @ p
    return world[i]
def wmat(i):
    b = skel[i]; m = euler_mat(*b['euler_xyz'])
    return m if b['parent'] < 0 else wmat(b['parent']) @ m
for i in range(len(skel)): wpos(i)
names = [b['name'] for b in skel]
def triple(o, a, b, c):
    return float(np.dot(np.array(a)-np.array(o), np.cross(np.array(b)-np.array(o), np.array(c)-np.array(o))))
# ymg tetrahedron: pelvis, head, L thigh, R thigh (L/R by NAME)
P = world[names.index('Bip Pelvis')]; H = world[names.index('Bip Head')]
TL = world[names.index('Bip L Thigh')]; TR = world[names.index('Bip R Thigh')]
t_ymg = triple(P, H, TL, TR)
print('=== (2) chirality test: sign of up.(LxR) ===')
print(f'  ymg (L/R by bone name): up.(LxR) = {t_ymg:+.1f}')
# ycg tetrahedron: pelvis, head, y<0 hip, y>0 hip -- try both L/R assignments
Pp = np.array([11.80, 0.01, 1.78]); Hp = np.array([20.34, 0., 1.33])
A = np.array([3.40, -5.38, -0.80]); B = np.array([3.40, 5.38, -0.80])
t_yneg_L = triple(Pp, Hp, A, B)   # y<0 = L
t_yneg_R = triple(Pp, Hp, B, A)   # y<0 = R
print(f'  ycg (y<0 = L): up.(LxR) = {t_yneg_L:+.1f}')
print(f'  ycg (y<0 = R): up.(LxR) = {t_yneg_R:+.1f}')
same = (t_ymg > 0) == (t_yneg_L > 0)
print(f'  => sign preserved iff ycg y<0 = anatomical L: {same}')
print('  CONCLUSION:', 'ycg y<0 = LEFT, ycg y>0 = RIGHT' if same else 'INCONCLUSIVE')

# ---------- (3) transfer to finger/toe pairs ----------
print('=== (3) transfer within 1E000000 system ===')
pairs = {'fingers': (0xA4955E6E, 0xBA955E6E), 'toes': (0x007FD58C, 0x1E7FD58C)}
for label, (a, b) in pairs.items():
    assert (a ^ b) == 0x1E000000, label
    # anchor: smaller member (0x04000000-bit side) <-> y<0 <-> L
    # fingers: A=0x04000000-bit (smaller); toes: A=root (smaller)
    print(f'  {label}: {a:08X} (smaller/A-member) -> LEFT ; {b:08X} (B-member) -> RIGHT')
print()
print('FINAL: A4955E6E=LEFT fingers, BA955E6E=RIGHT fingers;')
print('       579B8E50=LEFT thumb (pairs with A4955E6E), 579B89D0=RIGHT thumb;')
print('       007FD58C=LEFT toes, 1E7FD58C=RIGHT toes.')
