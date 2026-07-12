# Conventions: style, formatting, linting, i18n, commits

Canonical sources (read these when detail is needed):
- `AGENTS.md` (repo root) — hard constraints + workflow commands for AI agents
- `docs/en/dev/guides/formatting.md` — formatting/linting quick reference
- `docs/en/dev/explanation/code_style.md` — C++ style rationale
- `docs/en/contribute/contributing.md` + `changelog_guidelines.md`
- `docs/en/i18n/reference/translation.md` — translation API

## C++ formatting: dual formatter by location

- **astyle 3.1** formats ONLY top-level `src/*.cpp` / `src/*.h`
  (config `.astylerc`).
- **clang-format** formats everything else: `src/*/*`, `tests/`,
  `tools/format/`, `tools/clang-tidy-plugin/` (config `.clang-format`).
- NEVER formatted: `src/lua/`, `src/sol/`, `src/third-party/`,
  `tests/catch/`, `tools/clang-tidy-plugin/test/`.

Run via (pick one):
- `just fmt` (staged files; also JSON/docs/lua), `just fmt --all`,
  `just fmt-cpp`
- `cmake --build <build-dir> --target format`
- `build-scripts/fmt.sh` / `format-cpp.sh` directly

Pre-commit hook: `just hooks-setup` (installs via `prek`). CI also runs
autofix.ci which pushes format fixes to PR branches.

## JSON style

- Spec: `docs/en/mod/json/explanation/json_style.md` (2-space indent,
  inline arrays unless >120 chars, one object entry per line).
- Format with `just fmt-json` or the `json_formatter` binary built by
  `build-scripts/format-json.sh` (single file: `json_formatter <file>`).
  `data/names/` is excluded.
- Syntax lint: `build-scripts/lint-json.sh`; full lint incl. dialogue
  validator: `just lint`.

## clang-tidy (custom plugin)

- Config `.clang-tidy`; CI uses LLVM 22. Custom checks (`cata-*`) live in
  `tools/clang-tidy-plugin/` — notable: point/coordinate API enforcement
  (`cata-use-point-apis`, `cata-point-initialization`), i18n checks
  (`cata-no-static-gettext`, `cata-json-translation-input`,
  `cata-translator-comments`, `cata-use-localized-sorting`),
  `cata-no-long`, `cata-determinism`, `cata-test-filename`.
- Build plugin: `build-scripts/build-clang-tidy-plugin.sh`; run:
  `build-scripts/clang-tidy-wrapper.sh [-fix] src/foo.cpp`.

## Commit / PR conventions

- **Conventional Commits** for PR titles and commits:
  `<type>(<scope>): <subject>` — types: feat, fix, refactor, build,
  docs, style, perf, test, ci, chore, revert; scopes include lua, UI,
  i18n, mods/<MOD_ID>, balance, port.
- Commit template: `git config --local commit.template .gitmessage`.
- **AI-assistance policy** (from contributing.md): disclose AI use in PR
  descriptions; AI-assisted commits carry an `Assisted-by:` trailer
  (e.g. `Assisted-by: Claude:<model>`).
- PR checklist (.github/pull_request_template.md): link issues with
  closing keywords (`- fixed #1234`), update
  `lang/bn_extract_json_strings.sh` when C++ adds localizable JSON
  fields, add obsoletion/migration for removed JSON ids.

## i18n

- Code: `_( "text" )`, `pgettext( ctx, text )`, `vgettext` for plurals;
  stored strings use the `translation` class (`to_translation()`).
  Only string literals are extracted.
- Extraction lives in `lang/` (`extract_json_strings.py`,
  `bn_extract_json_strings.sh`, `update_pot.sh`); PO files not kept in
  repo since 2026 (CI pulls from Transifex).
- Validate a PO: `msgfmt -f -c -o /tmp/x.mo lang/po/x.po`;
  `tools/check_po_printf_format.py` after PO edits.

## Docs site

- Lume/Deno site in `docs/` (English under `docs/en/`, translations in
  de/ja/ko/ru). Preview: `deno task docs serve` (root) → localhost:3000.
- Auto-generated pages (regen with `deno task docs:gen`, needs
  `$CATA_EXE` pointing at a built game binary):
  `docs/en/mod/lua/reference/lua.md`, `docs/en/dev/reference/cli_options.md`.
- Markdown/TS formatting via `deno fmt` (config in root `deno.jsonc`;
  it also formats `.claude/`, `scripts/`, `build-scripts/`).

## Existing agent infrastructure

- `AGENTS.md` at repo root is the canonical agent doc — hard constraints
  (trailing return types `auto f() -> T`, no manual iterator loops,
  `auto x =` declarations, options structs for >3 params), C++23
  conventions, and exact workflow commands. Follow it.
- `.agents/skills/` contains upstream agent skills: pr, changelog-gen,
  i18n-context, test-quality, deno-script, release-gen,
  add-lua-binding-{simple,complex,api}, lua-binding-reference. Check
  there before inventing a workflow for those tasks.
- `.github/llm_review_guide.md` — LLM code-review guide.
