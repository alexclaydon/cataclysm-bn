---
name: cataclysm-bn-dev
description: >-
  Working guide for this Cataclysm Bright Nights fork — building (macOS,
  Steam Deck, CI), testing, C++ architecture, JSON game data, mods/Lua,
  and upstream conventions. Use this skill whenever working in this repo:
  fixing bugs or adding features in src/, adding or balancing game
  content in data/json, writing tests, running or building the game,
  touching shaders/rendering, preparing upstream PRs, or wondering "how
  do I do X in this codebase" — even for small changes, because this
  repo has unusual constraints (dual formatters, generated files,
  shader artifacts, AGENTS.md hard style rules) that are easy to violate
  by accident.
---

# Cataclysm BN development

Fork of Cataclysm: Bright Nights (C++23 roguelike, ~420k lines in src/,
~2900 JSON files in data/). Dev branch: `aec-dev`. Two things shape all
work here:

1. **`AGENTS.md` at the repo root is binding** for C++ changes — hard
   constraints (trailing return types, `auto x =`, ranges over manual
   loops, options structs for >3 params) and the canonical workflow.
   Read it before writing C++.
2. **Engine vs content**: C++ in `src/` defines mechanisms; nearly all
   game content lives in `data/json` and loads at runtime. JSON/Lua
   changes need no recompile — just relaunch. Prefer data-side solutions
   when possible.

## Quick orientation

| Task | Go to |
| ---- | ----- |
| Build/run on this Mac | `make` / `make run` (preset `osx-arm-slim`) |
| Incremental rebuild | `make compile` |
| Run tests | `make test`, or `out/build/<preset>/tests/cata_test-tiles "[tag]"` from repo root |
| Steam Deck build/run | `make deck-local` (native) or `make deck` (CI tarball) — see references/fork-workflow.md |
| Validate JSON edits | `just lint-json`, then `<binary> --jsonverify` (core) / `--check-mods` |
| Format before commit | `just fmt` (staged files) or `just fmt-cpp/-json <files>` (specific files) — C++ has TWO formatters by path, don't run astyle/clang-format by hand |
| Find where a JSON "type" loads in C++ | `src/init.cpp` `DynamicDataLoader::initialize()` |
| Add/modify game content | data/json — see references/json-data.md |
| Docs site | `deno task docs serve` → localhost:3000 |

## References (read when working in that area)

- **references/fork-workflow.md** — this fork's remotes, Makefile
  targets, shader-artifact workaround, Steam Deck setup (distrobox,
  `make deck-local`, Game Mode shortcut), fork CI policy. Read first
  for any build/run/deploy task.
- **references/architecture.md** — src/ subsystem map, entry points,
  core patterns (string_id/int_id, generic_factory, JsonObject load
  convention, units/calendar, translation macros), how to wire a new
  JSON type, Lua binding layer, test helpers, pitfalls (generated
  version.h, PCH, unity build, Tracy zones).
- **references/json-data.md** — data/ layout, where each content
  category lives, copy-from/abstract/extend/delete/relative/
  proportional inheritance, mod structure and load order, Lua mod
  hooks, validation tools, key reference docs.
- **references/conventions.md** — dual C++ formatters (astyle for
  src/*.cpp|h ONLY, clang-format elsewhere, vendored code untouched),
  JSON style, clang-tidy custom checks, Conventional Commits, i18n
  rules, docs tooling, existing `.agents/skills/`.
- **references/build-test.md** — CMake presets and options, shader/GPU
  system, test invocation and sharding, game CLI flags, CI pipeline.

## Ground rules distilled from the audit

- Follow AGENTS.md for C++ style; it overrides generic instincts (e.g.
  it mandates `auto f() -> T` and bans manual iterator loops).
- Never hand-edit generated files: `src/version.h`,
  `docs/en/mod/lua/reference/lua.md`, `docs/en/dev/reference/cli_options.md`,
  `lua_annotations.lua`.
- Never reformat or "fix" vendored code: `src/lua/`, `src/sol/`,
  `src/third-party/`, `tests/catch/`.
- New localizable strings use `_( "..." )` / `translation` class; new
  localizable JSON fields also need `lang/bn_extract_json_strings.sh`
  updated.
- Removing a JSON id needs a migration in `data/json/obsoletion/`.
- Commits: Conventional Commits (`feat:`, `fix:`, `refactor:` …).
  Upstream PRs additionally want the `Assisted-by:` trailer for
  AI-assisted commits and the PR template checklist.
- The full test binary takes minutes, not hours — for a focused change,
  run the relevant `"[tag]"` first, and the sharded full suite
  (references/build-test.md) before declaring victory on risky changes.
- This is a large legacy codebase: search for an existing helper before
  writing one (`src/cata_algo.h`, `src/string_utils`, test helpers in
  `tests/*_helpers.h`).
