#!/usr/bin/env python3
"""Generate mapgen.json for the svalbard_seed_vault CDDA mod.

Five z-levels; underground levels are 2x2 OMT (48x48) multi-OMT maps.
Fixed vertical anchors (absolute coords, identical on adjacent levels):
  S0 surface<->z-1 stairs: (11,4),(12,4)
  S1 z-1<->z-2 stairs:     (35,40),(36,40)
  S2 z-2<->z-3 stairs:     (11,25),(12,25)
  S3 z-3<->z-4 stairs:     (35,7),(36,7)
  Vent-shaft ladders alternate between tiles A=(43,17) B=(44,17):
    z-1 v@B | z-2 ^@B v@A | z-3 ^@A v@B | z-4 ^@B
Run:  python3 build-scripts/gen-svalbard-mapgen.py [--preview]
Writes build-scripts/dda-mods/svalbard_seed_vault/mapgen.json
"""
import json
import sys
from pathlib import Path

W = H = 48
SURF_H = 24


def grid(h=H, w=W):
    return [[' '] * w for _ in range(h)]


def hwall(g, y, x1, x2, ch='|'):
    for x in range(x1, x2 + 1):
        g[y][x] = ch


def vwall(g, x, y1, y2, ch='|'):
    for y in range(y1, y2 + 1):
        g[y][x] = ch


def fill(g, x1, y1, x2, y2, ch='.'):
    for y in range(y1, y2 + 1):
        for x in range(x1, x2 + 1):
            g[y][x] = ch


def room(g, x1, y1, x2, y2, wall='|', floor='.'):
    fill(g, x1 + 1, y1 + 1, x2 - 1, y2 - 1, floor)
    hwall(g, y1, x1, x2, wall)
    hwall(g, y2, x1, x2, wall)
    vwall(g, x1, y1, y2, wall)
    vwall(g, x2, y1, y2, wall)


def put(g, x, y, s):
    for i, c in enumerate(s):
        g[y][x + i] = c


def door(g, x, y):
    g[y][x] = '+'


WALLS = {'|', '1', ' '}


def check_connectivity(g, name, seeds):
    """Flood fill from seeds; every non-wall, non-rail tile must be reachable."""
    seen = set(seeds)
    stack = list(seeds)
    while stack:
        x, y = stack.pop()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < len(g[0]) and 0 <= ny < len(g) and (nx, ny) not in seen \
                    and g[ny][nx] not in WALLS and g[ny][nx] != '#':
                seen.add((nx, ny))
                stack.append((nx, ny))
    bad = [(x, y, g[y][x]) for y in range(len(g)) for x in range(len(g[0]))
           if g[y][x] not in WALLS and g[y][x] != '#' and g[y][x] != 'R'
           and (x, y) not in seen]
    if bad:
        print(f'!! {name}: {len(bad)} unreachable tiles, e.g. {bad[:8]}')
        return False
    print(f'ok {name}: connected')
    return True


# ---------------------------------------------------------------- surface
def build_surface():
    g = grid(SURF_H)
    # entrance wedge (unchanged from v1): x8..15, y2..17
    room(g, 8, 2, 15, 17, wall='1')
    put(g, 11, 4, '>>')
    door(g, 11, 17)
    door(g, 12, 17)
    # garage: x26..45, y4..20
    room(g, 26, 4, 45, 20, wall='1')
    for x in (29, 30, 31, 37, 38, 39):   # south vehicle bays
        door(g, x, 20)
    door(g, 26, 12)                       # personnel door facing the wedge
    put(g, 28, 5, 'n.cc')
    put(g, 40, 5, 'zz.ss')
    put(g, 27, 19, 'cc')
    return g


# ---------------------------------------------------------------- z-1
def build_sub1():
    g = grid()
    room(g, 2, 2, 45, 45)
    hwall(g, 12, 2, 45)
    hwall(g, 15, 2, 45)
    fill(g, 3, 13, 44, 14)               # corridor
    # north band: stair lobby | changing | vent plant
    vwall(g, 19, 2, 12)
    vwall(g, 31, 2, 12)
    put(g, 11, 4, '<<')
    put(g, 4, 10, 'bb')
    put(g, 15, 10, 'bb')
    put(g, 20, 3, 'WWWWWWWWWW')          # changing area: outdoor-gear lockers
    put(g, 21, 8, 'bbbbbbbb')
    put(g, 20, 11, 'oo')
    for x in (33, 36, 39, 42):           # vent plant machinery
        put(g, x, 4, 'a')
        put(g, x, 9, 'a')
    put(g, 43, 11, 'x')
    # west: pool hall / east: gym, storage, stair room
    vwall(g, 27, 15, 45)
    hwall(g, 38, 2, 27)
    fill(g, 6, 19, 23, 32, 'w')          # the pool
    put(g, 3, 17, 'bbbb')
    put(g, 3, 34, 'U')
    put(g, 3, 35, 'U')
    put(g, 3, 36, 'U')
    put(g, 24, 35, 'S')
    # pool changing room (south-west)
    put(g, 4, 44, 'WWWWWW')
    put(g, 4, 41, 'bbbbbb')
    put(g, 20, 44, 'U.U')
    put(g, 25, 44, 'T')
    put(g, 25, 41, 'S')
    # gym
    hwall(g, 26, 27, 45)
    for x in (29, 31, 33):
        put(g, x, 17, 'm')
        put(g, x, 20, 'E')
    put(g, 38, 23, 'P')
    put(g, 29, 25, 'qq')
    put(g, 36, 25, 'qq')
    # vent shaft closet (x41..45, y16..20) — top of the shaft
    room(g, 41, 16, 45, 20)
    put(g, 44, 17, 'v')
    put(g, 42, 19, 'aa')
    # storage y27..35
    hwall(g, 36, 27, 45)
    put(g, 29, 29, 'ssssss')
    put(g, 38, 29, 'ss')
    put(g, 29, 32, 'ssssss')
    put(g, 29, 34, 'zzzz')
    put(g, 42, 34, 'CC')
    # stair room down to ops
    put(g, 35, 40, '>>')
    put(g, 31, 44, 'ss')
    put(g, 43, 44, 'W')
    for x, y in ((11, 12), (25, 12), (38, 12), (19, 7), (10, 15), (33, 15),
                 (41, 18), (33, 26), (37, 36), (13, 38)):
        door(g, x, y)
    return g


# ---------------------------------------------------------------- z-2
def build_sub2():
    g = grid()
    room(g, 2, 2, 45, 45)
    hwall(g, 12, 2, 45)
    hwall(g, 15, 2, 45)
    fill(g, 3, 13, 44, 14)               # corridor
    # north band: three offices + server room
    for x in (12, 22, 32):
        vwall(g, x, 2, 12)
    for ox in (3, 13, 23):
        put(g, ox + 2, 5, 'd')
        put(g, ox + 2, 6, 'h')
        put(g, ox, 3, 'f')
        put(g, ox + 6, 3, 'u')
    put(g, 34, 4, 'V.V.V')
    put(g, 34, 6, 'V.V.V')
    put(g, 34, 8, 'V.V.V')
    put(g, 43, 3, 'x')
    put(g, 43, 4, 'x')
    # west block: comms over stair lobby
    vwall(g, 16, 15, 30)
    hwall(g, 22, 2, 16)
    put(g, 3, 17, 'xxx')
    put(g, 6, 19, 'd')
    put(g, 7, 19, 'h')
    put(g, 11, 25, '>>')                 # down to habitat
    put(g, 3, 28, 'bb')
    # operations room x16..33
    vwall(g, 33, 15, 30)
    put(g, 18, 16, 'x.x.x.x.x.x')
    fill(g, 22, 21, 25, 23, 't')
    put(g, 21, 21, 'h')
    put(g, 21, 23, 'h')
    put(g, 26, 21, 'h')
    put(g, 26, 23, 'h')
    put(g, 23, 20, 'hh')
    put(g, 23, 24, 'hh')
    put(g, 30, 28, 'd')
    put(g, 31, 28, 'h')
    # electrical room x33..45 (vent closet embedded)
    room(g, 41, 16, 45, 20)
    put(g, 43, 17, 'v^')                 # v@A(43,17), ^@B(44,17)
    put(g, 34, 17, 'ccccc')
    put(g, 34, 24, 'nn')
    put(g, 38, 24, 'a')
    hwall(g, 30, 2, 45)
    # south band: workshop | generator hall
    vwall(g, 24, 30, 45)
    for x in (4, 9, 14):
        put(g, x, 32, 'nn')
    put(g, 4, 44, 'cccc')
    put(g, 12, 44, 'zzz')
    put(g, 19, 44, 'ss')
    for x in (27, 31, 39, 43):
        put(g, x, 34, 'G')
        put(g, x, 35, 'G')
    put(g, 35, 40, '<<')                 # up to egress level
    put(g, 26, 44, 'nn')
    put(g, 31, 44, 'ss')
    put(g, 40, 44, 'zz')
    for x, y in ((7, 12), (17, 12), (27, 12), (38, 12), (8, 15), (24, 15),
                 (8, 22), (16, 26), (33, 20), (41, 18), (28, 30), (12, 30),
                 (24, 38)):
        door(g, x, y)
    return g


# ---------------------------------------------------------------- z-3
def build_sub3():
    g = grid()
    room(g, 2, 2, 45, 45)
    hwall(g, 12, 2, 45)
    hwall(g, 15, 2, 45)
    fill(g, 3, 13, 44, 14)               # corridor
    # north band: mess | kitchen | stair hall | pantry
    vwall(g, 20, 2, 12)
    vwall(g, 31, 2, 12)
    vwall(g, 40, 2, 12)
    for tx in (5, 10, 15):
        put(g, tx, 5, 'tt')
        put(g, tx, 4, 'hh')
        put(g, tx, 6, 'hh')
        put(g, tx, 9, 'tt')
        put(g, tx, 8, 'hh')
        put(g, tx, 10, 'hh')
    put(g, 21, 3, 'KKKKKKK')
    put(g, 29, 3, 'k')
    put(g, 29, 5, 'F')
    put(g, 29, 6, 'F')
    put(g, 21, 5, 'S')
    put(g, 21, 8, 'KK')
    put(g, 35, 7, '>>')                  # down to the vault
    put(g, 33, 3, 'x')
    for y in (3, 6, 9):
        put(g, 41, y, 'C')
        put(g, 44, y, 'C')
    # west/center: dorm cells over lobby/commons
    vwall(g, 16, 15, 30)
    vwall(g, 30, 15, 30)
    hwall(g, 22, 2, 30)
    vwall(g, 9, 15, 22)
    vwall(g, 23, 15, 22)
    for cx in (3, 10, 17, 24):           # four dorm cells y16..21
        put(g, cx, 16, 'B')
        put(g, cx, 17, 'B')
        put(g, cx, 21, 'e')
        put(g, cx + 4, 21, 'o')
    put(g, 11, 25, '<<')                 # up to ops
    put(g, 3, 28, 'bb')
    put(g, 18, 25, 'tt')
    put(g, 18, 24, 'hh')
    put(g, 18, 26, 'hh')
    put(g, 26, 28, 'AA')
    # east: rec room (vent closet embedded)
    room(g, 41, 16, 45, 20)
    put(g, 43, 17, '^v')                 # ^@A(43,17), v@B(44,17)
    put(g, 35, 22, 'pp')
    put(g, 32, 17, 'AA')
    put(g, 37, 17, 'AA')
    put(g, 31, 28, 'uuu')
    put(g, 38, 27, 't')
    put(g, 38, 28, 'hh')
    hwall(g, 30, 2, 45)
    # south band: lounge | infirmary | bath+laundry
    vwall(g, 20, 30, 45)
    vwall(g, 33, 30, 45)
    put(g, 4, 32, 'jj.A')
    put(g, 3, 44, 'uuuu')
    put(g, 10, 38, 'tt')
    put(g, 10, 37, 'hh')
    put(g, 10, 39, 'hh')
    put(g, 15, 32, 'A')
    put(g, 22, 32, 'B.B.B')
    put(g, 30, 32, 'M')
    put(g, 30, 33, 'M')
    put(g, 30, 35, 'S')
    put(g, 22, 43, 'dh')
    for y in (32, 35):
        put(g, 35, y, 'T')
        put(g, 38, y, 'T')
    put(g, 35, 38, 'U')
    put(g, 38, 38, 'U')
    put(g, 41, 38, 'U')
    put(g, 35, 41, 'SS')
    put(g, 41, 43, 'y')
    put(g, 43, 43, 'Y')
    for x, y in ((10, 12), (25, 12), (35, 12), (42, 12), (20, 7), (5, 15),
                 (12, 15), (19, 15), (26, 15), (5, 22), (12, 22), (19, 22),
                 (26, 22), (16, 26), (30, 26), (35, 15), (41, 18), (10, 30),
                 (25, 30), (37, 30), (20, 38), (33, 38)):
        door(g, x, y)
    return g


# ---------------------------------------------------------------- z-4
def build_deep():
    g = grid()
    room(g, 2, 2, 45, 45)
    hwall(g, 16, 2, 45)
    hwall(g, 30, 2, 45)
    # north: chambers A, B | stair hall
    vwall(g, 15, 2, 16)
    vwall(g, 28, 2, 16)
    for x1 in (4, 17):
        for y in (4, 7, 10, 13):
            put(g, x1, y, 'rrrr')
            put(g, x1 + 6, y, 'rrrr')
    put(g, 35, 7, '<<')                  # the way out
    put(g, 31, 12, 'd')
    put(g, 32, 12, 'h')
    put(g, 42, 3, 'W')
    put(g, 43, 3, 'W')
    put(g, 30, 3, 'x')
    # gallery y17..29 with raised central walkway
    fill(g, 4, 22, 43, 24, ',')
    hwall(g, 21, 4, 43, '#')
    hwall(g, 25, 4, 43, '#')
    for x in (8, 9, 21, 22, 34, 35):     # walkway steps
        g[21][x] = ','
        g[25][x] = ','
    put(g, 17, 19, 'xx')
    put(g, 5, 28, 'bb')
    put(g, 30, 28, 'bb')
    # vent closet — bottom of the shaft
    room(g, 41, 16, 45, 20)
    put(g, 44, 17, '^')                  # ^@B(44,17)
    put(g, 42, 19, 'aa')
    # south: chamber C | duty room (start) | chamber D
    vwall(g, 15, 30, 45)
    vwall(g, 28, 30, 45)
    for x1 in (4, 30):
        for y in (32, 35, 38, 41):
            put(g, x1, y, 'rrrr')
            put(g, x1 + 6, y, 'rrrr')
    put(g, 4, 44, 'rrrr')
    put(g, 34, 44, 'rrrr')
    # duty room: the crew's overwinter station — player wakes here
    put(g, 17, 32, 'B.B')
    put(g, 21, 32, 'e')
    put(g, 26, 32, 'l')
    put(g, 26, 33, 'l')
    put(g, 21, 37, 'tt')
    put(g, 21, 36, 'hh')
    put(g, 21, 38, 'hh')
    put(g, 17, 44, 'cc')
    put(g, 25, 44, 'W')
    put(g, 26, 44, 'W')
    put(g, 17, 40, 'b')
    for x, y in ((8, 16), (21, 16), (32, 16), (41, 18), (8, 30), (21, 30),
                 (36, 30)):
        door(g, x, y)
    return g


# ---------------------------------------------------------------- assembly
def rows(g):
    return [''.join(r) for r in g]


def main():
    surface = build_surface()
    sub1, sub2, sub3, deep = build_sub1(), build_sub2(), build_sub3(), build_deep()

    ok = True
    ok &= check_connectivity(surface, 'surface', [(11, 5), (30, 10)])
    ok &= check_connectivity(sub1, 'z-1 egress', [(11, 5)])
    ok &= check_connectivity(sub2, 'z-2 operations', [(35, 41)])
    ok &= check_connectivity(sub3, 'z-3 habitat', [(11, 26)])
    ok &= check_connectivity(deep, 'z-4 vault', [(35, 8)])

    # stair/ladder anchor cross-checks
    anchors = [
        (surface, sub1, [(11, 4), (12, 4)], '>', '<'),
        (sub1, sub2, [(35, 40), (36, 40)], '>', '<'),
        (sub2, sub3, [(11, 25), (12, 25)], '>', '<'),
        (sub3, deep, [(35, 7), (36, 7)], '>', '<'),
        (sub1, sub2, [(44, 17)], 'v', '^'),
        (sub2, sub3, [(43, 17)], 'v', '^'),
        (sub3, deep, [(44, 17)], 'v', '^'),
    ]
    for up, down, pts, upch, downch in anchors:
        for x, y in pts:
            if up[y][x] != upch or down[y][x] != downch:
                print(f'!! anchor mismatch at ({x},{y}): {up[y][x]!r}/{down[y][x]!r}'
                      f' expected {upch!r}/{downch!r}')
                ok = False
    if not ok:
        sys.exit(1)
    print('ok anchors: all stairs/ladders aligned')

    if '--preview' in sys.argv:
        for name, g in (('SURFACE', surface), ('Z-1 EGRESS', sub1),
                        ('Z-2 OPERATIONS', sub2), ('Z-3 HABITAT', sub3),
                        ('Z-4 VAULT', deep)):
            print(f'\n=== {name} ===')
            print('    ' + ''.join(str(x % 10) for x in range(len(g[0]))))
            for y, r in enumerate(rows(g)):
                print(f'{y:3d} {r}')

    roof16 = ['RRRRRRRR' + ' ' * 8] * 16
    garage_roof = [' ' * 24] * 4 + [' ' * 2 + 'R' * 20 + ' ' * 2] * 17 + [' ' * 24] * 3

    out = [
        {
            "type": "mapgen",
            "om_terrain": [["svalbard_vault_entrance", "svalbard_vault_garage"]],
            "//": "Surface: portal wedge (west) and vehicle garage (east).",
            "object": {
                "fill_ter": "t_region_groundcover",
                "rows": rows(surface),
                "palettes": ["svalbard_vault_palette"],
                "place_nested": [
                    {"chunks": ["svalbard_vault_roof"], "x": 8, "y": 2, "z": 1},
                    {"chunks": ["svalbard_garage_roof"], "x": 24, "y": 0, "z": 1}
                ],
                "place_vehicles": [
                    {"vehicle": "suv", "x": 31, "y": 12, "chance": 90, "rotation": 270, "status": 1, "fuel": 40},
                    {"vehicle": "humvee", "x": 39, "y": 12, "chance": 75, "rotation": 270, "status": 1, "fuel": 40}
                ]
            }
        },
        {
            "type": "mapgen",
            "nested_mapgen_id": "svalbard_vault_roof",
            "object": {"mapgensize": [16, 16], "rows": roof16,
                       "palettes": ["svalbard_vault_palette"]}
        },
        {
            "type": "mapgen",
            "nested_mapgen_id": "svalbard_garage_roof",
            "object": {"mapgensize": [24, 24], "rows": garage_roof,
                       "palettes": ["svalbard_vault_palette"]}
        },
    ]
    levels = [
        ("sub1", sub1, "z-1: egress level — changing area, pool, gym, vent plant, storage."),
        ("sub2", sub2, "z-2: operations — offices, server room, ops centre, electrical, workshop, generator hall."),
        ("sub3", sub3, "z-3: habitat — mess, kitchen, pantry, dorms, rec room, lounge, infirmary, bath/laundry."),
        ("deep", deep, "z-4: the vault — six seed chambers, gallery with raised walkway, duty room (start)."),
    ]
    for key, g, note in levels:
        out.append({
            "type": "mapgen",
            "om_terrain": [
                [f"svalbard_vault_{key}_a", f"svalbard_vault_{key}_b"],
                [f"svalbard_vault_{key}_c", f"svalbard_vault_{key}_d"]
            ],
            "//": note,
            "object": {
                "fill_ter": "t_rock",
                "rows": rows(g),
                "palettes": ["svalbard_vault_palette"]
            }
        })

    dest = Path(__file__).parent / 'dda-mods' / 'svalbard_seed_vault' / 'mapgen.json'
    dest.write_text(json.dumps(out, indent=2) + '\n')
    print(f'wrote {dest}')


if __name__ == '__main__':
    main()
