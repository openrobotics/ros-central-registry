#!/bin/sh
# Runs an upstream test program the way Magick++/tests/tests.tap does.
#
# Usage: run_in_srcdir.sh <file-in-srcdir> <program> [args...]
#
# SRCDIR is set to the directory containing <file-in-srcdir> (with a trailing
# slash, as the tests concatenate it directly with file names) and the
# program is run from $TEST_TMPDIR so that its output files land there.
set -eu

here=$(pwd)
abspath() {
  case "$1" in
    /*) printf '%s\n' "$1" ;;
    *) printf '%s\n' "${here}/$1" ;;
  esac
}

SRCDIR="$(dirname "$(abspath "$1")")/"
export SRCDIR
program=$(abspath "$2")
shift 2

cd "${TEST_TMPDIR:?}"
exec "${program}" "$@"
