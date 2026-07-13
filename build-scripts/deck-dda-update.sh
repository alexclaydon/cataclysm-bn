#!/usr/bin/env bash
# Update and rebuild the from-source Cataclysm-DDA build on the Steam Deck.
# Runs on the Deck host; the build happens inside the bn-dev distrobox
# (SteamOS rootfs has no toolchain). DDA uses its own Makefile build
# (SDL2), unlike BN's CMake/SDL3 build, but the distrobox is shared.
#
# Kept in the cataclysm-bn repo (this fork is the config home for all
# Deck game builds); `make deck-dda` on Nova copies it over before use.
set -euo pipefail

repo_dir="${DDA_REPO_DIR:-$HOME/cataclysm-dda}"
box="${DECK_DISTROBOX:-bn-dev}"
jobs="${JOBS:-$(nproc)}"

cd "${repo_dir}"
git pull --ff-only
distrobox enter "${box}" -- bash -c \
    "cd '${repo_dir}' && nice -n 19 make -j${jobs} CLANG=1 RELEASE=1 LTO=0 \
        TILES=1 SOUND=1 LOCALIZE=1 LANGUAGES=none BACKTRACE=0 RUNTESTS=0 PCH=1"
echo "Deck DDA build updated: $(git log --oneline -1)"
