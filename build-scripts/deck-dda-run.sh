#!/usr/bin/env bash
# Launch the from-source Cataclysm-DDA build on the Steam Deck.
# Point a Steam non-Steam-game shortcut at this script to run it from
# Game Mode. Runs on the Deck host, enters the bn-dev distrobox (the
# binary links against the container's glibc/SDL2), and execs the game
# from the repo root so data/ and gfx/ resolve. Saves stay inside the
# repo dir, fully separate from the Steam-installed DDA.
set -euo pipefail

repo_dir="${DDA_REPO_DIR:-$HOME/cataclysm-dda}"
box="${DECK_DISTROBOX:-bn-dev}"
binary="cataclysm-tiles"

if [ ! -x "${repo_dir}/${binary}" ]; then
    echo "Game binary missing; run deck-dda-update.sh first." >&2
    exit 1
fi

exec distrobox enter "${box}" -- bash -c \
    "cd '${repo_dir}' && exec ./${binary}"
