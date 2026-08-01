#!/bin/sh
set -eu

if [ "$#" -ne 3 ]; then
    echo "usage: $0 WORKSPACE DIST_DIR MANIFEST" >&2
    exit 2
fi

workspace=$(cd "$1" && pwd)
if [ -e "$2" ] && [ -n "$(find "$2" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]; then
    echo "refusing to reuse non-empty dist directory: $2" >&2
    exit 1
fi
mkdir -p "$2"
dist_dir=$(cd "$2" && pwd)
manifest=$(cd "$(dirname "$3")" && pwd)/$(basename "$3")
output_user_root=${KLEAF_OUTPUT_USER_ROOT:-"$(dirname "$workspace")/bazel-output-jxz-kernelsu"}

if [ "$(uname -s)" != Linux ] || [ "$(uname -m)" != x86_64 ]; then
    echo "KernelSU GKI build requires Linux x86_64" >&2
    exit 1
fi
if [ ! -f "$manifest" ]; then
    echo "manifest does not exist: $manifest" >&2
    exit 1
fi
python3 "$workspace/warsaw_enhanced/verify_source_state.py" "$workspace" \
    > "$dist_dir/source-verification.json"

export BUILD_NUMBER=15511674
mkdir -p "$output_user_root"
ulimit -n 65535 2>/dev/null || true
cd "$workspace"

tools/bazel --output_user_root="$output_user_root" run \
    --repo_manifest="$workspace:$manifest" \
    --config=release \
    --jobs=6 \
    --local_resources=cpu=8 \
    --local_resources=memory=10000 \
    //warsaw_enhanced:warsaw_gki_kernelsu_dist -- --dist_dir="$dist_dir"

tools/bazel --output_user_root="$output_user_root" build \
    --repo_manifest="$workspace:$manifest" \
    --config=release \
    --jobs=6 \
    --local_resources=cpu=8 \
    --local_resources=memory=10000 \
    //warsaw_enhanced:warsaw_gki_kernelsu_config

config_file=$(tools/bazel --output_user_root="$output_user_root" cquery \
    --repo_manifest="$workspace:$manifest" \
    --config=release \
    --output=files \
    //warsaw_enhanced:warsaw_gki_kernelsu_config | tail -n 1)
case "$config_file" in
    /*) ;;
    *) config_file="$workspace/$config_file" ;;
esac
if [ -d "$config_file" ]; then
    config_file="$config_file/.config"
fi
if [ ! -f "$config_file" ]; then
    echo "unable to locate generated config: $config_file" >&2
    exit 1
fi

cp "$config_file" "$dist_dir/.config"
checksum_file=$(mktemp)
(
    cd "$dist_dir"
    find . -maxdepth 1 -type f ! -name SHA256SUMS -print0 \
        | sort -z \
        | xargs -0 sha256sum
) > "$checksum_file"
mv "$checksum_file" "$dist_dir/SHA256SUMS"
