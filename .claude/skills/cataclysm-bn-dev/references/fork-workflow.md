# Fork-specific workflow (this fork, not upstream)

This is Alex's personal fork of Cataclysm-BN. Dev work happens on the
`aec-dev` branch. Upstream PRs are not the goal unless explicitly asked.

**Machine convention**: all development happens on the local clone on
Nova (this Mac; always on). The Steam Deck clone is a deployment target
only — never a workspace. "Deploy on deck" = `make deck-local` from
Nova (push origin → ssh → pull + rebuild on the Deck).

## Remotes

| Remote    | Where                                  | Role                          |
| --------- | -------------------------------------- | ----------------------------- |
| `forgejo` | forgejo.tailnet-46f3.ts.net (private)  | Primary — push here           |
| `origin`  | github.com/alexclaydon/cataclysm-bn    | Needed for CI (`make deck`)   |
| `upstream`| github.com/cataclysmbn/Cataclysm-BN    | Sync + shader artifacts       |

Push to both `forgejo` and `origin` to keep them in sync.

## Makefile targets (repo root; fork-local, not upstream)

| Target            | What it does                                              |
| ----------------- | --------------------------------------------------------- |
| `make`            | Full macOS build: fetch shaders if missing → configure → compile (`osx-arm-slim` preset) |
| `make compile`    | Incremental build only — the day-to-day loop              |
| `make run`        | Build then launch the game                                |
| `make test`       | Build then run the Catch2 test binary                     |
| `make shaders-force` | Re-download precompiled shaders from upstream CI       |
| `make deck`       | CI route: push branch → dispatch fork CI → download self-contained `linux-tiles-x64` tarball to `out/deck/` |
| `make deck-local` | Native Deck route: push origin → ssh to Deck → pull + incremental rebuild in its distrobox |
| `make deck-dda`   | Update + rebuild the from-source Cataclysm-DDA build on the Deck (copies scripts over first) |
| `make clean`      | Remove the preset's build directory                       |

Override preset: `make PRESET=osx-arm-dist`.

## Shaders (important quirk)

`data/shaders/` is gitignored; CI generates shaders on Linux. Neither
macOS nor the Deck can build shadercross, so both use precompiled
artifacts:

- macOS: `build-scripts/fetch-shaders-macos.sh` (downloads upstream CI's
  `generated-shaders` artifact via `gh`).
- Configure with `-DBUILD_SHADERCROSS=OFF` when shaders are prefetched
  (the Deck setup does this; macOS ignores shadercross automatically).

Only re-fetch when `src/shaders/*.hlsl` changes.

## Steam Deck

- SSH: host alias `steamdeck` (tailnet; user `deck`). Timeouts usually
  mean the Deck is asleep.
- Clone at `~/cataclysm-bn` on the Deck; builds happen inside the
  `bn-dev` distrobox (Ubuntu 26.04 + clang-22; SteamOS rootfs has no
  toolchain).
- `build-scripts/deck-bootstrap.sh` — full environment from a fresh
  clone. `deck-update.sh` — pull + rebuild. `deck-run.sh` — launcher
  (the Steam shortcut "Cataclysm BN (dev)" points at it for Game Mode).

## Cataclysm-DDA from source on the Deck (sibling install)

Upstream DDA (github.com/CleverRaven/Cataclysm-DDA, `master`) also runs
from source on the Deck, fully separate from both the Steam-installed
DDA and the BN build:

- Clone at `~/cataclysm-dda` on the Deck (shallow); saves/config live in
  the clone dir (no USE_HOME_DIR), so nothing collides with Steam's DDA.
- Builds in the same `bn-dev` distrobox but with DDA's own Makefile
  (`CLANG=1 RELEASE=1 TILES=1 SOUND=1 LANGUAGES=none`), not CMake. DDA
  master uses SDL3; Ubuntu has no libsdl3-mixer package, so SDL3_mixer
  3.2.0 is built from source at `~/build-deps/SDL_mixer` and installed
  to the distrobox's /usr/local (redo after recreating the distrobox).
- `build-scripts/deck-dda-update.sh` / `deck-dda-run.sh` live in THIS
  repo (its config home) and `make deck-dda` scp's them over before
  running the update, so edits propagate automatically.
- Steam shortcut "Cataclysm DDA (dev)": a wrapper script with that
  literal filename in `~/cataclysm-dda/` (steamos-add-to-steam names
  shortcuts after the file) exec's deck-dda-run.sh; it was added live
  via `steamos-add-to-steam` — that works over ssh while Steam runs,
  no Steam restart or desktop mode needed, unlike the shortcuts.vdf
  binary edit used for the BN shortcut.

## Fork CI

GitHub Actions on the fork: `matrix.yml` stays enabled (needed for
`make deck` dispatch; also runs on pushes to `main`). The auto-trigger
workflows (experimental-release, docs, push-translation-template,
pr-artifact-publish) are disabled; `release.yml` is fork-disabled by
GitHub. Pushes to `aec-dev` never trigger CI.

## macOS build environment

Homebrew deps per docs plus `dylibbundler`. No env file or PATH changes
needed — presets call ccache directly; sqlite/ncurses come from the
macOS SDK. Binary: `out/build/osx-arm-slim/src/cataclysm-bn-tiles`
(run from repo root so `data/` resolves).
