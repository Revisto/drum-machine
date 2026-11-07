#!/usr/bin/env bash
# desktop-file-validate refuses files without a .desktop extension, so validate
# copies of the *.desktop.in templates instead.
set -euo pipefail

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

status=0
for f in "$@"; do
  name="$(basename "${f%.in}")"
  cp "$f" "$tmp/$name"
  desktop-file-validate "$tmp/$name" || status=1
done
exit "$status"
