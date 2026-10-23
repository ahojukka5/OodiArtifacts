#!/usr/bin/env bash
set -euo pipefail

if [[ "$(uname -s)" != Darwin || "$(uname -m)" != arm64 ]]; then
  echo 'Run this recipe natively on an Apple Silicon Mac.' >&2
  exit 1
fi
for tool in python3 cmake ninja git xcrun; do
  command -v "$tool" >/dev/null
done
recipe_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
work_dir="${OCCT_WORK_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/oodi/OodiArtifacts/occt-8.0.1}"
mkdir -p "$work_dir"
exec python3 "$recipe_dir/occt.py" build --work "$work_dir" "$@"
