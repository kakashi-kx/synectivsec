# SynectivSec

**A composition theory for federated agent authority.**

Spec. Formal verification. Attack harness. (In progress.)

---

## What This Is

SynectivSec is a formal model for the **composition** of three layers that
exist independently in the 2026 agent-security literature:

- **Delegation chains** — how authority attenuates across hops
- **Sequence policies** — how actions compose over time
- **Cross-organizational federation** — how authority crosses trust boundaries

Each layer has been formalized separately. No one has stated or proved
the composition theorem — the conditions under which composing all three
preserves the safety invariants of each.

SynectivSec states that theorem and begins its verification.

---

## Prior Art

This work does not claim to invent delegation chains, sequence policies,
or federation. Each exists:

- **SentinelAgent** (arXiv:2604.02767) — Delegation Chain Calculus, TLA+ verified
- **Bounded Agents** (arXiv:2608.15888) — Agentic Principal Chain, sequence policy
- **AgentRFC** (arXiv:2603.23801) — Composition Safety principle
- **Spera** (arXiv:2603.15973) — Non-Compositionality of Safety Theorem
- **OAP** (arXiv:2603.20953) — Pre-action authorization
- **PCAS** (arXiv:2602.16708) — Policy compiler for secure agentic systems
- **AgentGuardian** (arXiv:2601.10440) — Learned access control
- **Wang** — Federated Governance Testbed
- **COA-MAS v2** — Cross-domain governance meta-framework
- **Tallam** — Authorization Propagation formalization

The novel contribution is the composition operator, the compatibility
conditions, and the positive composition theorem — not the individual layers.

---

## Status

**v0.1 — first verified instance.**

The minimal composition instance (6 principals, 2 delegation chains,
3 trust domains, capability attenuation, global sequence policy, bounded
history) has been model-checked with TLC:

```
Model checking completed. No error has been found.
1825939 states generated, 60490 distinct states found, 0 states left on queue.
Depth of the complete state graph search: 7.
```

Four invariants verified: CI1 (authority containment), CI2 (sequence
soundness), CI4 (attestation soundness), CI5 (boundary determinism).

CI3 (revocation freshness) is trivially satisfied in the current model
and requires strengthening. See `tla/RESULT.md`.

---

## Repository Structure

```
synectivsec/
├── tla/
│   ├── Composition.tla     # TLA+ model
│   ├── Composition.cfg     # TLC configuration
│   ├── RESULT.md           # Verification result and interpretation
│   └── RESULT.txt          # Raw TLC output
├── redteam/                # Composition attack harness (in progress)
├── docs/                   # Algebra, policy, federation specifications
├── paper/                  # Research paper (in progress)
└── README.md
```

---

## How to Reproduce

Requirements: Java 17+, tla2tools.jar from https://github.com/tlaplus/tlaplus/releases

```bash
cd tla
java -XX:+UseParallelGC -jar tla2tools.jar -config Composition.cfg Composition.tla
```

Expected output: `Model checking completed. No error has been found.`

---

## Open Problems

1. CI3 (revocation freshness) — currently trivially satisfied; needs
   action-level principal tracking to become non-trivial
2. Unbounded verification — current model is bounded (time <= 6);
   inductive or symbolic proof of the general theorem is open
3. Scale — minimal instance verified; scaling to more chains, domains,
   and layered policies is future work
4. CBAT novelty — cross-boundary attestation transitivity may re-derive
   1990s trust management results (SPKI/SDSI, Abadi-Burrows-Lampson);
   honest positioning requires checking and citing

---

## Author

Solo security researcher and red teamer.

---

## License

TBD — spec under CC-BY, code under Apache 2.0 (proposed)
EOF
```
