# Fork-specific workflow (this fork, not upstream)

This is Alex's personal fork of Cataclysm-BN. Dev work happens on the
`aec-dev` branch. Upstream PRs are not the goal unless explicitly asked.

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
