# Red Team Harness — Final Results

**Date:** 2026-09-27
**Tool:** TLC2 v2.19, 4 workers

## Results

| Attack | Condition broken | Invariant violated | Result |
|---|---|---|---|
| PC: alphabet escape | Guard-level sequence policy disabled | CI2 Sequence Soundness | **ATTACK SUCCEEDED** |
| RS: revocation race | Guard-level revocation check removed | CI3 Revocation Freshness | **ATTACK SUCCEEDED** |
| CBAT: attestation laundering | Guard-level attestation reach disabled | CI4 Attestation Soundness | **ATTACK SUCCEEDED** |

**3 passed, 0 failed.**

## Design

Each attack operates at the **guard level**:
- The strict helper (e.g., `SequencePolicyOK`) is kept unchanged and used by the invariant.
- A separate guard helper (e.g., `Guard_SequencePolicy`) is used by `DoAction`.
- The attack weakens only the guard. The invariant stays strict.
- Result: weakened guard permits disallowed transitions; strict invariant catches them.

## Interpretation

**PC, RS, and CBAT are each necessary.** Removing any one produces a
concrete TLA+ counterexample. Together with the verification in `tla/`
(which shows the theorem holds when all three are satisfied), this
establishes that the three conditions are **jointly sufficient and
individually necessary**.

**The Composition Preservation Theorem is tight.**

## Reproducing

```bash
cd redteam
./run_all.sh
```

Expect: `3 passed, 0 failed`.

## Combined Result

| Artifact | Evidence |
|---|---|
| `tla/RESULT.md` | 11,185,890 states, 300,447 distinct, 0 violations — theorem holds |
| `redteam/RESULTS.md` | 3 attacks, 3 successes — each condition is necessary |

Together: the composition preserves CI1–CI5 **if and only if** PC ∧ RS ∧ CBAT hold.
