# Game data layer (data/, gfx/, mods)

~2900 JSON files; 1909 under `data/json/` (the core content).

## Layout

- `data/json/` — core game content; this IS the core mod (`bn`), whose
  `data/mods/bn/modinfo.json` has `"core": true, "path": "../../json"`.
- `data/mods/` — 84 bundled first-party mods (each with `modinfo.json`).
  Default-enabled set: `data/mods/default.json`.
- `data/raw/` — engine bootstrap (colors, fonts, keybindings, tips) +
  Lua docgen scripts. `data/lua/lib/` — shared Lua stdlib.
- `data/shaders/` — precompiled GPU shaders (gitignored; from CI).
- `gfx/<TilesetName>/` — tilesets (`tileset.txt` + `tile_config.json` +
  PNG sheets); default is MSX++UnDeadPeopleEdition ("UDP").
- `data/sound/Basic/` — bundled soundpack. Root-level `mods/` and
  `sound/` are user drop-dirs, distinct from `data/mods|sound`.

## data/json organization (where to put/find content)

items/ (373 files, by class: ammo/ armor/ gun/ tool/ comestibles/ …),
monsters/ (by theme: zed-*.json, nether.json…), monstergroups/,
recipes/ (by category), mapgen/ (661 files, one per building; palettes
in mapgen_palettes/), overmap/, npcs/ (NC_*.json classes, dialogue per
faction), mutations/, vehicles/ + vehicleparts/,
furniture_and_terrain/ (furniture-*.json / terrain-*.json), itemgroups/
(loot tables), requirements/ (shared crafting blocks), construction/,
snippets/, obsoletion/ (migrations for removed ids).

Norm: a new item that should appear in the world needs an itemgroup
entry (loot tables) and/or a recipe; craft-only items can skip
itemgroups. Debug menu can spawn anything for testing either way.

Every file is a JSON array of objects; every object has `"type"`; most
have `"id"` (or `"abstract"`).

## Inheritance (copy-from system)

Canonical doc: `docs/en/mod/json/reference/items/json_inheritance.md`.

- `copy-from` — inherit all fields from a same-type object; same id +
  copy-from = override the original.
- `abstract` — template-only object (no id, discarded after load).
- `extend` / `delete` — append to / remove from inherited list fields
  (e.g. flags, effects).
- `relative` / `proportional` — offset / scale inherited numeric fields.
- copy-from only works for C++ types backed by `generic_factory`.

Flags are string arrays; catalog in `data/json/flags.json` and
`docs/en/mod/json/reference/json_flags.md`.

## Validation & formatting (data edits)

- Style formatter: `just fmt-json <files>` or
  `build-scripts/format-json.sh` (builds the `json_formatter` C++ tool
  on first run). `data/names/` excluded.
- Parse check: `just lint-json`. Dialogue check: `just lint`.
- Game-load validation (needs a built binary, run from repo root):
  - `<binary> --jsonverify` — validates all core JSON, no window.
  - `<binary> --check-mods [ids…]` — validates mods (default set if
    no args).
- Data changes need NO recompile — relaunch the game to test. New
  content usually needs a new world (or spawn via debug menu).

## Mods

- `modinfo.json` = a `MOD_INFO` object: id, name, category,
  dependencies (load order is topological; everything depends on `bn`),
  optional `obsolete`, `lua_api_version: 2`.
- Mod content overrides core via copy-from/extend/delete.
- Third-party mods are bundled at release time from the online registry
  (mods.cataclysmbn.org) by `build-scripts/bundle-registry-mods.ts` —
  not committed to the repo.
- Removed content needs migration entries in `data/json/obsoletion/`
  (`type: MIGRATION`) so old saves keep loading.

## Lua modding

- Mod entrypoints, auto-discovered: `preload.lua` (register hooks),
  `main.lua`, `finalize.lua`.
- Hook API: `game.add_hook("on_<event>", fn)` — ~40 hooks (on_game_save,
  on_creature_spawn, on_character_try_move, on_every_x, dialogue
  hooks…). Doc: `docs/en/mod/lua/hooks.md`.
- Example minimal Lua mod: `data/mods/Spawn_Hook_Test/`. Bigger ones:
  `rpg_system`, `smart_house_remotes`, `skills_through_kills`.
- Lua API reference (`docs/en/mod/lua/reference/lua.md`) is generated
  from a built binary (`deno task docs:gen`, `$CATA_EXE --lua-doc`).
- `gdebug.log_info()` for logging; in-game Lua console exists.

## Key JSON reference docs (docs/en/mod/json/)

- `reference/json_info.md` — master overview (units, time syntax,
  every top-level field).
- `reference/items/item_creation.md`, `recipes.md`, `item_spawn.md`
- `reference/creatures/monsters.md`, `mutations.md`, `npcs.md`,
  `missions_json.md`, `magic.md`
- `reference/map/mapgen.md`, `overmap.md`, `region_settings.md`
- `reference/mod_info.md`, `explanation/loading_order.md`,
  `explanation/json_style.md`, `explanation/game_balance.md`

## Utility tools

`tools/json_tools/` (cddatags.py for JSON ctags, keys/values/pluck
query tools), `tools/copy_from.py`, `tools/dialogue_validator.py`,
`tools/gfx_tools/`, `tools/vehicleDef.py`. (`tools/` is nominally
legacy — new tooling goes in `scripts/` — but these remain active.)
