#!/usr/bin/env bash
# Produce a Steam Deck (Linux x64 tiles) build via GitHub Actions on the fork.
#
# Pushes the current branch to the GitHub fork, dispatches the matrix
# workflow, waits for the linux-tiles-x64 playtest tarball artifact, and
# downloads it into out/deck/. The artifact is uploaded before the test
# stage runs, so this usually finishes well before the whole run does.
#
# Usage: deck-build.sh [--no-push]
# Requires: gh (authenticated with workflow scope)
set -euo pipefail

repo="${DECK_BUILD_REPO:-alexclaydon/cataclysm-bn}"
remote="${DECK_BUILD_REMOTE:-origin}"
output_dir="${DECK_BUILD_OUTPUT_DIR:-out/deck}"
poll_seconds=60

branch="$(git branch --show-current)"
if [ -z "${branch}" ]; then
    echo "Detached HEAD; check out a branch first." >&2
    exit 1
fi

if [ "${1:-}" != "--no-push" ]; then
    echo "Pushing ${branch} to ${remote}"
    git push "${remote}" "${branch}"
fi

echo "Dispatching matrix.yml on ${repo}@${branch}"
gh workflow run matrix.yml --repo "${repo}" --ref "${branch}"
sleep 10

run_id="$(gh run list --repo "${repo}" --workflow matrix.yml --branch "${branch}" \
    --limit 1 --json databaseId --jq '.[0].databaseId')"
if [ -z "${run_id}" ]; then
    echo "Could not find the dispatched workflow run." >&2
    exit 1
fi
echo "Watching run ${run_id} (https://github.com/${repo}/actions/runs/${run_id})"

while true; do
    artifact_id="$(gh api "repos/${repo}/actions/artifacts?per_page=30" \
        --jq ".artifacts[] | select(.workflow_run.id==${run_id} and (.name|startswith(\"linux-tiles-x64\"))) | .id" \
        2>/dev/null | head -1 || true)"
    if [ -n "${artifact_id}" ]; then
        break
    fi
    status="$(gh run view "${run_id}" --repo "${repo}" --json status,conclusion \
        --jq '"\(.status) \(.conclusion)"' 2>/dev/null || echo poll-error)"
    case "${status}" in
        completed*)
            echo "Run ended without producing a linux-tiles-x64 artifact: ${status}" >&2
            exit 1
            ;;
    esac
    echo "  still building (${status}); next check in ${poll_seconds}s"
    sleep "${poll_seconds}"
done

echo "Downloading artifact ${artifact_id} into ${output_dir}/"
mkdir -p "${output_dir}"
tmp_zip="$(mktemp -t deck-build.XXXXXX).zip"
trap 'rm -f "${tmp_zip}"' EXIT
gh api "repos/${repo}/actions/artifacts/${artifact_id}/zip" > "${tmp_zip}"
unzip -oq "${tmp_zip}" -d "${output_dir}"

echo "Done:"
ls -lh "${output_dir}" | tail -n +2
echo "Copy the tarball to the Deck, extract, and add cataclysm-bn-tiles as a non-Steam game."
