# Dev setup: macOS + Steam Deck workflow

*2026-07-12 — written by Claude during the setup session.*

This entry records the development setup for this fork (`aec-dev` branch)
as established today: local builds on the Mac, a native dev build on the
Steam Deck maintained over SSH, and an optional CI path for distributable
packages.

## Repo and remotes

- Fork of Cataclysm: Bright Nights; dev work happens on `aec-dev`.
- `forgejo` (private, tailnet) is the primary remote; `origin` is the
  GitHub fork (needed for CI); `upstream` is cataclysmbn/Cataclysm-BN.
- Pushes go to both forgejo and origin to keep them in sync.

## macOS (primary dev machine)

- Dependencies via Homebrew per the repo docs, plus `dylibbundler`
  (missing from the docs' list). No env file or PATH changes were needed:
  the CMake presets invoke ccache directly, and sqlite/ncurses resolve
  from the macOS SDK despite Homebrew's keg-only warnings.
- Shaders cannot be generated on macOS (no shadercross support), so
  `build-scripts/fetch-shaders-macos.sh` downloads the `generated-shaders`
  artifact from upstream CI into the gitignored `data/shaders/`.
- Root `Makefile` targets: `make` (shaders + configure + compile via the
  `osx-arm-slim` preset), `make run`, `make test`, `make clean`.
- Data changes (JSON/Lua/title art) need no rebuild — edit and relaunch.

## Steam Deck (native dev build, played from Game Mode)

The Deck runs a clone of the repo at `~/cataclysm-bn` (branch `aec-dev`,
cloned from the GitHub fork). SSH access is via the `steamdeck` host
alias (tailscale MagicDNS; user `deck`). If the alias times out the Deck
is probably asleep.

SteamOS has a read-only rootfs with no toolchain, so the build lives in
a distrobox container (`bn-dev`, Ubuntu 26.04) with clang-22 symlinked
as default (the repo needs Clang 22+; Ubuntu's stock clang is 21). The
game builds with the `linux-slim` preset and `-DBUILD_SHADERCROSS=OFF`,
reusing the CI shader artifacts. First build ~45 minutes; incremental
rebuilds are seconds.

Scripts (all in `build-scripts/`):

- `deck-bootstrap.sh` — one-time setup from a fresh clone: creates the
  container with all build deps, installs clang-22, fetches shaders,
  runs the first build. Makes the Deck environment reproducible.
- `deck-update.sh` — pull + incremental rebuild inside the container.
- `deck-run.sh` — launcher; enters the container and starts the game.

Day-to-day loop from the Mac: commit on `aec-dev`, then `make deck-local`
(pushes the branch, then sshes to the Deck and runs `deck-update.sh`).

A non-Steam game shortcut **"Cataclysm BN (dev)"** points at
`deck-run.sh`, so the current dev build launches from Game Mode. It was
added by scripted binary-VDF edit of
`~/.steam/steam/userdata/51494222/config/shortcuts.vdf` (Steam must be
shut down while editing; a backup sits alongside as
`shortcuts.vdf.bak-claude`).

## CI path (distributable packages)

`make deck` dispatches upstream's `matrix.yml` workflow on the GitHub
fork (`workflow_dispatch`), waits for the self-contained
`linux-tiles-x64` playtest tarball (bundled SDL3 runtime), and downloads
it to `out/deck/`. Used for proper packages rather than dev iteration.

Workflows that auto-trigger on the fork (experimental-release, docs,
push-translation-template, pr-artifact-publish) were disabled to avoid
CI burn on every sync of `main`; `matrix.yml` stays enabled because
disabling it would also block manual dispatch.
