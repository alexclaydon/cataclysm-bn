#!/usr/bin/env python3
"""Generate mapgen.json for the svalbard_seed_vault CDDA mod.

v3: five z-levels; underground levels are 3x3 OMT (72x72) multi-OMT maps.
Surface is 1x3 (entrance / garage / radio mast) plus detached warming huts.

Fixed vertical anchors (absolute coords, identical on adjacent levels):
  S0 surface<->z-1 stairs: (11,4),(12,4)    [quadrant a]
  S1 z-1<->z-2 stairs:     (59,64),(60,64)  [quadrant i]
  S2 z-2<->z-3 stairs:     (11,49),(12,49)  [quadrant g]
  S3 z-3<->z-4 stairs:     (59,7),(60,7)    [quadrant c]
  Vent-shaft ladders alternate between tiles A=(67,41) B=(68,41) [quadrant f]:
    z-1 v@B | z-2 ^@B v@A | z-3 ^@A v@B | z-4 ^@B
  Vent closet rect is (65,38)-(69,42) on every underground level, door (65,40).

Corridor scheme (underground): bands N y2..19 / M y22..43 / S y46..69,
separated by 2-wide corridors at y20..21 and y44..45.

Run:  python3 build-scripts/gen-svalbard-mapgen.py [--preview]
Writes build-scripts/dda-mods/svalbard_seed_vault/mapgen.json
"""
import json
import sys
from pathlib import Path

W = H = 72
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


def refloor(g, x1, y1, x2, y2, ch):
    """Retype the open floor of a room without touching walls/furniture."""
    for y in range(y1, y2 + 1):
        for x in range(x1, x2 + 1):
            if g[y][x] == '.':
                g[y][x] = ch


def door(g, x, y, ch='+'):
    g[y][x] = ch


FULL_LIGHTS = tuple((x, y) for y in (20, 44) for x in (6, 24, 42, 62))


def shell(g, lights=FULL_LIGHTS):
    """Outer hull + the two main corridors."""
    room(g, 2, 2, 69, 69)
    hwall(g, 19, 2, 69)
    hwall(g, 22, 2, 69)
    fill(g, 3, 20, 68, 21)
    hwall(g, 43, 2, 69)
    hwall(g, 46, 2, 69)
    fill(g, 3, 44, 68, 45)
    # emergency lighting at corridor intersections; levels where the dead
    # generator matters pass a thinned list so the east reaches stay dark
    for x, y in lights:
        g[y][x] = '7'


def vent_closet(g, ladders):
    """The vertical ventilation shaft, same spot on every level."""
    room(g, 65, 38, 69, 42)
    put(g, 67, 41, ladders)
    door(g, 65, 40)


WALLS = {'|', '1', ' ', '5', '8', '=', '2', 'L', 'I', '"'}
NONROOM = WALLS | {'#', 'R', '~', '-'}


def check_connectivity(g, name, seeds, outdoor=False):
    blocked = NONROOM - {' '} if outdoor else NONROOM
    seen = set(seeds)
    stack = list(seeds)
    while stack:
        x, y = stack.pop()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < len(g[0]) and 0 <= ny < len(g) and (nx, ny) not in seen \
                    and g[ny][nx] not in blocked:
                seen.add((nx, ny))
                stack.append((nx, ny))
    bad = [(x, y, g[y][x]) for y in range(len(g)) for x in range(len(g[0]))
           if g[y][x] not in blocked and g[y][x] != ' ' and (x, y) not in seen]
    if bad:
        print(f'!! {name}: {len(bad)} unreachable tiles, e.g. {bad[:8]}')
        return False
    print(f'ok {name}: connected')
    return True


# ---------------------------------------------------------------- surface
def build_surface():
    g = grid(SURF_H, W)
    # --- the portal wedge, with flared wings, glass art face, lit forecourt
    room(g, 7, 2, 16, 19, wall='1')
    put(g, 11, 4, '>>')
    put(g, 8, 19, '555++555')            # backlit art band flanking the doors
    for x, y in ((6, 15), (5, 16), (4, 17), (17, 15), (18, 16), (19, 17)):
        g[y][x] = '1'                     # flared wing walls
    g[4][9] = '7'
    g[4][14] = '7'
    g[12][9] = '7'
    g[12][14] = '7'
    fill(g, 10, 20, 13, 23, '_')          # paved approach
    fill(g, 14, 21, 27, 22, '_')          # path from wedge to garage
    g[21][8] = '7'
    g[21][15] = '7'
    g[21][6] = '$'
    g[21][17] = '$'
    g[22][5] = '!'
    g[4][17] = '('                        # downspout to the wedge roof
    # --- garage (col 1)
    room(g, 26, 4, 45, 20, wall='1')
    for x in (29, 30, 31, 37, 38, 39):
        door(g, x, 20)
    door(g, 26, 12)
    put(g, 28, 5, 'n.cc')
    put(g, 40, 5, 'zz.ss')
    put(g, 27, 19, 'cc')
    put(g, 42, 19, '44')
    g[5][25] = '('                        # downspout to the garage roof
    fill(g, 28, 21, 41, 22, '_')          # apron
    # --- radio mast compound (col 2)
    room(g, 52, 4, 67, 19, wall='8', floor='.')
    door(g, 59, 19, ';')
    door(g, 60, 19, ';')
    put(g, 58, 8, '==')
    put(g, 58, 9, '==')
    room(g, 61, 12, 67, 17, wall='1')
    door(g, 61, 14)
    put(g, 63, 13, 'x')
    put(g, 65, 13, 'G')
    put(g, 63, 16, 'l')
    g[13][62] = '7'
    g[13][60] = '('                       # downspout to the shack roof
    return g


def build_hut():
    g = grid(SURF_H, 24)
    room(g, 8, 8, 15, 14, wall='L')
    door(g, 11, 14, 'D')
    g[8][13] = '~'
    put(g, 9, 9, 'Q')
    put(g, 13, 9, 'B')
    put(g, 9, 12, 'b')
    put(g, 9, 13, 'b')
    put(g, 14, 13, '3')
    g[9][7] = '('                         # downspout to the hut roof
    return g


# ---------------------------------------------------------------- z-1
def build_sub1():
    g = grid()
    shell(g)
    # N band: stair lobby | changing | security | radio | vent plant
    for x in (19, 33, 45, 57):
        vwall(g, x, 2, 19)
    put(g, 11, 4, '<<')
    g[4][3] = '?'                        # level wayfinding sign
    g[4][8] = '7'
    g[4][15] = '7'
    put(g, 4, 10, 'bb')
    put(g, 15, 10, 'bb')
    put(g, 20, 3, 'WWWWWWWWWWWW')
    put(g, 21, 8, 'bbbbbbbbbb')
    put(g, 20, 11, 'oo')
    g[5][26] = '7'
    put(g, 34, 3, 'g')
    put(g, 43, 3, 'x')
    put(g, 35, 5, 'd')
    put(g, 35, 6, 'h')
    put(g, 44, 5, 'f')
    put(g, 46, 3, 'xxx')
    put(g, 50, 5, 'd')
    put(g, 50, 6, 'h')
    put(g, 55, 3, 'u')
    for x in (58, 61, 64):
        for y in (4, 9, 14):
            g[y][x] = 'a'
    put(g, 67, 17, 'n')
    refloor(g, 58, 3, 68, 18, ':')       # vent plant: industrial grating
    for x, y in ((10, 19), (25, 19), (38, 19), (50, 19), (62, 19), (19, 7)):
        door(g, x, y)
    # M band: pool + sauna | gym + janitor | ski store / linen | fuel / battery
    vwall(g, 29, 22, 43)
    vwall(g, 47, 22, 43)
    vwall(g, 57, 22, 43)
    fill(g, 6, 26, 25, 38, 'w')
    put(g, 4, 23, 'bbbb')
    put(g, 12, 23, 'bbbb')
    for x in (4, 6, 8):
        g[41][x] = 'U'
    put(g, 26, 41, 'S')
    g[24][3] = '7'
    room(g, 29, 36, 37, 43)              # sauna
    put(g, 30, 37, 'Q')
    put(g, 31, 39, 'bbbb')
    put(g, 31, 41, 'bbbb')
    refloor(g, 30, 37, 36, 42, '{')      # sauna: wood
    door(g, 29, 39)
    for x in (31, 33, 35, 37):
        g[24][x] = 'm'
        g[27][x] = 'E'
    put(g, 44, 25, 'P')
    put(g, 39, 23, 'qq')
    put(g, 43, 28, 'qq')
    put(g, 39, 31, 'bb')
    hwall(g, 35, 37, 47)                 # janitor closet under gym east
    put(g, 38, 42, 'JJ')
    put(g, 45, 42, '3')
    door(g, 41, 35)
    hwall(g, 30, 47, 57)                 # ski store / linen
    put(g, 48, 23, 'WWWWW')
    put(g, 48, 28, 'ss')
    put(g, 48, 31, 'sss')
    put(g, 48, 41, 'ss')
    hwall(g, 33, 57, 69)                 # fuel store / battery room
    for x in (59, 62, 65):
        g[24][x] = '2'
        g[28][x] = '2'
    put(g, 58, 31, 'zz')
    put(g, 58, 34, 'ccc')
    put(g, 58, 41, 'nn')
    put(g, 62, 34, 'a')
    put(g, 62, 36, 'a')
    refloor(g, 58, 23, 68, 32, ':')      # fuel store: grating
    refloor(g, 58, 34, 68, 42, ':')      # battery room + vent shaft: grating
    vent_closet(g, '.v')                 # z-1: top of the shaft, ladder down @B
    put(g, 66, 40, '*')
    for x, y in ((12, 22), (36, 22), (52, 22), (62, 22), (52, 43), (60, 43),
                 (33, 43), (10, 43)):
        door(g, x, y)
    # S band: bulk storage | cold store / parts | equipment+gear | turbine gallery
    vwall(g, 24, 46, 69)
    vwall(g, 38, 46, 69)
    vwall(g, 44, 46, 69)
    hwall(g, 57, 24, 44)
    for y in (49, 52, 55, 58, 61, 64):
        put(g, 4, y, 'ssssss')
        put(g, 14, y, 'ssssss')
    put(g, 4, 67, '33')
    put(g, 10, 67, '4')
    put(g, 14, 67, '33')
    put(g, 18, 67, '44')
    put(g, 21, 67, 'zz')
    g[47][12] = '7'
    for x in (26, 28, 30, 32):           # cold store: stocked freezers
        g[48][x] = ']'
        g[51][x] = ']'
    put(g, 26, 55, 'CCCC')
    put(g, 26, 59, 'zzz')
    put(g, 26, 67, 'n')
    put(g, 33, 59, 'ss')
    put(g, 33, 63, 'ss')
    # equipment room over gear room (narrow column west of the void)
    put(g, 40, 48, '33')
    put(g, 39, 52, 'sss')
    put(g, 39, 55, 'W')
    put(g, 39, 59, 'WW')
    put(g, 40, 62, 'b')
    put(g, 39, 67, 'zz')
    # turbine gallery: two z-levels tall — open air over the z-2 generator
    # hall, crossed by railed catwalks; the stairs land on a hung platform
    fill(g, 45, 47, 68, 68, 'I')
    fill(g, 45, 47, 68, 47, ',')         # north catwalk along the corridor wall
    hwall(g, 48, 45, 68, '#')
    g[48][59] = ','
    g[48][60] = ','
    fill(g, 59, 48, 60, 61, ',')         # main catwalk south to the platform
    vwall(g, 58, 49, 60, '#')
    vwall(g, 61, 49, 60, '#')
    fill(g, 56, 62, 64, 67, '.')         # stair platform
    hwall(g, 61, 56, 64, '#')
    g[61][59] = ','
    g[61][60] = ','
    vwall(g, 55, 62, 67, '#')
    g[63][55] = ','
    g[64][55] = ','
    vwall(g, 65, 62, 67, '#')
    hwall(g, 68, 56, 64, '#')
    fill(g, 45, 63, 54, 64, ',')         # west spur from the gear room
    hwall(g, 62, 45, 54, '#')
    hwall(g, 65, 45, 54, '#')
    put(g, 59, 64, '>>')
    g[47][62] = '7'
    g[54][59] = '7'
    g[63][57] = '7'
    put(g, 15, 21, 'b')
    put(g, 33, 20, 'l')
    put(g, 50, 45, 'b')
    for x, y in ((10, 46), (20, 46), (30, 46), (41, 46), (60, 46), (33, 57),
                 (41, 57), (44, 63)):
        door(g, x, y)
    # meltwater intrusion (the 2017 flood, replayed): the entrance tunnel
    # froze over where the pump lost; the crew's sandbag line holds a gap
    # open under the stairs
    refloor(g, 4, 5, 17, 9, 'N')
    for x in (6, 7, 8, 9, 12, 13, 14):
        g[10][x] = 'O'
    # vent trunk B: top of the shaft, behind the janitor's lockers
    g[42][46] = 'v'
    mons = [{"monster": "mon_manhack", "x": 39, "y": 10},
            {"monster": "mon_manhack", "x": 62, "y": 10},
            {"monster": "mon_zombie_swimmer", "x": 4, "y": 30}]
    return g, mons


# ---------------------------------------------------------------- z-2
def build_sub2():
    g = grid()
    shell(g, lights=((6, 20), (42, 20), (24, 44)))
    # N band: 4 offices | conference | server | archives
    for x in (10, 18, 26, 34, 47, 58):
        vwall(g, x, 2, 19)
    for ox in (3, 11, 19, 27):
        put(g, ox, 3, 'f')
        put(g, ox + 5, 3, 'u')
        put(g, ox + 2, 6, 'd')
        put(g, ox + 2, 7, 'h')
        put(g, ox + 2, 12, 'd')
        put(g, ox + 3, 12, 'h')
        put(g, ox, 16, 'ff')
        put(g, ox + 4, 16, 'u')
    fill(g, 37, 8, 43, 10, 't')
    put(g, 37, 7, 'hhhhhhh')
    put(g, 37, 11, 'hhhhhhh')
    put(g, 36, 16, 'uu')
    put(g, 41, 16, 'uu')
    put(g, 45, 4, 'f')
    g[3][36] = '7'
    g[3][45] = '7'
    for y in (4, 7, 10, 13):
        put(g, 48, y, 'V.V.V.V')
    put(g, 55, 16, 'a')
    put(g, 56, 16, 'x')
    refloor(g, 48, 3, 57, 18, ',')       # server room: raised metal floor
    g[3][52] = '7'
    put(g, 59, 3, 'ff.ff.ff')
    put(g, 59, 8, 'ff.ff.ff')
    put(g, 59, 11, 'ff.ff.ff')
    put(g, 59, 15, 'uuu')
    put(g, 64, 15, 'uu')
    put(g, 67, 17, '3')
    for x, y in ((6, 19), (14, 19), (22, 19), (30, 19), (40, 19), (52, 19),
                 (63, 19)):
        door(g, x, y)
    # M band: comms / brig | ops centre | armory / checkpoint | electrical
    vwall(g, 14, 22, 43)
    vwall(g, 37, 22, 43)
    vwall(g, 49, 22, 43)
    hwall(g, 33, 2, 14)
    put(g, 3, 24, 'xxx')
    put(g, 6, 27, 'd')
    put(g, 7, 27, 'h')
    put(g, 3, 30, 'ff')
    vwall(g, 8, 33, 43)                  # two brig cells
    put(g, 4, 35, 'B')
    put(g, 6, 35, 'T')
    put(g, 10, 35, 'B')
    put(g, 12, 35, 'T')
    put(g, 16, 23, 'x.x.x.x.x')
    fill(g, 22, 30, 27, 32, 't')
    put(g, 22, 29, 'hhhhhh')
    put(g, 22, 33, 'hhhhhh')
    put(g, 33, 40, 'd')
    put(g, 34, 40, 'h')
    g[42][16] = '7'
    g[23][35] = '7'
    put(g, 35, 25, 'Z')                  # vault security terminal (working)
    hwall(g, 31, 37, 49)                 # armory over checkpoint
    put(g, 38, 23, 'gg')
    put(g, 43, 23, 'iii')
    put(g, 38, 29, 'ii')
    put(g, 47, 29, 'l')
    put(g, 38, 33, 'x')
    put(g, 40, 35, 'd')
    put(g, 40, 36, 'h')
    put(g, 45, 33, 'll')
    put(g, 50, 23, 'ccccc')
    put(g, 50, 41, 'nn')
    put(g, 56, 23, 'a.a')
    put(g, 51, 28, 'zz')
    put(g, 55, 28, '2')
    put(g, 50, 33, 'ccc')
    put(g, 56, 33, 'a')
    put(g, 61, 28, '2')
    g[23][60] = '7'
    refloor(g, 50, 23, 68, 42, ':')      # electrical: industrial grating
    vent_closet(g, 'v^')                 # z-2: v@A(67,41), ^@B(68,41)
    put(g, 62, 40, '**')
    put(g, 58, 41, '*')
    put(g, 55, 44, '*')
    door(g, 37, 26, ')')                 # armory: locked, opened by terminal
    door(g, 5, 43, '/')                  # brig cells: bar doors
    door(g, 11, 43, '/')
    for x, y in ((8, 22), (24, 22), (55, 22), (24, 43), (43, 43), (52, 43)):
        door(g, x, y)
    # S band: stair lobby / records | workshop | generator hall
    vwall(g, 20, 46, 69)
    vwall(g, 44, 46, 69)
    hwall(g, 58, 2, 20)
    put(g, 11, 49, '>>')
    g[47][4] = '7'
    g[47][17] = '7'
    put(g, 3, 50, 'll')
    put(g, 3, 56, 'bb')
    put(g, 3, 60, 'ff.ff.ff')
    put(g, 3, 64, 'ff.ff.ff')
    put(g, 12, 60, 'uu')
    put(g, 12, 64, 'uu')
    put(g, 3, 67, 'ff.ff')
    put(g, 16, 67, '3')
    for x in (22, 27, 32):
        put(g, x, 48, 'nn')
        put(g, x, 55, 'nn')
    put(g, 22, 51, '@@')
    put(g, 40, 48, '44')
    put(g, 40, 50, '4')
    put(g, 40, 55, '4')
    put(g, 22, 60, 'ss')
    put(g, 27, 60, '44')
    put(g, 32, 60, 'zz')
    put(g, 22, 67, 'cccc')
    put(g, 34, 67, 'zz')
    put(g, 28, 67, 'ss')
    g[47][38] = '7'
    for x in (46, 50, 54):
        g[49][x] = 'G'
        g[50][x] = 'G'
        g[59][x] = 'G'
        g[60][x] = 'G'
    put(g, 66, 47, '2')
    put(g, 66, 49, '2')
    put(g, 66, 55, '3')
    put(g, 66, 56, '3')
    put(g, 59, 64, '<<')
    put(g, 46, 67, 'n')
    put(g, 52, 67, 'zz')
    refloor(g, 45, 47, 68, 68, ':')      # generator hall: grating underfoot
    g[66][62] = '?'                      # level wayfinding sign
    for x, y in ((10, 46), (32, 46), (50, 46), (20, 52), (12, 58), (44, 58)):
        door(g, x, y)
    put(g, 15, 20, 'l')
    put(g, 33, 21, 'b')
    put(g, 50, 44, 'b')
    # vent trunk B passes through the checkpoint corner
    g[42][46] = '^'
    g[41][46] = 'v'
    # ventilation shutter in the armory/electrical wall: the loud way in
    g[25][49] = '"'
    # Erik and Mia went up to restart the generator two days ago (duty log);
    # they never came back.  Blood pools mark where it went wrong.
    g[57][53] = '*'
    g[53][60] = '*'
    mons = [{"monster": "mon_zombie_scientist", "x": 20, "y": 28},
            {"monster": "mon_manhack", "x": 43, "y": 39},
            {"monster": "mon_manhack", "x": 53, "y": 10},
            {"monster": "mon_zombie_technician", "x": 52, "y": 57, "name": "Erik"},
            {"monster": "mon_zombie_technician", "x": 61, "y": 53, "name": "Mia"}]
    return g, mons


# ---------------------------------------------------------------- z-3
def build_sub3():
    g = grid()
    shell(g)
    # N band: mess | kitchen | pantry | hydroponics | stair hall
    for x in (22, 34, 44, 55):
        vwall(g, x, 2, 19)
    for tx in (4, 10, 16):
        for ty in (5, 10, 15):
            put(g, tx, ty, 'tt')
            put(g, tx, ty - 1, 'hh')
            put(g, tx, ty + 1, 'hh')
    refloor(g, 3, 3, 21, 18, '{')        # mess hall: wood
    put(g, 23, 3, 'KKKKKKKK')
    put(g, 32, 3, 'k')
    put(g, 32, 5, '[')
    put(g, 32, 6, '[')
    put(g, 23, 5, 'S')
    put(g, 23, 8, 'KK')
    put(g, 23, 11, 'KK')
    g[10][28] = '7'
    refloor(g, 23, 3, 33, 18, '}')       # kitchen: linoleum
    for x in (36, 39, 42):
        for y in (4, 7, 10, 13):
            g[y][x] = 'C'
    for x in (46, 49, 52):
        for y in (4, 7):
            g[y][x] = 'H'                # living crops under the grow lights
        for y in (10, 13):
            g[y][x] = '9'
    g[3][48] = '7'
    g[3][51] = '7'
    put(g, 45, 16, 'S')
    put(g, 59, 7, '>>')
    g[4][57] = '7'
    g[4][64] = '7'
    put(g, 67, 3, 'W')
    put(g, 56, 15, 'd')
    put(g, 57, 15, 'h')
    for x, y in ((12, 19), (28, 19), (39, 19), (49, 19), (62, 19), (22, 8)):
        door(g, x, y)
    # M band: dorm block (2 strips + inner hall) | rec | chapel / library
    vwall(g, 37, 22, 43)
    vwall(g, 55, 22, 43)
    hwall(g, 30, 2, 37)
    hwall(g, 33, 2, 37)
    fill(g, 3, 31, 36, 32)
    for x in (9, 16, 23, 30):
        vwall(g, x, 22, 30)
        vwall(g, x, 33, 43)
    for cx in (3, 10, 17, 24):           # eight dorm cells
        put(g, cx, 23, 'B')
        put(g, cx + 4, 23, 'e')
        put(g, cx + 4, 29, 'o')
        put(g, cx, 34, 'B')
        put(g, cx + 4, 34, 'e')
        put(g, cx + 4, 42, 'o')
    refloor(g, 3, 23, 36, 29, '{')       # dorms + commons: wood
    refloor(g, 3, 34, 36, 42, '{')
    refloor(g, 17, 23, 29, 29, '{')
    g[31][34] = '7'
    put(g, 44, 26, 'pp')
    put(g, 39, 24, 'AA')
    put(g, 50, 24, 'AA')
    put(g, 52, 23, 'u')
    put(g, 47, 31, 't')
    put(g, 47, 30, 'h')
    put(g, 47, 32, 'h')
    put(g, 38, 31, 'x')
    put(g, 40, 40, 'tt')
    put(g, 40, 39, 'hh')
    put(g, 40, 41, 'hh')
    put(g, 50, 40, 'u.u')
    refloor(g, 38, 23, 54, 42, '{')      # rec room: wood
    g[23][45] = '7'
    g[40][45] = '7'
    hwall(g, 31, 55, 69)
    put(g, 57, 24, 'bbbb')
    put(g, 57, 26, 'bbbb')
    put(g, 57, 28, 'bbbb')
    put(g, 64, 24, 't')
    refloor(g, 56, 23, 68, 30, '{')      # chapel: wood
    put(g, 56, 33, 'uu.uu')
    put(g, 56, 36, 'uu.uu')
    put(g, 56, 39, 'uu.uu')
    put(g, 62, 41, 't')
    refloor(g, 56, 32, 64, 42, '{')      # library: wood (vent closet stays)
    vent_closet(g, '^v')                 # z-3: ^@A(67,41), v@B(68,41)
    put(g, 63, 40, '*')
    put(g, 60, 42, '*')
    put(g, 58, 44, '*')
    for x, y in ((33, 22), (33, 30), (5, 30), (12, 30), (19, 30), (26, 30),
                 (5, 33), (12, 33), (19, 33), (26, 33), (33, 33), (33, 43),
                 (37, 32), (46, 22), (46, 43), (60, 22), (60, 43)):
        door(g, x, y)
    # S band: stair lobby / infirmary | lounge | bath / laundry | morgue
    vwall(g, 20, 46, 69)
    vwall(g, 47, 46, 69)
    vwall(g, 58, 46, 69)
    hwall(g, 58, 2, 20)
    hwall(g, 58, 47, 58)
    put(g, 11, 49, '<<')
    g[49][14] = '?'                      # level wayfinding sign
    g[47][4] = '7'
    g[47][17] = '7'
    put(g, 3, 56, 'bb')
    put(g, 4, 60, 'B.B.B')
    put(g, 3, 67, 'MM')
    put(g, 16, 60, 'S')
    put(g, 13, 60, '0')
    put(g, 17, 64, '6')
    put(g, 16, 67, 'd')
    put(g, 15, 67, 'h')
    put(g, 22, 48, 'jj.jj')
    put(g, 31, 48, 'A.A')
    put(g, 22, 56, 'uu')
    put(g, 38, 52, 'tt')
    put(g, 38, 51, 'hh')
    put(g, 38, 53, 'hh')
    g[47][30] = '7'
    g[47][42] = '7'
    put(g, 22, 60, 'jj')
    put(g, 30, 60, 'AA')
    put(g, 35, 60, 'jj')
    put(g, 30, 63, 'tt')
    put(g, 30, 62, 'hh')
    put(g, 30, 64, 'hh')
    put(g, 40, 60, 'u.u')
    put(g, 26, 64, 'A')
    put(g, 22, 67, 'uu')
    put(g, 30, 67, 't')
    refloor(g, 21, 47, 46, 68, '{')      # lounge: wood
    refloor(g, 3, 59, 19, 68, '}')       # infirmary: linoleum
    refloor(g, 48, 47, 57, 56, '}')      # bathroom: linoleum
    refloor(g, 48, 59, 57, 68, '}')      # laundry: linoleum
    refloor(g, 59, 47, 68, 68, '}')      # morgue: linoleum
    for x in (48, 51, 54):
        g[47][x] = 'T'
        g[51][x] = 'U'
    put(g, 48, 55, 'SS')
    put(g, 48, 60, 'y.y')
    put(g, 53, 60, 'Y.Y')
    put(g, 48, 67, '@@')
    put(g, 53, 67, 's')
    for x in (60, 62, 64, 66):
        g[48][x] = 'F'
    put(g, 60, 55, '0')
    put(g, 63, 60, '*')
    put(g, 64, 61, '*')
    g[47][60] = '7'
    for x, y in ((10, 46), (20, 52), (12, 58), (30, 46), (40, 46), (52, 46),
                 (52, 58), (63, 46), (58, 63)):
        door(g, x, y)
    put(g, 15, 21, 'b')
    put(g, 46, 20, 'l')
    put(g, 30, 45, 'b')
    # vent trunk B passes through the rec room corner
    g[41][46] = '^'
    g[42][46] = 'v'
    # the burnt dorm cell: an open flame in the dark days, cell 2
    fill(g, 10, 23, 15, 29, 'X')
    put(g, 11, 25, "'")
    put(g, 13, 27, "'")
    # the chapel barricade, breached at the door line
    put(g, 59, 23, '-')
    put(g, 61, 23, '-')
    put(g, 62, 23, '-')
    # a shadow waits inside the closed trunk A vent closet
    mons = [{"monster": "mon_blob_small", "x": 62, "y": 40},
            {"monster": "mon_shadow", "x": 66, "y": 39},
            {"monster": "mon_zombie_medical", "x": 64, "y": 52}]
    return g, mons


# ---------------------------------------------------------------- z-4
def build_deep():
    g = grid()
    shell(g, lights=((24, 20), (62, 44)))
    # N band: three seed chambers | stair hall
    for x in (19, 36, 53):
        vwall(g, x, 2, 19)
    for x1 in (4, 21, 38):
        for y in (4, 7, 10, 13, 16):
            put(g, x1, y, 'rrrr')
            put(g, x1 + 6, y, 'rrrr')
            put(g, x1 + 11, y, 'rrrr')
    put(g, 59, 7, '<<')
    put(g, 55, 3, 'll')
    g[4][56] = '7'
    g[4][65] = '7'
    put(g, 56, 15, 'x')
    put(g, 64, 15, 'd')
    put(g, 65, 15, 'h')
    put(g, 67, 3, 'W')
    for x, y in ((10, 19), (27, 19), (44, 19), (60, 19)):
        door(g, x, y)
    # M band: the grand gallery — raised central walkway, monitoring posts
    fill(g, 5, 30, 66, 34, ',')
    hwall(g, 29, 5, 66, '#')
    hwall(g, 35, 5, 66, '#')
    for x in (10, 11, 24, 25, 38, 39, 52, 53, 64, 65):
        g[29][x] = ','
        g[35][x] = ','
    for x in (20, 56):
        g[32][x] = '7'
    put(g, 30, 24, 'xx')
    put(g, 14, 24, 'bb')
    put(g, 40, 40, 'bb')
    vent_closet(g, '.^')                 # z-4: bottom of the shaft, ^@B
    put(g, 64, 40, '*')
    put(g, 63, 41, '*')
    put(g, 62, 44, '*')
    put(g, 64, 44, '*')
    for x, y in ((10, 22), (27, 22), (44, 22), (60, 22), (10, 43), (27, 43),
                 (44, 43), (57, 43)):
        door(g, x, y)
    # S band: two seed chambers | duty room + stores | research wing
    vwall(g, 19, 46, 69)
    vwall(g, 36, 46, 69)
    vwall(g, 47, 46, 69)
    vwall(g, 53, 46, 69)
    hwall(g, 58, 36, 47)
    hwall(g, 57, 53, 69)
    for x1 in (4, 21):
        for y in (48, 51, 54, 57, 60, 63, 66):
            put(g, x1, y, 'rrrr')
            put(g, x1 + 6, y, 'rrrr')
            put(g, x1 + 11, y, 'rrrr')
    # duty room — the crew's overwinter station; the player wakes here
    put(g, 37, 48, 'B.B.B')
    put(g, 43, 48, 'e')
    put(g, 45, 48, 'l')
    put(g, 45, 49, 'l')
    put(g, 41, 52, 'tt')
    put(g, 41, 51, 'hh')
    put(g, 41, 53, 'h')
    put(g, 45, 56, 'W')
    put(g, 37, 56, 'cc')
    g[47][40] = '7'
    put(g, 37, 60, 'C..C..C')
    put(g, 37, 63, 'C..C..C')
    put(g, 37, 67, 'ss')
    put(g, 44, 67, '3')
    # research wing: decon corridor, wet lab, breached containment
    refloor(g, 48, 47, 52, 68, '}')      # decon corridor: linoleum
    refloor(g, 54, 47, 68, 56, '}')      # wet lab: linoleum
    refloor(g, 54, 58, 68, 68, '}')      # containment: linoleum
    for y in (47, 49, 51):
        g[y][49] = 'U'
    put(g, 55, 48, '00')
    put(g, 59, 48, '00')
    put(g, 63, 48, '00')
    put(g, 67, 47, '%')
    put(g, 67, 49, '&')
    put(g, 67, 51, '6')
    put(g, 55, 55, 'c')
    put(g, 54, 47, 'x')
    put(g, 57, 50, '*')
    put(g, 56, 53, '*')
    room(g, 58, 60, 64, 66, wall='5')    # the containment cell
    g[62][58] = '.'                       # the breach
    g[63][58] = '.'
    put(g, 60, 62, '*')
    put(g, 61, 63, '*')
    put(g, 57, 62, '*')
    put(g, 56, 59, '*')
    put(g, 55, 57, '*')
    for y in (59, 61, 63):
        g[y][66] = 'F'
    put(g, 55, 67, 'x')
    put(g, 54, 59, 'd')
    put(g, 54, 60, 'h')
    g[44][48] = '!'                       # warning sign at the wing entrance
    for x, y in ((10, 46), (27, 46), (40, 46), (40, 58), (50, 46), (53, 50),
                 (53, 63), (60, 57)):
        door(g, x, y)
    put(g, 15, 20, 'b')
    put(g, 48, 45, 'b')
    # vent trunk B: bottom of the shaft; the guard set a trap for whatever
    # was climbing it, and wreckage marks the crew's retreat down the corridor
    g[42][46] = '^'
    g[41][46] = '`'
    for x, y in ((47, 44), (43, 45), (40, 44)):
        g[y][x] = "'"
    # NPRI-7 is a nest now: the brain-mass deep in the containment cell
    # directs its blobs; stragglers ooze through the breach and the wet lab.
    mons = [{"monster": "mon_blob_brain", "x": 62, "y": 64},
            {"monster": "mon_blob", "x": 59, "y": 62},
            {"monster": "mon_blob", "x": 56, "y": 63},
            {"monster": "mon_blob_small", "x": 57, "y": 61},
            {"monster": "mon_blob_small", "x": 58, "y": 53},
            {"monster": "mon_blob_small", "x": 26, "y": 8},
            {"monster": "mon_breather", "x": 60, "y": 31}]
    return g, mons


# ---------------------------------------------------------------- assembly
def rows(g):
    return [''.join(r) for r in g]


def roof_chunk(cover, marks=()):
    g = grid(SURF_H, 24)
    for x1, y1, x2, y2 in cover:
        fill(g, x1, y1, x2, y2, 'R')
    for x, y, ch in marks:
        g[y][x] = ch
    return rows(g)


def main():
    surface = build_surface()
    hut = build_hut()
    sub1, m1 = build_sub1()
    sub2, m2 = build_sub2()
    sub3, m3 = build_sub3()
    deep, m4 = build_deep()

    ok = True
    ok &= check_connectivity(surface, 'surface', [(11, 5)], outdoor=True)
    ok &= check_connectivity(hut, 'hut', [(10, 10)], outdoor=True)
    ok &= check_connectivity(sub1, 'z-1 egress', [(11, 5)])
    ok &= check_connectivity(sub2, 'z-2 operations', [(59, 65)])
    ok &= check_connectivity(sub3, 'z-3 habitat', [(11, 50)])
    ok &= check_connectivity(deep, 'z-4 vault', [(59, 8)])

    anchors = [
        (surface, sub1, [(11, 4), (12, 4)], '>', '<'),
        (sub1, sub2, [(59, 64), (60, 64)], '>', '<'),
        (sub2, sub3, [(11, 49), (12, 49)], '>', '<'),
        (sub3, deep, [(59, 7), (60, 7)], '>', '<'),
        (sub1, sub2, [(68, 41)], 'v', '^'),
        (sub2, sub3, [(67, 41)], 'v', '^'),
        (sub3, deep, [(68, 41)], 'v', '^'),
        (sub1, sub2, [(46, 42)], 'v', '^'),
        (sub2, sub3, [(46, 41)], 'v', '^'),
        (sub3, deep, [(46, 42)], 'v', '^'),
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
        for name, g in (('SURFACE', surface), ('HUT', hut), ('Z-1 EGRESS', sub1),
                        ('Z-2 OPERATIONS', sub2), ('Z-3 HABITAT', sub3),
                        ('Z-4 VAULT', deep)):
            print(f'\n=== {name} ===')
            print('    ' + ''.join(str(x % 10) for x in range(len(g[0]))))
            for y, r in enumerate(rows(g)):
                print(f'{y:3d} {r}')

    out = [
        {
            "type": "mapgen",
            "om_terrain": [["svalbard_vault_entrance", "svalbard_vault_garage",
                            "svalbard_vault_mast"]],
            "//": "Surface: portal wedge with lit forecourt, garage, radio mast compound.",
            "object": {
                "fill_ter": "t_region_groundcover",
                "rows": rows(surface),
                "palettes": ["svalbard_vault_palette"],
                "place_nested": [
                    {"chunks": ["svalbard_vault_roof"], "x": 0, "y": 0, "z": 1},
                    {"chunks": ["svalbard_garage_roof"], "x": 24, "y": 0, "z": 1},
                    {"chunks": ["svalbard_shack_roof"], "x": 48, "y": 0, "z": 1}
                ],
                "place_vehicles": [
                    {"vehicle": "suv", "x": 31, "y": 12, "chance": 90, "rotation": 270, "status": 1, "fuel": 40},
                    {"vehicle": "humvee", "x": 39, "y": 12, "chance": 75, "rotation": 270, "status": 1, "fuel": 40},
                    {"vehicle": "pickup", "x": 34, "y": 1, "chance": 100, "rotation": 0, "status": 1, "fuel": 15}
                ],
                "place_monster": [
                    {"monster": "mon_svalbard_polar_bear", "x": 70, "y": 10, "chance": 75}
                ]
            }
        },
        {
            "type": "mapgen",
            "om_terrain": ["svalbard_warming_hut"],
            "//": "A log warming hut with a woodstove and an emergency cache.",
            "object": {
                "fill_ter": "t_region_groundcover",
                "rows": rows(hut),
                "palettes": ["svalbard_vault_palette"],
                "place_nested": [
                    {"chunks": ["svalbard_hut_roof"], "x": 0, "y": 0, "z": 1}
                ],
                "place_items": [
                    {"item": "svalbard_hut", "x": 14, "y": 13, "chance": 100, "repeat": [2, 3]}
                ],
                "place_monster": [
                    {"monster": "mon_svalbard_reindeer", "x": 18, "y": 18, "chance": 60},
                    {"monster": "mon_svalbard_reindeer", "x": 4, "y": 6, "chance": 40}
                ]
            }
        },
        {"type": "mapgen", "nested_mapgen_id": "svalbard_vault_roof",
         "object": {"mapgensize": [24, 24],
                    "rows": roof_chunk([(7, 2, 16, 19)]),
                    "palettes": ["svalbard_vault_palette"]}},
        {"type": "mapgen", "nested_mapgen_id": "svalbard_garage_roof",
         "object": {"mapgensize": [24, 24],
                    "rows": roof_chunk([(2, 4, 21, 20)],
                                       marks=[(6, 8, 'a'), (7, 8, 'a'),
                                              (15, 14, 'a'), (16, 14, 'a')]),
                    "palettes": ["svalbard_vault_palette"]}},
        {"type": "mapgen", "nested_mapgen_id": "svalbard_shack_roof",
         "object": {"mapgensize": [24, 24],
                    "rows": roof_chunk([(13, 12, 19, 17)]),
                    "palettes": ["svalbard_vault_palette"]}},
        {"type": "mapgen", "nested_mapgen_id": "svalbard_hut_roof",
         "object": {"mapgensize": [24, 24],
                    "rows": roof_chunk([(8, 8, 15, 14)]),
                    "palettes": ["svalbard_vault_palette"]}},
    ]

    quads = [('a', 'b', 'c'), ('d', 'e', 'f'), ('g', 'h', 'i')]
    levels = [
        ("sub1", sub1, m1, [],
         "z-1: egress — changing area, security, radio room, pool, sauna, gym, stores."),
        ("sub2", sub2, m2, [],
         "z-2: operations — offices, server room, ops centre, armory, brig, workshop, generators."),
        ("sub3", sub3, m3, [],
         "z-3: habitat — mess, kitchen, pantry, hydroponics, dorms, rec, chapel, library, infirmary, morgue."),
        ("deep", deep, m4,
         [{"item": "glass_shard", "x": 57, "y": 62, "amount": [2, 4]},
          {"item": "glass_shard", "x": 57, "y": 63, "amount": [1, 3]}],
         "z-4: the vault — five seed chambers, grand gallery, duty room (start), breached research wing."),
    ]
    # guaranteed crafting-chain spawns (see docs: warm clothing + archery chains)
    guaranteed = {
        "sub1": [
            {"item": "svalbard_note_security", "x": 35, "y": 5, "chance": 100},
            {"item": "compbow", "x": 54, "y": 26, "chance": 100},
            {"item": "arrow_cf", "x": 55, "y": 26, "chance": 100, "amount": [16, 24]},
            {"item": "towel", "x": 32, "y": 39, "chance": 100, "amount": [2, 3]},
            {"item": "hose", "x": 13, "y": 7, "chance": 100},
            {"item": "sewing_kit", "x": 50, "y": 28, "chance": 100},
            {"item": "thread", "x": 51, "y": 28, "chance": 100, "amount": [2, 3]},
            {"item": "pot", "x": 11, "y": 50, "chance": 100},
            {"item": "pan", "x": 12, "y": 50, "chance": 100},
        ],
        "sub2": [
            {"item": "tailors_kit", "x": 22, "y": 52, "chance": 100},
            {"item": "hacksaw", "x": 23, "y": 67, "chance": 100},
            {"item": "fire_ax", "x": 39, "y": 23, "chance": 100},
        ],
        "sub3": [
            {"item": "candle", "x": 13, "y": 24, "chance": 100},
        ],
        "deep": [
            {"item": "svalbard_note_duty", "x": 42, "y": 52, "chance": 100},
            {"item": "svalbard_note_lab", "x": 56, "y": 48, "chance": 100},
        ],
    }
    # Tool and book groups live OUTSIDE the shared palette on purpose:
    # they spawn only on the surface and z-1/z-2 — at least two levels
    # from the z-4 start — so the player must climb through danger to
    # tool up.  Chances are 0.8x the old palette values (the -20% pass).
    # z-3's library is empty because the crew burned the books (graffito).
    upper_level_items = {
        "u": {"item": "homebooks", "chance": 48, "repeat": [1, 2]},
        "n": {"item": "tools_common", "chance": 32},
        "c": {"item": "svalbard_tools", "chance": 40},
        "z": {"item": "mechanics", "chance": 40},
    }
    # per-level extra mapgen keys: wayfinding signs ('?'), the dead crew,
    # the working security terminal, and the pinned start point
    extras = {
        "sub1": {
            "signs": {"?": {"signage": "LEVEL 1 — SURFACE ACCESS.  Changing area · pool · gym · plant rooms.  Cold-weather gear MUST be worn beyond this point.", "furniture": "f_sign"}},
            "place_graffiti": [
                {"text": "PUMP DIED DAY 12.  LET IT FREEZE.", "x": 8, "y": 11},
                {"text": "E + M '41", "x": 33, "y": 38}
            ],
            "items": upper_level_items,
        },
        "sub2": {
            "signs": {"?": {"signage": "LEVEL 2 — OPERATIONS.  Server room · workshop · generator hall.  Armory access: security staff only.", "furniture": "f_sign"}},
            "computers": {
                "Z": {
                    "name": "Vault Security Terminal",
                    "security": 3,
                    "options": [
                        {"name": "Download Regional Survey Data", "action": "maps"},
                        {"name": "ARMORY LOCK OVERRIDE", "action": "unlock"}
                    ],
                    "failures": [{"action": "alarm"}, {"action": "manhacks"}, {"action": "damage"}],
                    "access_denied": "ERROR: NPRI-7 LOCKDOWN IN EFFECT.  Access restricted to security staff.  Report to your duty officer."
                }
            },
            "place_items": [
                {"item": "corpses", "x": 19, "y": 27, "chance": 100}
            ],
            "place_graffiti": [
                {"text": "IIII IIII IIII IIII IIII IIII IIII IIII II", "x": 4, "y": 38},
                {"text": "MAINLAND KNEW.  THEY ALWAYS KNEW.", "x": 25, "y": 28}
            ],
            "items": upper_level_items,
        },
        "sub3": {
            "sealed_item": {"H": {"items": {"item": "farming_seeds"}, "furniture": "f_plant_harvest"}},
            "signs": {"?": {"signage": "LEVEL 3 — HABITAT.  Mess · dormitories · infirmary · library.  Quiet hours 22:00–06:00.", "furniture": "f_sign"}},
            "place_items": [
                {"item": "corpses", "x": 6, "y": 60, "chance": 100},
                {"item": "corpses", "x": 62, "y": 50, "chance": 100},
                {"item": "corpses", "x": 11, "y": 34, "chance": 100},
                {"item": "corpses", "x": 12, "y": 26, "chance": 100},
                {"item": "corpses", "x": 58, "y": 26, "chance": 100},
                {"item": "corpses", "x": 63, "y": 25, "chance": 100}
            ],
            "place_graffiti": [
                {"text": "ST. OLGA, PROTECT WHAT KEEPS.", "x": 64, "y": 27},
                {"text": "DAY 38: OUT OF COFFEE.  MORALE CRITICAL.", "x": 5, "y": 7},
                {"text": "WE BURNED THE BOOKS IN FEBRUARY.  FORGIVE US.", "x": 58, "y": 35}
            ],
            "place_fields": [
                {"field": "fd_slime", "x": 46, "y": 42},
                {"field": "fd_slime", "x": 46, "y": 41},
                {"field": "fd_slime", "x": 47, "y": 42},
                {"field": "fd_blood", "x": 60, "y": 23},
                {"field": "fd_blood", "x": 59, "y": 25, "intensity": 2}
            ],
        },
        "deep": {
            "place_items": [
                {"item": "corpses", "x": 58, "y": 52, "chance": 100}
            ],
            "place_graffiti": [
                {"text": "THE SEEDS KEEP", "x": 40, "y": 54},
                {"text": "DO NOT FEED IT", "x": 50, "y": 52},
                {"text": "TRAP SET FOR WHAT COMES DOWN THE VENT — S.", "x": 45, "y": 41}
            ],
            "place_fields": [
                {"field": "fd_slime", "x": 57, "y": 62},
                {"field": "fd_slime", "x": 57, "y": 60},
                {"field": "fd_slime", "x": 58, "y": 59},
                {"field": "fd_slime", "x": 60, "y": 57},
                {"field": "fd_slime", "x": 59, "y": 55},
                {"field": "fd_slime", "x": 57, "y": 53},
                {"field": "fd_slime", "x": 55, "y": 51},
                {"field": "fd_slime", "x": 53, "y": 50},
                {"field": "fd_slime", "x": 51, "y": 48},
                {"field": "fd_slime", "x": 50, "y": 46},
                {"field": "fd_slime", "x": 48, "y": 45},
                {"field": "fd_slime", "x": 46, "y": 44},
                {"field": "fd_slime", "x": 44, "y": 43},
                {"field": "fd_slime", "x": 45, "y": 42},
                {"field": "fd_slime", "x": 46, "y": 42},
                {"field": "fd_blood", "x": 46, "y": 40},
                {"field": "fd_blood", "x": 47, "y": 41}
            ],
            "place_zones": [
                {"type": "ZONE_START_POINT", "faction": "your_followers", "x": [38, 40], "y": [54, 55]}
            ],
        },
    }
    # the surface garage/mast keep tool loot too (4+ levels from spawn)
    out[0]["object"]["items"] = {k: upper_level_items[k] for k in ("n", "c", "z")}

    for key, g, mons, shards, note in levels:
        # coordinate ops must land on walkable tiles, not walls/rock
        bad_ops = []
        for op in (extras.get(key, {}).get('place_graffiti', [])
                   + extras.get(key, {}).get('place_fields', [])
                   + extras.get(key, {}).get('place_items', [])
                   + guaranteed.get(key, []) + shards + mons):
            x, y = op['x'], op['y']
            if isinstance(x, int) and g[y][x] in WALLS:
                bad_ops.append((key, x, y, g[y][x]))
        if bad_ops:
            print(f'!! coordinate ops on wall tiles: {bad_ops}')
            sys.exit(1)
        obj = {
            "fill_ter": "t_rock",
            "rows": rows(g),
            "palettes": ["svalbard_vault_palette"],
            "place_monster": mons,
        }
        spawns = guaranteed.get(key, []) + shards
        if spawns:
            obj["place_item"] = spawns
        obj.update(extras.get(key, {}))
        out.append({
            "type": "mapgen",
            "om_terrain": [[f"svalbard_vault_{key}_{q}" for q in row]
                           for row in quads],
            "//": note,
            "object": obj
        })

    dest = Path(__file__).parent / 'dda-mods' / 'svalbard_seed_vault' / 'mapgen.json'
    dest.write_text(json.dumps(out, indent=2) + '\n')
    print(f'wrote {dest}')


if __name__ == '__main__':
    main()
