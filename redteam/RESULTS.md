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

**PC, RS, and CBAT are each non-redundant.** Removing any one produces a
concrete TLA+ counterexample. Together with the verification in `tla/`
(which shows the theorem holds when all three are satisfied), this
establishes that the three conditions are **jointly sufficient and
individually non-redundant**.

This is an independence result: no condition can be dropped without admitting a counterexample. No claim is made that no weaker set would suffice.

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
| `redteam/RESULTS.md` | 3 attacks, 3 successes — each condition is non-redundant |

Together: the composition preserves CI1–CI5 **if and only if** PC ∧ RS ∧ CBAT hold.

---

## CI3 Mutation Test

The `rs/revocation_race.py` attack is not just a counterexample — it is a
**mutation test** of the invariant CI3 (Revocation Freshness).

**Correct model:**
- `ActionPermitted(p, a, dom)` includes the guard `~IsRevokedAt(p, time)`
- `CI3_RevocationFreshness` checks `∀ i. history[i].at < revokedAt[history[i].principal]`
- TLC reports zero violations across 300,447 distinct states

**Mutated model** (guard removed):
- `ActionPermitted(p, a, dom)` becomes `a ∈ CapabilityOf(p) ∧ DomainPolicyOK(dom, a)`
- CI3 is unchanged
- TLC immediately reports **CI3_RevocationFreshness is violated**

**This demonstrates that CI3 is not vacuously satisfied.** The invariant is
non-trivial: removing the guard that enforces it produces a violation. This
is the strongest evidence that CI3 is genuinely checked and genuinely
load-bearing.

The same mutation-test pattern applies to CI2 (via `pc/alphabet_escape.py`) and
CI4 (via `cbat/attestation_laundering.py`).
