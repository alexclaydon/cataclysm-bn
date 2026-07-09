#!/usr/bin/env bash
# Fetch precompiled shaders from upstream CI for local macOS builds.
#
# shadercross cannot run on macOS (vcpkg directx-dxc is unsupported there),
# so CI generates shaders on Linux and uploads them as the
# "generated-shaders" workflow artifact. This script downloads the most
# recent artifact into data/shaders/ (gitignored).
#
# Usage: fetch-shaders-macos.sh [--force]
# Requires: gh (authenticated), unzip
set -euo pipefail

repo="${SHADER_ARTIFACT_REPO:-cataclysmbn/Cataclysm-BN}"
output_dir="${SHADER_OUTPUT_DIR:-data/shaders}"

force=0
if [ "${1:-}" = "--force" ]; then
    force=1
fi

if [ "${force}" -eq 0 ] && ls "${output_dir}"/*.msl >/dev/null 2>&1; then
    echo "Shaders already present in ${output_dir}; use --force to re-download."
    exit 0
fi

if ! command -v gh >/dev/null 2>&1; then
    echo "gh CLI is required (brew install gh && gh auth login)" >&2
    exit 1
fi

artifact_id="$(gh api "repos/${repo}/actions/artifacts?name=generated-shaders&per_page=10" \
    --jq '[.artifacts[] | select(.expired | not)][0].id // empty')"

if [ -z "${artifact_id}" ]; then
    echo "No unexpired generated-shaders artifact found on ${repo}" >&2
    exit 1
fi

echo "Downloading generated-shaders artifact ${artifact_id} from ${repo}"
tmp_zip="$(mktemp -t generated-shaders.XXXXXX).zip"
trap 'rm -f "${tmp_zip}"' EXIT

gh api "repos/${repo}/actions/artifacts/${artifact_id}/zip" > "${tmp_zip}"

mkdir -p "${output_dir}"
find "${output_dir}" -maxdepth 1 \( -name '*.spv' -o -name '*.msl' -o -name '*.dxil' \) -delete
unzip -oq "${tmp_zip}" -d "${output_dir}"

count="$(find "${output_dir}" -maxdepth 1 -type f | wc -l | tr -d ' ')"
echo "Extracted ${count} shader files into ${output_dir}"
