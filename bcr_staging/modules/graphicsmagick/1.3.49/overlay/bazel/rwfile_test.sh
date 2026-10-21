#!/bin/sh
# Runs the upstream tests/rwfile.tap invocations for one or more formats.
#
# Usage: rwfile_test.sh <rwfile> <rwfile.tap> <tap-functions.shi> FORMAT...
#
# Each "# <FORMAT> format" section of tests/rwfile.tap is extracted verbatim
# and evaluated with upstream's TAP helper functions, so the exact same
# rwfile command lines (and -F feature gating) as "make check" are used.
# Output files are written to $TEST_TMPDIR. Exits non-zero if any TAP test
# reports "not ok".
set -u

here=$(pwd)
abspath() {
  case "$1" in
    /*) printf '%s\n' "$1" ;;
    *) printf '%s\n' "${here}/$1" ;;
  esac
}

rwfile=$(abspath "$1")
tap=$(abspath "$2")
tap_functions=$(abspath "$3")
shift 3

# Delegates compiled into this build (see magick/magick_config.h).
MAGICK_FEATURES='JPEG PNG TIFF ZLIB'
MEMCHECK=''
SRCDIR=$(dirname "${tap}")
export SRCDIR

# shellcheck disable=SC1090
. "${tap_functions}"

failures=0
test_result_fn() {
  test_result=$1
  shift
  test_count=$((test_count + 1))
  if test "${test_result}" != 'ok'; then
    failures=$((failures + 1))
  fi
  printf '%s %s - %s\n' "${test_result}" "${test_count}" "$*"
}

cd "${TEST_TMPDIR:?}" || exit 1

# Shared definitions from the top of rwfile.tap.
eval "$(grep -E '^(check_types|check_types_noone)=' "${tap}")"

for format in "$@"; do
  section=$(awk -v header="# ${format} format" '
    $0 == header { emit = 1; next }
    /^# / { emit = 0 }
    emit { print }
  ' "${tap}")
  if test -z "${section}"; then
    echo "No '# ${format} format' section found in ${tap}" >&2
    exit 1
  fi
  eval "${section}"
done

echo "1..${test_count}"
if test "${test_count}" -eq 0; then
  echo "No tests were run" >&2
  exit 1
fi
if test "${failures}" -ne 0; then
  echo "${failures} of ${test_count} tests failed" >&2
  exit 1
fi
