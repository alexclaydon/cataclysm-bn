#!/usr/bin/env bash
# Launch the from-source Cataclysm: The Last Generation build on the
# Steam Deck. Point a Steam non-Steam-game shortcut at this script to
# run it from Game Mode. Runs on the Deck host, enters the bn-dev
# distrobox (the binary links against the container's glibc/SDL2), and
# execs the game from the repo root so data/ and gfx/ resolve. Saves
# stay inside the repo dir, fully separate from every other install.
set -euo pipefail

repo_dir="${TLG_REPO_DIR:-$HOME/cataclysm-tlg}"
box="${DECK_DISTROBOX:-bn-dev}"
binary="cataclysm-tlg-tiles"

if [ ! -x "${repo_dir}/${binary}" ]; then
    echo "Game binary missing; run deck-tlg-update.sh first." >&2
    exit 1
fi

exec distrobox enter "${box}" -- bash -c \
    "cd '${repo_dir}' && exec ./${binary}"
