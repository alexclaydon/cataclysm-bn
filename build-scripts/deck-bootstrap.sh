#!/usr/bin/env bash
# One-time Steam Deck dev environment setup, from a fresh clone.
# Runs on the Deck host (SteamOS ships distrobox/podman; its read-only
# rootfs has no toolchain, so everything builds inside a container).
#
# After this completes: deck-update.sh rebuilds, deck-run.sh launches,
# and a Steam shortcut can point at deck-run.sh for Game Mode.
#
# Usage: deck-bootstrap.sh
set -euo pipefail

repo_dir="${DECK_REPO_DIR:-$HOME/cataclysm-bn}"
box="${DECK_DISTROBOX:-bn-dev}"
image="docker.io/library/ubuntu:26.04"
deps="git cmake ninja-build mold clang llvm ccache libsdl3-dev \
libsdl3-image-dev libsdl3-ttf-dev libfreetype-dev bzip2 zlib1g-dev \
libvorbis-dev libncurses-dev gettext libflac++-dev libsqlite3-dev \
pkg-config unzip gh"

cd "${repo_dir}"

if ! command -v distrobox >/dev/null 2>&1; then
    echo "distrobox not found; this script expects SteamOS 3.5+" >&2
    exit 1
fi

if ! podman container exists "${box}" 2>/dev/null; then
    echo "Creating ${box} container (image pull + package install, ~10 min)"
    distrobox create --yes --name "${box}" --image "${image}" \
        --additional-packages "${deps}"
    # First enter triggers container init (installs the packages above)
    distrobox enter "${box}" -- true
else
    echo "Container ${box} already exists; skipping creation"
fi

# The repo needs Clang 22+; Ubuntu 26.04's default clang is 21.
if ! distrobox enter "${box}" -- clang++ --version | grep -q "version 22"; then
    echo "Installing clang-22 and making it the default"
    podman exec --user root "${box}" bash -c \
        'apt-get install -y -q clang-22 llvm-22 >/dev/null &&
         for t in clang clang++ llvm-ar llvm-ranlib; do
             ln -sf "/usr/bin/${t}-22" "/usr/local/bin/${t}"
         done'
fi

# Shaders: shadercross cannot be built here cheaply; reuse CI artifacts.
if ! ls data/shaders/*.spv >/dev/null 2>&1; then
    echo "Fetching precompiled shaders from upstream CI"
    if ! distrobox enter "${box}" -- gh auth status >/dev/null 2>&1; then
        echo "gh is not authenticated. Either run:" >&2
        echo "    distrobox enter ${box} -- gh auth login" >&2
        echo "or copy shaders from another machine:" >&2
        echo "    scp -r <host>:cataclysm-bn/data/shaders ${repo_dir}/data/" >&2
        exit 1
    fi
    distrobox enter "${box}" -- bash -c \
        "cd '${repo_dir}' && bash build-scripts/fetch-shaders-macos.sh"
fi

echo "Configuring and building (first build takes ~45 min on the Deck)"
distrobox enter "${box}" -- bash -c \
    "cd '${repo_dir}' &&
     cmake --preset linux-slim -DBUILD_SHADERCROSS=OFF &&
     cmake --build --preset linux-slim --target cataclysm-bn-tiles"

echo "Bootstrap complete. Launch with build-scripts/deck-run.sh"
