#!/usr/bin/env bash
# Fail if po/drum-machine.pot is out of date with the sources in po/POTFILES.in.
#
# Used by both the pre-commit hook and CI. Timestamps and line numbers are
# ignored, so unrelated edits don't cause noise. When the template really is
# stale, the regenerated file is left in place so you can review and commit it.
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

pot=po/drum-machine.pot
builddir="$(mktemp -d)"
orig="$(mktemp)"
trap 'rm -rf "$builddir" "$orig" "$orig.norm" "$pot.norm"' EXIT

normalize() {
  sed -E \
    -e 's/POT-Creation-Date: [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}[+-][0-9]{4}/POT-Creation-Date: TIMESTAMP/g' \
    -e '/^#:/ s/:[0-9]+//g' \
    "$1"
}

cp "$pot" "$orig"

meson setup "$builddir" >/dev/null
meson compile -C "$builddir" drum-machine-pot >/dev/null

if [ ! -f "$pot" ]; then
  echo "error: failed to generate $pot" >&2
  cp "$orig" "$pot"
  exit 1
fi

normalize "$orig" >"$orig.norm"
normalize "$pot" >"$pot.norm"

if diff -u --ignore-all-space "$orig.norm" "$pot.norm" >/dev/null; then
  # Only timestamps/line numbers changed: keep the committed file untouched.
  cp "$orig" "$pot"
  exit 0
fi

echo "Translation template is out of date; $pot has been regenerated." >&2
echo "Review the changes, then 'git add $pot'." >&2
diff -u "$orig.norm" "$pot.norm" || true
exit 1
