# Advanced CDDA mapgen techniques

Distilled from `doc/JSON/` in the CDDA checkout (MAPGEN.md, OVERMAP.md,
REGION_SETTINGS.md, ITEM_SPAWN.md) plus the official mapping guides at
docs.cataclysmdda.org. Read the relevant section here before reaching
for C++ or hand-rolling something — mapgen JSON is far more capable
than the basics suggest. Doc-site pages render straight from repo
master and are authoritative; pre-0.F forum/wiki guides predate
palettes-everywhere, JSON roofs, and regional terrain. Note: DDA and
BN mapgen have diverged (parametric palettes and mutable specials are
DDA-only); BN's parallel docs are at docs.cataclysmbn.org.

## Variants, weights, and om_terrain forms

- Several mapgen objects may target the same `om_terrain`; `"weight"`
  (default 1000, 0 disables) sets relative rarity. Weight can be
  dynamic: `{"global_val": "var"}` or a `math` expression.
- Testing trick: temporarily set `"weight": 10000000` to make your
  variant spawn everywhere.
- `"om_terrain": ["house", "house_base"]` = same mapgen for several
  ids (NOT multi-OMT); the nested-list form is the multi-OMT grid.
- Terrains flagged `LINEAR` (roads, tunnels) need one mapgen per
  suffix: `_end`, `_straight`, `_curved`, `_tee`, `_four_way`.

## Parameters and parametrized palettes

- Roll-once-reuse randomization:
  `"parameters": {"wall_type": {"type": "ter_str_id", "scope": "omt",
  "default": {"distribution": [["t_concrete_wall",2],["t_scrap_wall",1]]}}}`
  then `"terrain": {"|": {"param": "wall_type"}}`.
- Scopes: `overmap_special` (default), `omt`, `nest`, `omt_stack`
  (shared across z — use to align materials/nests vertically).
  `overmap_special`/`omt_stack` scopes REQUIRE a `"fallback"` at every
  use site (savegame migration).
- `{"switch": {"param": "fence_type", "fallback": "..."}, "cases": {...}}`
  derives matching ids (gate matching the rolled fence).
- Stock parametrized palettes in
  `data/json/mapgen_palettes/common_parameters.json`:
  `parametrized_walls_palette`, `_fences_`, `_linoleum_`, `_carpets_`,
  `roof_palette`, `domestic_general_and_variant_palette`.
- Palettes themselves can be rolled:
  `"palettes": [{"distribution": [["cabin_palette",1],["cabin_palette_abandoned",1]]}]`
  — special-scoped, so all OMTs of one special pick the same look.
- Override rules: last-listed palette wins for terrain/furniture;
  the mapgen object overrides palettes; additive mappings (items,
  fields) stack. `t_null`/`f_null` remove an inherited definition.
  A mod palette with `"extending": true` merges into the vanilla one.

## Layering and predecessors

- `"predecessor_mapgen": "forest"` generates the natural terrain
  first, then overlays yours — cabins that track the local biome.
  `"fallback_predecessor_mapgen"` uses whatever was there (for
  specials placeable on several biomes); still needs a literal
  fallback for migration.
- Changing tiles that already carry furniture/traps/items is an ERROR
  unless you set a layer-clearing flag: `ERASE_ALL_BEFORE_PLACING_TERRAIN`
  / `DISMANTLE_ALL_...` / `ALLOW_TERRAIN_UNDER_OTHER_DATA` (mutually
  exclusive), or fine-grained `*_FURNITURE_*`/`*_TRAP_*`/`*_ITEMS_*`.
  Gotcha: these flags silently do nothing at negative z offsets.
- Other flags: `AVOID_CREATURES` (skip tiles occupied by a creature),
  `SKIP_ON_OPEN_AIR`, `NO_UNDERLYING_ROTATE`.

## The `set` array and surgical ops

- Ordered point/line/square ops: `terrain`, `furniture`, `trap`,
  `radiation`, `variable`, `bash` (one guaranteed bash), `burn`, and
  removals `trap_remove`/`item_remove`/`field_remove`/`creature_remove`.
  Support `chance` (1-in-N) and `repeat`. In multi-OMT maps `set`
  entries repeat in EVERY OMT — avoid them there.
- `remove_all` wipes fields+items+traps+graffiti+furniture from a
  tile; `traps`/`fields` accept `"remove": true`.
- `ter_furn_transforms` runs a transform id over a range in-mapgen.

## Placement ops beyond the basics

- `place_monster` `spawn_data`: pre-loaded ammo
  (`{"ammo": [{"ammo_id": "556", "qty": [20,30]}]}`) and `patrol`
  waypoints (relative map-square offsets; may point into adjacent
  OMTs). `place_monsters` (plural) guarantees every group entry —
  count is hard to control on big groups.
- `place_corpses`: `{"group": "GROUP_PETS", "age": 3}` (days).
- `place_loot`: the only op spawning a SINGLE item from a
  distribution group; `ammo`/`magazine` are x-in-100 include chances.
- `computers` / `place_computers`: interactive consoles —
  `{"name": "...", "security": 3, "options": [{"name": "Unlock",
  "action": "unlock"}], "failures": [{"action": "alarm"}],
  "eocs": [...], "chat_topics": [...]}`. Actions/failures are the
  hardcoded set in `computer_session.cpp`; security rolls vs computer
  skill + INT. Define `options` OR `eocs`+`chat_topics` or it's inert.
- `sealed_item`: the only way to put the hidden seed item on
  `PLANT`-flag furniture (`f_plant_harvest`).
- `vendingmachines` (`powered`, `lootable`, `reinforced`), `gaspumps`
  (`fuel`: gasoline/diesel/jp8/avgas), `place_liquids` (spilled fuel
  flavor).
- `place_item` flag `ACTIVATE_ON_PLACE`: pre-armed items (noisemaker
  traps, lit dynamite).
- `faction_owner` marks a box of spawned items as faction property
  (theft flagging); item/vehicle ops also take per-op `"faction"`.
- Vehicles: `status` -1 light damage (default) / 0 undamaged /
  1 heavy / 2 pristine+security-disabled; `fuel` -1 = fumes, else %.
  A vehicle must fit inside one OMT — straddling a 24-tile boundary
  silently fails to spawn.
- Zones: `NPC_RETREAT`/`NPC_NO_INVESTIGATE`/`LOOT_*` steer NPC AI. A
  `ZONE_START_POINT` zone owned by `your_followers` sets the scenario
  spawn tile (no validity check — can drop the player in a wall).

## Conditional nests

- `place_nested` conditions: `"neighbors"` (per-direction om_terrain
  substring match; `om_terrain_match_type` PREFIX/SUBTYPE...),
  `"flags"`/`"flags_any"` (oter flags per direction, incl. above/
  below), `"joins"`, `"predecessors"`, `"check_z"`; `"else_chunks"`
  fires on failure. This is the biome-transition/edge-walling tool.
- Nest conventions that make nests reusable: name with size +
  orientation (`room_9x9_recroom_N`), keep corners empty so parents
  can place doors, include a weighted `"null"` chunk so the nest can
  not-spawn (rare encounters), `t_null` passes parent terrain through.
  Nests never link z-levels — roofs belong to the parent.

## update_mapgen, missions, map extras

- `{"type": "mapgen", "update_mapgen_id": "mx_x", "object": {...}}`
  mutates an EXISTING OMT — the engine for EOC/mission-driven map
  changes and faction-camp construction. Same fields as normal mapgen
  plus the layer-clearing flags.
- Mission targeting: `"assign_mission_target": {"om_terrain": "...",
  "om_special": "..."}`; `place_npc/monster/computer` accept
  `"target": true` under a mission-invoked update.
- Map extras: `{"type": "map_extra", "generator":
  {"generator_method": "update_mapgen", "generator_id": "mx_x"}, ...}`
  — must ALSO be wired into `region_settings.map_extras` (per-biome
  weighted list) or it never spawns.

## Overmap: placement, connections, mutable specials

- `occurrences` minimum should essentially always be 0: minima are NOT
  enforced in worldgen but ARE enforced by CI tests
  (`default_overmap_generation_always_succeeds`) — a nonzero min
  breaks tests, not guarantees spawns. Non-unique specials place far
  more often than intuition suggests; for "rare but present" use flag
  `OVERMAP_UNIQUE` (occurrences becomes an x-in-y chance, convention
  `[x, 100]`) or `GLOBALLY_UNIQUE`.
- `"connections": [{"point": [1,-1,0], "connection": "local_road",
  "from": [1,0,0]}]` auto-builds a road from the nearest network to
  that edge point (point must lie OUTSIDE the special's own OMTs) —
  this is how to guarantee a route toward civilization.
  `"existing": true` only validates against pre-existing terrain and
  sharply lowers spawn chance if the target is rare.
- A points entry `"camp": "<faction>", "camp_name": "..."` spawns an
  NPC basecamp. `"priority"` reorders generation for hard-to-place
  specials (SAFE_AT_WORLDGEN specials deserve priority 1).
- Avoid box-drawing symbols (│─┌) on rotatable overmap terrain — they
  render wrong under rotation. Prefer `overmap_location` ids over raw
  terrain lists in `locations`.
- Mutable specials (`"subtype": "mutable"`): jigsaw growth via
  `overmaps` pieces with per-edge join ids, a `root`, and weighted
  `phases`. Joins may be `mandatory` (default) or `available`, with
  `alternatives`. Placement errors out if mandatory joins go
  unsatisfied — give low-join "cap" pieces high weight in the final
  phase. Reference: `data/json/overmap/overmap_mutable/`,
  `tests/overmap_test.cpp` (`mutable_overmap_placement`).

## Item groups, advanced

- Sealed containers: group-level `"container-item"` +
  `"on_overflow": "discard"|"spill"`; entry-level `"container-group"`
  + `"sealed"`; `count: -1`/`charges: -1` fill the container;
  `"entry-wrapper"` packs non-stackables into one container.
- `"ammo-item"`, `"ammo": 100`/`"magazine": 100` (x-in-100) only
  apply to tools/guns/mags; `charges` on a multi-pocket entry is
  rejected with a debugmsg.
- Entry extras: `"faults"`, `"variables"`, `"snippets"`,
  `"damage": [0,3]`, `"event": "christmas"` (real-world-date gated).
- Prefer reusable SUS ("specific use storage") groups for furniture.

## Review standards for upstream-quality locations

- Reuse standard palettes (`standard_domestic_variant_palette` for
  houses, parametrized wall/roof palettes); never casually edit a
  shared palette — override symbols in your mapgen object instead.
  Upstream actively converts inline definitions to palettes (issue
  #62747) and pushes back on new inline submissions.
- Every building gets a JSON roof (`<building>_roof`), reachable via
  1–2 `t_gutter_downspout` (staggered per floor on multi-story).
- Regionalize exterior terrain (`t_region_groundcover_urban` etc.) so
  the map blends into any biome.
- Loot philosophy (design-balance doc): distribute goods as they'd
  exist in reality; if that's unbalanced, tune ENEMIES, not loot —
  junk plentiful, ideal tools rare. Loot tells the story of the place.
- Symbol-based `items` chance applies to EVERY instance of the symbol
  — the leading cause of over-generous loot. Coordinate ops for
  specific tiles.
- Monster ambience is moving to `overmap_terrain` `mondensity`;
  reserve explicit mapgen spawns for scripted encounters. `place_npc`
  guarantees spawn; wrap optional NPCs in weighted nests.
- Keep mapgen file entry order matching existing maps (metadata →
  palettes → set → terrain → furniture → toilets/sealed → items →
  vehicles → monsters). Run the bundled `json_formatter` before PRs.
- Good single-OMT reference map: `data/json/mapgen/fire_station.json`.

## In-game testing loop

- Bind the Debug menu key, then: Reveal map → find your special;
  long-range teleport accepts exact OMT coords; overmap editor (`s`)
  force-places a special on ungenerated areas; `spawn nested map`
  tests nests in isolation; the in-game map editor repaints tiles
  without JSON edits.
- Exiting to the main menu and reloading re-reads most JSON — no full
  restart needed while iterating.
- QA pass before shipping: walk the map and SMASH every furniture
  piece — furniture over non-default floor without a terrain mapping
  reveals the wrong floor underneath (the classic newbie bug we also
  hit as furniture-on-rock). Verify vehicles in-game (origin points
  vary by model).
- External tools worth knowing: `mapgen_explorer` (two-way JSON↔
  visual editing), CDDA-Map-Editor-v2, and the Hitchhiker's Guide
  (cdda-guide.nornagon.net) for fast id lookup.
