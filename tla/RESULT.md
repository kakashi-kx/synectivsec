# Verification Result — Minimal Instance

**Date:** 2026-09-27
**Model:** Composition.tla
**Tool:** TLC2 Version 2.19

## Instance
- 6 principals (R1, PA, PB, R2, PC, PD)
- 2 delegation chains (D1 rooted T1, D2 rooted T2)
- 3 trust domains (T1, T2, T3)
- Capability lattice with attenuation
- Attestation relation: T1→T2, T2→T3
- Global sequence policy: no two consecutive `send`
- State constraint: time <= 6, Len(history) <= MaxHistory(4)

## Invariants Verified
- CI1 Authority Containment
- CI2 Sequence Soundness
- CI4 Attestation Soundness
- CI5 Boundary Determinism

## Result
Model checking completed. No error has been found.
1825939 states generated, 60490 distinct states found, 0 states left on queue.
Depth of complete state graph search: 7.
Finished in 17s.

## Interpretation
First verified instance of the Composition Preservation Theorem
for the stated invariants on the bounded state space.

## Open Items
- CI3 (Revocation Freshness) is trivially satisfied; needs strengthening
- State space is bounded (time <= 6); unbounded verification open
- Instance is minimal; scaling to more chains/domains is future work
