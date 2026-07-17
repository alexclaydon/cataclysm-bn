#!/usr/bin/env bash
# Update and rebuild the from-source Cataclysm: The Last Generation build
# on the Steam Deck. Runs on the Deck host; the build happens inside the
# bn-dev distrobox (SteamOS rootfs has no toolchain). TLG is a CDDA fork
# and uses the same Makefile build (SDL2, from the distrobox's Ubuntu
# packages — no source-built deps needed, unlike DDA's SDL3_mixer).
#
# Kept in the cataclysm-bn repo (this fork is the config home for all
# Deck game builds); `make deck-tlg` on Nova copies it over before use.
#
# NB: no keybindings install here — TLG's gamepad layer is the legacy
# numeric JOY_n scheme, so the BN-parity layout in
# deck-dda-keybindings.json does not apply to it.
set -euo pipefail

repo_dir="${TLG_REPO_DIR:-$HOME/cataclysm-tlg}"
box="${DECK_DISTROBOX:-bn-dev}"
jobs="${JOBS:-$(nproc)}"

cd "${repo_dir}"
# --no-tags: same shallow-clone discipline as the DDA build — we only
# track master, and tag auto-following on a shallow clone drags in
# release history we don't want.
git pull --ff-only --no-tags

# WARNINGS override: TLG's default includes -Werror, and clang-22
# promotes optimization-report warnings (-Wpass-failed "loop not
# unrolled" in handle_liquid.cpp at -Os) into hard errors. We build
# someone else's release source, so warnings-as-errors is only
# friction; the override also drops the Makefile's conditional
# `WARNINGS +=` suppressions, which is harmless without -Werror.
distrobox enter "${box}" -- bash -c \
    "cd '${repo_dir}' && nice -n 19 make -j${jobs} CLANG=1 RELEASE=1 LTO=0 \
        TILES=1 SOUND=1 LOCALIZE=1 BACKTRACE=0 RUNTESTS=0 PCH=1 \
        WARNINGS='-Wall -Wextra'"
# NB: leave LANGUAGES unset — the Makefile gates translation compilation
# on `ifdef LANGUAGES`, and any value (even "none") is taken as a language id.
echo "Deck TLG build updated: $(git log --oneline -1)"
