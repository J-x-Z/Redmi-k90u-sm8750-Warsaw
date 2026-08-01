#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
OUTPUT="${1:-$SCRIPT_DIR/jxz-bore-like-v0.1.0.zip}"

rm -f "$OUTPUT"
(
    cd "$SCRIPT_DIR"
    zip -q -r -X "$OUTPUT" \
        module.prop \
        customize.sh \
        service.sh \
        system
)

shasum -a 256 "$OUTPUT"
