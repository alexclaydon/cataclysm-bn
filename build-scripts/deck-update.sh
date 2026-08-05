#!/usr/bin/env bash
# Update and rebuild the local dev build on the Steam Deck.
# Runs on the Deck host; the build happens inside the bn-dev distrobox
# (see docs: the SteamOS rootfs has no toolchain).
#
# Usage: deck-update.sh [git-ref]   (default: current branch)
set -euo pipefail

repo_dir="${DECK_REPO_DIR:-$HOME/cataclysm-bn}"
box="${DECK_DISTROBOX:-bn-dev}"

cd "${repo_dir}"
# Take Nova's branch wholesale rather than pulling. We rebase aec-dev onto new
# upstream releases, which rewrites commits, and a pull cannot fast-forward
# across that. Nothing here is authored on the Deck, so replacing history
# outright is the honest operation.
#
# NEVER add `git clean` to this. reset --hard leaves ignored and untracked
# files alone, which is why saves and configs survive a deploy; `git clean -fd`
# would delete them.
#
# --no-tags: the upstream projects tag heavily, and following tags onto this
# clone drags in years of history nobody here needs.
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch --no-tags origin "${branch}"
git reset --hard "origin/${branch}"
distrobox enter "${box}" -- bash -c \
    "cd '${repo_dir}' && cmake --build --preset linux-slim --target cataclysm-bn-tiles"
echo "Deck build updated: $(git log --oneline -1)"
