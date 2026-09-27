#!/usr/bin/env bash
set -u
cd "$(dirname "${BASH_SOURCE[0]}")"
PASS=0; FAIL=0
echo "=== SynectivSec Red Team Harness ==="
run() {
    echo "--- $1 ---"
    if python3 "$2"; then PASS=$((PASS+1)); echo "[OK] $1"
    else FAIL=$((FAIL+1)); echo "[FAIL] $1"; fi
    echo ""
}
run "PC: alphabet escape"          pc/alphabet_escape.py
run "RS: revocation race"          rs/revocation_race.py
run "CBAT: attestation laundering" cbat/attestation_laundering.py
echo "=== $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
