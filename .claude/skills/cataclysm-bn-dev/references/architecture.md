# C++ architecture (src/)

Scale: ~414 .cpp + 461 .h directly in src/ (~417k lines of .cpp).

## Central files and subsystems

| Subsystem | Key files |
| --------- | --------- |
| Game orchestration | `src/game.cpp` (16.8k lines; singleton `g`), game loop = `game::do_turn()` at src/game.cpp:1988 |
| Map / world | `map.cpp`, `mapdata.cpp`, `mapbuffer.cpp` (tile persistence), `mapgen*.cpp`, `overmap*.cpp`, `submap.cpp`, `src/map/utils/` |
| Creatures | `creature.cpp`, `monster.cpp`, `monattack.cpp`, `monmove.cpp`, `mongroup.cpp`, `monstergenerator.cpp`, `mtype.h` |
| Characters/NPCs | `character.cpp` (12.7k), `npc*.cpp`, `newcharacter.cpp`, `bionics.cpp`, `mutation*.cpp` |
| Items | `item.cpp` (12k), `item_factory.cpp`, `itype.h`, `iuse.cpp`/`iuse_actor.cpp` (use behaviors), `inventory*.cpp` |
| Vehicles | `vehicle.cpp`, `vehicle_part.cpp`, `veh_*.cpp`, `vpart_*.cpp` |
| UI / rendering | `sdltiles.cpp`, `cata_tiles.cpp` (7.5k), `panels.cpp`, `output.cpp`, `input.cpp`, catacurses layer; GPU compute in `src/compute/` (`gpu_lm.cpp`, `gpu_transparency.cpp`) |
| Save/load | `savegame.cpp` (`game::serialize`/`unserialize`), `savegame_json.cpp` (object-level), `savegame_legacy.cpp`, `worldfactory.cpp` |
| Terrain interaction | `iexamine.cpp` |
| Magic | `src/magic/`, `src/enchantments/` |

## Entry points

- `src/main.cpp:224` `main()`: crash handlers → PATH_INFO → CLI args →
  config preload → language → options → SDL init → `g->load_static_data()`
  (JSON loading, main.cpp:844) → main menu (`src/main_menu.cpp`).
- JSON loading hub: `src/init.cpp` — `DynamicDataLoader::initialize()`
  registers every JSON `"type"` string → loader function
  (`add("type", &loader)`); `load_object()` dispatches by `"type"`;
  `load_deferred()` handles ordering. Also `finalize_loaded_data()`,
  `check()` (consistency), `unload_data()`.

## Core patterns (must-know)

- **IDs**: `string_id<T>` (stable JSON handle) / `int_id<T>` (fast runtime
  index); aliases in `src/type_id.h` (`itype_id`, `mtype_id`, `ter_id`…).
  `.obj()` to dereference, `.is_valid()` to check.
- **JSON deserialization**: `JsonObject`/`JsonIn`/`JsonArray` from
  `src/json.h`. Convention: each type has
  `void load( const JsonObject &jo, const std::string &src )` and a
  `bool was_loaded`. Helpers in `src/assign.h` and
  `src/generic_readers.h` (`mandatory`, `optional`, reader types).
- **`generic_factory<T>`** (`src/generic_factory.h`): the canonical
  registry for JSON-defined types. Requires `load()`, `id`, `was_loaded`.
  Items and monsters have bespoke factories (`Item_factory`,
  `MonsterGenerator`) following the same idea.
- **Units**: `src/units.h` — typed quantities (mass, volume, energy,
  length, temperature, angle) with literals. Never bare ints for
  physical quantities.
- **Time**: `src/calendar.h` — `time_point`/`time_duration` with literals
  `1_turns`, `1_seconds`, `1_minutes`, `1_hours`, `1_days`.
- **Translations**: `_( msg )`, `pgettext( ctxt, msg )`, `vgettext`
  (plurals) from `src/translations.h`; `translate_marker()` for static
  tables; `translation` class + `to_translation()`/`no_translation()`
  for stored strings.
- **Containers/idioms**: `detached_ptr<T>`, `shared_ptr_fast<T>`,
  `cata::flat_set`, `enum_bitset`, `cata_variant`; bundled {fmt} via
  `src/fmtlib_*.h`; `debugmsg(...)` for errors shown in-game.

## Adding a new JSON-driven entity type

1. Define the struct with `load()`, `id`, `was_loaded`; back it with a
   `generic_factory<T>` and a static `T::load_all( jo, src )`.
2. Register one line in `DynamicDataLoader::initialize()` (src/init.cpp):
   `add( "my_type", &my_type::load_all );`
3. Hook `reset()`, `finalize()`, `check()` alongside the other types.
Existing registrations to crib from: furniture/terrain (init.cpp:285),
items by subtype (init.cpp:331–385 → item_factory.cpp), monsters
(init.cpp:395 → monstergenerator.cpp), `"recipe"`, `"mapgen"`,
`"vehicle_part"`, `"mutation"`, `"bionic"`.

## Lua layer

- Bundled Lua 5.4 in `src/lua/`; sol2 in `src/sol/`; in-house wrapper
  "luna" (`src/catalua_luna.h`, `catalua_luna_doc.h`) with `LUNA_VAL`,
  `LUNA_ID` (registers type + its string_id/int_id), `LUNA_ENUM`.
- Master registration: `cata::reg_all_bindings()` in
  `src/catalua_impl.cpp:31`; per-domain bindings in
  `src/catalua_bindings_*.cpp` (each has `cata::detail::reg_*`).
- Hooks fired from `src/catalua.cpp`: `run_on_game_load_hooks`,
  `run_on_game_save_hooks`, `run_on_every_x_hooks`,
  `run_on_mapgen_postprocess_hooks`. Lua console: `catalua_console.cpp`.

## Tests (tests/)

- Catch2 v2 (single header `tests/catch/catch.hpp`), custom main in
  `tests/test_main.cpp` (seeds cata RNG from the Catch seed).
- ~180 flat `*_test.cpp` files, tags like `[item]`, `[vehicle][mechanics]`;
  run subsets: `cata_test-tiles "[crafting]"`.
- Helpers: `map_helpers.h`, `player_helpers.h`, `state_helpers.h` (reset
  global state between cases), `options_helpers.h` (scoped option
  overrides), `assertion_helpers.h`, `test_statistics.h` (statistical
  balance assertions), `cata_generators.h`. Test JSON in `tests/data/`.

## Pitfalls

- `src/version.h` is generated by CMake at configure time — never
  hand-edit.
- Precompiled header `pch/main-pch.hpp`: touching widely-included
  headers triggers near-full rebuilds.
- Unity build (`USE_UNITY_BUILD`, off by default): file-local symbol
  collisions (anonymous namespaces, `static` names) break it.
- Tracy `ZoneScopedN(...)` macros in hot paths compile out when Tracy is
  off — preserve them when editing those functions.
- Third-party code is vendored in-tree (`src/lua/`, `src/sol/`,
  `src/third-party/`, fmtlib) — don't add system-package dependencies
  for those, and don't "clean up" their style.
