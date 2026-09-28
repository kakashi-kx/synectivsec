# Verification Result

**Date:** 2026-09-27
**Model:** Composition.tla (v0.2)
**Tool:** TLC2 Version 2.19

## Instance
- 6 principals (R1, PA, PB, R2, PC, PD)
- 2 delegation chains (D1 rooted T1, D2 rooted T2)
- 3 trust domains (T1, T2, T3)
- Capability lattice with attenuation
- Attestation relation: T1 -> T2, T2 -> T3
- Global sequence policy: no two consecutive `send`
- Action-level principal tracking: history stores (principal, action, time)
- Per-principal revocation timestamps
- State constraint: time <= 4, Len(history) <= MaxHistory(3)

## Invariants Verified
- CI1 Authority Containment
- CI2 Sequence Soundness
- CI3 Revocation Freshness (non-trivial)
- CI4 Attestation Soundness
- CI5 Boundary Determinism

## Result

    Model checking completed. No error has been found.
    11185890 states generated, 300447 distinct states found, 0 states left on queue.
    The depth of the complete state graph search is 5.

Runtime: ~33 seconds (4 parallel workers).
Fingerprint collision probability (calculated): 1.8E-7.

## Interpretation
First verified instance of the Composition Preservation Theorem
with all five invariants non-trivial. The composition of delegation
chains, sequence policy, and federation preserves the safety invariants
of each component on the bounded state space.

## Open Items
- State space is bounded (time <= 4); unbounded verification open
- Instance is minimal (6 principals, 3 domains); scaling is future work
- CBAT (cross-boundary attestation transitivity) novelty check pending
  against SPKI/SDSI and Abadi-Burrows-Lampson trust management calculi
