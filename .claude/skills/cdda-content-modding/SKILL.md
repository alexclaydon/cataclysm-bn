---
name: cdda-content-modding
description: How to build Cataclysm-DDA content mods in this repo — multi-level maps (mapgen), overmap specials, palettes, item groups, scenarios, professions, weather/region overlays, and EOCs — and deploy/validate them on the Steam Deck. Use whenever creating or modifying CDDA levels, buildings, dungeons, starting scenarios, or loot, including any work under build-scripts/dda-mods/ or on the Svalbard vault mod. Distilled from building the five-level "The Last Deposit" vault; full of validated ids and traps that grep-first discipline caught and the validator did not.
---

# CDDA level & mod authoring

CDDA mods for our Deck install live in `build-scripts/dda-mods/<mod_id>/`
in THIS repo (the BN repo is the config home). The CDDA source checkout
at `~/dev/cataclysm-dda` (Nova) is the reference: **grep it before using
any id, field, or syntax** — this discipline caught every would-be
runtime bug this workflow has produced; guessing ids caused every other
one. Shell gotcha when verifying: `grep -rl x | head -1 || echo MISSING`
never prints MISSING (head exits 0 regardless) — use
`r=$(grep -rl x ...); echo "${r:-MISSING}"` so absence is visible. Format docs: `doc/JSON/` in that checkout (MAPGEN.md,
OVERMAP.md, ITEM_SPAWN.md, WEATHER_TYPE.md, EFFECT_ON_CONDITION.md).

Worked example of everything below: `svalbard_seed_vault` (five z-levels,
3×3-OMT floors, research-wing storyline, guaranteed crafting chains).

**references/advanced-mapgen.md** catalogs the advanced machinery with
syntax and gotchas — read it before designing anything non-trivial:
weighted mapgen variants, parametrized palettes (roll-once wall/floor
randomization), predecessor_mapgen, layer-clearing flags, interactive
computers, sealed containers, update_mapgen/missions/map extras,
auto road `connections` on specials, mutable (jigsaw-growth) specials,
conditional nests, upstream review standards, and the in-game debug
testing loop. Many "needs C++" instincts are wrong — check there first.

## The two-stage validation trap (learn this first)

1. `--check-mods` (run via ssh on the Deck) catches missing ids, bad
   enums, structural errors. Run it after every change:
   `ssh steamdeck 'cd ~/cataclysm-dda && distrobox enter bn-dev -- ./cataclysm-tiles --check-mods <mod_id>'`
2. It does NOT run the strict field checker. Wrong-but-well-formed
   fields ("invalid or misplaced field name") only surface as yellow
   warnings at game launch. After the user plays, check
   `ssh steamdeck 'grep -i "json error\|invalid or misplaced" ~/cataclysm-dda/config/debug.log'`.

Classic instance: item_group entries take `"count"` for quantity —
`"repeat"` is mapgen-placement vocabulary (valid in palette `items`,
`place_items`, `place_loot`). Mixing them passes --check-mods and warns
at launch.

## Generated maps, not hand-typed ones

Maps ≥48×48 are authored via a Python generator (see
`build-scripts/gen-svalbard-mapgen.py`), never by hand-editing rows.
The generator pattern that works:

- Compose from primitives: `room()`, `hwall/vwall`, `fill`, `put`,
  `door` over a char grid; corridors as fixed bands (e.g. rooms in
  y2..19 / y22..43 / y46..69 with 2-wide corridors between).
- **Flood-fill connectivity check**: every non-wall tile reachable from
  the stairs, or refuse to emit. This catches missing doors instantly
  and is the reason big layout edits are cheap.
- **Anchor table for vertical alignment**: stairs/ladders between
  z-levels must share absolute (x,y). Keep one table of anchors, assert
  `>`/`<` and `v`/`^` pairs across level grids before writing JSON.
- `--preview` prints indexed ASCII grids for eyeballing; do that after
  any layout change. Trust the checks over eyeball column-counting.
- The generator runs offline on Nova, output committed as static JSON.
  Never hand-edit the generated mapgen.json.

## Mapgen facts (all verified in anger)

- Multi-OMT maps: `"om_terrain": [["a","b"],["c","d"]]` with rows
  24·cols wide and 24·rows tall. Each cell id needs its own
  `overmap_terrain`. Coordinates in `place_*` are absolute in the big
  grid, BUT a ranged coordinate (`"x": [10, 30]`) and a vehicle
  footprint must each stay inside ONE 24-tile OMT — crossing a
  boundary is an error (ranges) or a silent no-spawn (vehicles).
  `set`-array entries repeat in every OMT of a multi-OMT map; avoid
  them there.
- Nested chunks (`place_nested`) must be SQUARE (`mapgensize` [n,n],
  n ≤ 24); spaces in their rows are no-ops. Roofs = nested chunk of
  `t_flat_roof` placed with `"z": 1`.
- Stairs (`t_stairs_up/down`) link at identical x,y on adjacent levels.
  Ladders (`t_ladder_up/down`) too — for a shaft through several
  levels use two adjacent tiles and alternate which carries up/down per
  level, so every descent lands on an up-ladder.
- Guaranteed spawns: `"place_item"` (single item, `chance: 100`,
  `amount`) — use for crafting-chain essentials. Group spawns:
  `"place_items"` (group id + chance/repeat) or palette `items`
  (per-char, `chance`, `repeat`). Monsters:
  `"place_monster": [{"monster": "mon_x", "x":.., "y":..}]`.
  Vehicles: `"place_vehicles"` (rotation, status, fuel).
- Fields via palette `"fields": {"*": {"field": "fd_blood", "intensity": 1}}`
  — blood trails are cheap environmental storytelling. Signs via
  palette `"signs": {"$": {"signage": "...", "furniture": "f_sign_warning"}}`.
- `t_utility_light` is self-lit floor — sprinkle in corridors/key rooms
  so underground/eternal-night maps stay playable.
- Rooms CAN span two z-levels: fill the upper level's footprint with
  `t_open_air` and run `t_metal_floor` catwalks edged with `t_railing`
  across it (vanilla silos/atria do this). Both levels must belong to
  your special, and any stairs landing there need a solid platform.
  Works underground.
- Floor variety sells a map (wood `t_floor`, `t_linoleum_white`,
  `t_grate`, `t_metal_floor`) — but each palette symbol has ONE
  terrain, so a furniture char's floor must match the room type it
  usually appears in; room-specific furniture (beds→wood, kitchen/med
  →linoleum, machinery→grate) works, ubiquitous chars (counters,
  desks) stay on the default floor and read as equipment pads.
- `fill_ter` fills every cell without terrain. **Every furniture char
  in the palette needs an explicit terrain entry** (e.g.
  `t_thconc_floor`), or the furniture sits inside the fill terrain
  (racks embedded in solid rock — no validator catches it).

## Sprites for custom content (looks_like)

Custom overmap_terrain ids render as ASCII fallback in EVERY tileset —
players read this as "my tileset is broken", especially when the whole
explored map is your special. Give every custom oter (and custom item)
a `"looks_like": "<vanilla id with sprites>"` donor (verify the donor
id exists — e.g. `bunker`, `garage_gas_1`, `cabin_aban1`, `lmoe_under`;
there is no vanilla `radio_tower`/`cabin`/`lab` oter). looks_like
resolves at render time, so existing worlds pick it up on relaunch.
It's cosmetic borrowing — bespoke art means a tileset extension.

## Interactive computers (verified behavior)

- Char-based: palette gives the char `f_console` furniture; the mapgen
  object's `"computers": {"Z": {...}}` makes it interactive.
- Action ids are the hardcoded set in `computer_session.cpp` — grep it
  before using one. Useful generic ones: `"maps"` (reveals surrounding
  overmap — great "find the town" reward), `"unlock"`, failure
  `"alarm"`.
- `"unlock"` converts `t_door_metal_locked` (NOT elocked) within 8
  tiles OF THE PLAYER — the terminal must physically sit near the door
  it opens, or the option never appears.
- Gating trap: when you lock a door, check nothing *guaranteed* (chain
  tools, `place_item` 100% spawns) sits behind it — gate rewards, not
  requirements.

## Overmap specials

- One `overmap_terrain` per OMT id; useful flags: `KNOWN_UP`/
  `KNOWN_DOWN` (only where stairs actually are), `SOURCE_FOOD`,
  `SOURCE_SAFETY`. `see_cost` is an enum (`none`, `all_clear`,
  `medium`, `high`, `spaced_high`, `full_high`) — invalid values are a
  load error.
- Special points: `{"point": [x,y,z], "overmap": "<id>_north"}`.
  **Underground points MUST set `"locations": ["subterranean_empty"]`**
  — they otherwise inherit the special's surface locations (e.g.
  `wilderness`) and placement silently fails, i.e. the special never
  spawns and nothing tells you why.
- Points don't need to be contiguous and may use negative offsets —
  that's how to guarantee satellite structures near the main site
  (warming huts around the vault). Every extra surface point adds a
  placement constraint; keep satellites few.
- `city_distance`/`city_sizes` control town proximity (min ≥ N keeps
  towns away; [3,30] reliably puts one nearby). `city_distance`
  measures from the city's EDGE (urban radius), nearest city only.
  Coastal placement cannot be forced from a mod.
- `occurrences` minima are NOT enforced in worldgen (only in CI
  tests) — keep the minimum 0 for upstream-quality work. Non-unique
  specials place far more often than intuition suggests; for "rare
  but present", use flag `OVERMAP_UNIQUE` (occurrences then means an
  x-in-y chance, conventionally `[x, 100]`).
- A special can demand a road: `"connections"` with a point outside
  its own OMTs auto-builds one from the nearest road network (see
  references/advanced-mapgen.md).
- Existing worlds keep their overmap: id changes/renames require a NEW
  world to see (and break old saves that referenced removed ids).

## Region/weather overlays & scenario glue

- `weather_generator` id `default` + `copy-from: default` overlays the
  world climate. **`base_temperature` doubles as the constant
  underground temperature** (weather.cpp `get_temperature`, z<0): keep
  it ~+4 °C or all-underground starts freeze solid and crafting locks
  out. Make the surface cold with the outdoor-only
  `winter/spring/summer/autumn_temp_manual_mod` fields instead.
- `weather_white_list`: a weather type only occurs if its
  `required_weathers` chain is whitelisted too (snowstorm needs
  thunder/lightning kept in the list).
- Non-stub `EXTERNAL_OPTION` in a mod overrides built-in world options
  (e.g. `ETERNAL_TIME_OF_DAY` = "night" for polar night; Aftershock
  uses the same trick for DEFAULT_REGION).
- Scenario: `start_of_cataclysm` / `start_of_game` (hour/day/season/
  year), `distance_initial_visibility: 0` for no map knowledge,
  `"eoc"` array runs at character creation — good for weather math
  (`weather('temperature') = from_fahrenheit(x)`, `"next_weather"`) and
  a scene-setting `u_message` popup. `start_location.terrain` = OMT id
  the player spawns in (pick the quadrant containing the start room).
- Professions: item entries use `count`/`charges`;
  `{"group": "charged_flashlight"}` is the stock way to grant a lit
  flashlight. A dark start needs light in EVERY profession.
- Pin the exact spawn tile with mapgen
  `"place_zones": [{"type": "ZONE_START_POINT", "faction":
  "your_followers", "x": [38,40], "y": [54,55]}]` (ranges must stay in
  one OMT; no validity check — put it on known-open floor). Without it
  the player spawns on any valid tile of the start OMT.
- The dead crew: `place_items` with the stock `"corpses"` item group
  spawns generic non-reviving human remains. `place_corpses` with a
  monster group makes corpses OF those monsters — zombie-group corpses
  can revive; don't ambush your own start location by accident.
- Scripted story beats: clone `survnote`'s ITEM definition with a
  fixed `description` (drop `snippet_category`) and `place_item` it at
  100% — guaranteed exact text, vs snippets which draw randomly from a
  category (better for repeatable flavor than for a specific arc).

## Id spelling minefield (all confirmed by grep)

- Rags are `cotton_patchwork`; cloth resources are `sheet_cotton`,
  `sheet_felt`, `leather`, `fur`. No `knife_utility` — use
  `knife_hunting`/`knife_combat`. It's `balclava` (sic), `socks_wool`.
- Consoles are FURNITURE now: `f_console`, `f_console_broken`.
- No shattered-glass wall terrain: represent a breach as a gap in
  `t_reinforced_glass` walls + `glass_shard` items + blood fields.
- No vanilla snowmobile vehicle, no overhead/garage door terrain (use
  `t_door_metal_c` pairs). `t_wall_log`, `t_window`, `t_door_c` for
  cabins; `t_chainfence`/`t_chaingate_c`; `t_radio_tower`.
- Rich verified furniture: `f_lab_bench`, `f_autoclave`, `f_fume_hood`,
  `f_centrifuge`, `f_gun_safe_el`, `f_standing_tank`, `f_crate_c`,
  `f_woodstove`, `f_planter`, `f_treadmill`, `f_ergometer`,
  `f_punching_bag`, `f_foot_locker`, `f_server`, `f_freezer`.
- Useful stock item groups: `kitchen`, `office`, `gym`, `cannedfood`,
  `mechanics`, `dresser`, `bed`, `homebooks`, `magazines`, `chem_lab`,
  `science`, `tools_common`, `archery`, `farming_seeds`,
  `charged_flashlight`. Prefer these over inventing groups; custom
  groups only for thematic loot.
- Weak/atmospheric threats for a start location: `mon_blob_small`,
  `mon_breather` (near-harmless nether flavor), `mon_manhack`,
  `mon_zombie_scientist`.

## Design lessons (what made the vault good)

- **Guarantee the chains**: decide what the player must be able to do
  (sew warm clothes, build a bow, boil water) and `place_item` the
  bottleneck tools at 100%; groups provide the redundancy on top.
- **Size ratio**: balance big set-piece halls with strips of small
  rooms (dorm cells, offices, closets); pure big-room floors feel
  empty. Vary room *types* per floor theme (egress / operations /
  habitat / payload).
- **Make traversal a journey**: put each level's up-stairs on the
  opposite side from its down-stairs so escape crosses every floor.
- **Threats sparse at a start location**: a handful of weak monsters
  across huge floors, placed where the story says they'd be.
- **Storytell with the fabric**: blood-field trails, breached glass,
  a warning sign, one locked gun safe — no dialogue needed.

## In-game iteration (faster than restart cycles)

- Exiting to the main menu and reloading the save re-reads most JSON —
  no relaunch needed between content tweaks.
- Debug menu (bind its key first): Reveal map to find your special,
  long-range teleport (takes exact OMT coords), overmap editor to
  force-place a special on ungenerated land, `spawn nested map` to
  test nests in isolation. Temporarily setting a mapgen `"weight"`
  absurdly high makes a variant spawn everywhere for inspection.
- QA pass before shipping: walk the map and smash furniture — a
  furniture symbol without its own terrain mapping reveals the wrong
  floor underneath (the classic bug; we shipped it once as racks on
  solid rock). Verify vehicles in-game — origins vary by model.
- Loot sanity: a symbol-based `items` chance applies to EVERY
  instance of that symbol; dense symbols multiply loot fast. Balance
  philosophy upstream: loot mirrors pre-Cataclysm reality — tune
  enemies, not loot, and let junk outnumber ideal tools.

## Deploy loop

`make deck-dda` does everything (scp scripts+keybindings+mods, git pull,
rebuild). For mod-only iteration skip the rebuild:
`scp -r build-scripts/dda-mods steamdeck:cataclysm-dda/ && ssh steamdeck 'cp -r ~/cataclysm-dda/dda-mods/. ~/cataclysm-dda/mods/'`
then run --check-mods (above). Mods land in `~/cataclysm-dda/mods/`
(user mod dir, untracked, pull-safe). JSON-only changes need only a
game relaunch; overmap-structure changes need a new world. Commit to
BOTH remotes (origin + forgejo). Long builds: background task, and
never overwrite a shell script while it runs (copy first).
