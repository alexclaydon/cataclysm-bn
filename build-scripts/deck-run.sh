#!/usr/bin/env bash
# Launch the local dev build on the Steam Deck.
# Point a Steam non-Steam-game shortcut at this script to run the dev
# branch from Game Mode. Runs on the Deck host, enters the bn-dev
# distrobox, and execs the game from the repo root (so data/ resolves).
set -euo pipefail

repo_dir="${DECK_REPO_DIR:-$HOME/cataclysm-bn}"
box="${DECK_DISTROBOX:-bn-dev}"
binary="out/build/linux-slim/src/cataclysm-bn-tiles"

if [ ! -x "${repo_dir}/${binary}" ]; then
    echo "Game binary missing; run deck-update.sh first." >&2
    exit 1
fi

exec distrobox enter "${box}" -- bash -c \
    "cd '${repo_dir}' && exec ./${binary}"
