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

# Install the BN-parity gamepad layout (see the cdda-gamepad-controls
# skill). config/keybindings.json is CDDA's user-override file; entries
# replace default bindings per (category,id). The repo copy is the
# source of truth — this overwrites any in-game rebinds on each deploy.
if [ -f "${repo_dir}/deck-dda-keybindings.json" ]; then
    mkdir -p "${repo_dir}/config"
    cp "${repo_dir}/deck-dda-keybindings.json" "${repo_dir}/config/keybindings.json"
fi
distrobox enter "${box}" -- bash -c \
    "cd '${repo_dir}' && nice -n 19 make -j${jobs} CLANG=1 RELEASE=1 LTO=0 \
        TILES=1 SOUND=1 LOCALIZE=1 BACKTRACE=0 RUNTESTS=0 PCH=1"
# NB: leave LANGUAGES unset — CDDA's Makefile gates translation compilation
# on `ifdef LANGUAGES`, and any value (even "none") is taken as a language id.
echo "Deck DDA build updated: $(git log --oneline -1)"
