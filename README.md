# SynectivSec

**A composition theorem for federated agent authority.**

Spec. Model-checked verification. Attack harness. Research artifact — not a product.

**Author:** Abhijith S ([@kakashi-kx](https://github.com/kakashi-kx), [LinkedIn](https://www.linkedin.com/in/abhixjith)) — independent security researcher.

---

## What This Is

Three layers of AI-agent security exist independently in the current literature:
delegation chains (how authority attenuates across hops), sequence policies (how
actions compose over time), and cross-organizational federation (how authority
crosses trust boundaries). Each has been formalized on its own. We have not
found the composition theorem — the conditions under which composing all three
preserves the safety invariants each guarantees individually — stated or proved
in that literature. Spera (2026) proves a negative result showing composition
can break safety in the adjacent multi-agent capability setting.

SynectivSec states and model-checks the positive composition theorem: three
compatibility conditions, sufficient (and, per the attack harness below,
individually necessary) for the composition to preserve five safety invariants.

---

## The Theorem

Let `D` be a delegation chain, `S` a sequence policy, `F` a federation graph.
Their composition `D ⊗ S ⊗ F` is a labeled transition system (full construction
in `docs/ALGEBRA.md`).

**Composition Preservation Theorem.** If three compatibility conditions hold —

- **PC** (Policy Compatibility) — every action producible under any chain in `D`
  is classified by `S`'s action alphabet
- **RS** (Revocation Synchronization) — revocation in one trust domain propagates
  to every domain reachable by an attestation path within a bounded time `δ`
- **CBAT** (Cross-Boundary Attestation Transitivity) — attestation composes
  across domains unless a domain explicitly bounds it

— then the composition preserves five invariants: authority containment (CI1),
sequence soundness (CI2), revocation freshness (CI3), attestation soundness
(CI4), and boundary determinism (CI5).

**Each of the three conditions restates prior work:**

| Condition | Restates | Where |
|---|---|---|
| CBAT | Speaks-for transitivity: "it is also easy to show that ⊢ is monotonic in both arguments and that ⇒ is transitive" | Lampson, Abadi, Burrows, Wobber, *Authentication in Distributed Systems: Theory and Practice*, ACM TOCS 10(4):265–310, 1992, §3.2 *(primary source verified)* |
| CBAT (bounding) | The same paper's suggestion to use a qualified form of transitivity: "the general axiom is too powerful... if the conclusion uses a qualified form of ⇒ it may be more acceptable"; closest formal analog is RT's linked roles | Lampson et al. 1992 §3.3 (note on P10) *(primary source verified)*; Li, Mitchell, Winsborough, *RT: A Role-Based Trust-Management Framework*, IEEE S&P 2002 *(primary source pending)* |
| RS | Validity intervals on certificates: "How long are you willing to let the world believe and act on a statement you know to be false?" | RFC 2693, SPKI Certificate Theory, §5.4 *(primary source verified)* |
| PC | Scope/budget tracking across sequences of actions | Bounded Agents, arXiv:2608.15888, 2026 *(secondary source)* |

The claimed contribution is the composition operator, the three conditions taken
*jointly*, and the preservation theorem over their combination — not any
condition on its own. See `docs/POSITIONING.md` for the full prior-art
treatment, including SentinelAgent, AgentRFC, Wang, COA-MAS v2, OAP, PCAS, and
AgentGuardian.

---

## Verification Status

**Model-checked on a bounded instance. Not proved in general.**

```
Instance: 6 principals, 2 delegation chains, 3 trust domains, capability
          attenuation, global sequence policy, action-level principal
          tracking with revocation timestamps.
State constraint: time ≤ 4, Len(history) ≤ 3.

Model checking completed. No error has been found.
11,185,890 states generated, 300,447 distinct states found, 0 violations.
Depth of the complete state graph search: 5.
Runtime: ~33 seconds on 4 parallel workers.
```

Reproduce with Java 17+ and `tla2tools.jar`:

```
cd tla
java -XX:+UseParallelGC -jar tla2tools.jar -workers 4 -config Composition.cfg Composition.tla
```

**What this result does and does not show:**

- **CI1–CI5 are all verified as non-trivial.** The model exercises real
  attenuation, sequencing, revocation, attestation, and boundary structure.
  TLC exhausts the reachable state space and finds zero violations.
- **CI3 (revocation freshness)** is non-trivial: the model tracks each
  principal's revocation timestamp (`revokedAt`) and checks every historical
  action against its actor's revocation time
  (`history[i].at < revokedAt[history[i].principal]`). The guard on the
  transition relation prevents post-revocation actions, and the invariant
  confirms none occur.
- **The result is bounded.** `time ≤ 4`, one specific instance size. It is
  evidence for the theorem, not a proof of it. The unbounded, general case is
  open. See Open Problems.

---

## Attack Harness

The contrapositive of the theorem — drop any one compatibility condition and a
concrete invariant violation exists — is what makes the theorem falsifiable
rather than definitional. `redteam/` implements one runnable attack per
condition, each constructing a composition state that satisfies the other two
conditions but violates the invariant tied to the dropped one:

- **PC violation** — an action reachable under a delegation chain but outside
  the sequence policy's recognized alphabet → CI2 violated
- **RS violation** — action taken in the propagation window before a
  cross-domain revocation takes effect → CI3 violated
- **CBAT violation** — attestation accepted across a domain boundary where
  transitivity was supposed to be explicitly bounded → CI4 violated

All three attacks succeed. Run them with `./redteam/run_all.sh`. Full results
in `redteam/RESULTS.md`.

This is the tightness argument: the three conditions aren't a conservative
superset of what's needed, they're individually load-bearing.

---

## How to Break This

The attack harness only proves the three conditions are necessary in the
constructions we wrote. It does not prove they're jointly *sufficient* beyond
the bounded instance, and it does not prove no fourth condition is needed.

If you can construct a composition state where PC, RS, and CBAT all hold and a
CI1–CI5 invariant is nonetheless violated, that falsifies the theorem as
stated. File it as an issue against `redteam/` with a minimal reproduction —
that is the single most useful contribution this repository can receive.

---

## Repository Structure

```
synectivsec/
├── tla/
│   ├── Composition.tla     # TLA+ model
│   ├── Composition.cfg     # TLC configuration
│   ├── RESULT.md           # Full verification result and interpretation
│   └── RESULT.txt          # Raw TLC output
├── redteam/                # Attack harness — one script per condition
├── docs/
│   ├── ALGEBRA.md          # Formal construction of D ⊗ S ⊗ F
│   ├── POLICY.md           # Sequence policy language
│   ├── FEDERATION.md       # Cross-domain trust and revocation propagation
│   ├── AUDIT.md            # Tamper-evident logging, external verification
│   └── POSITIONING.md      # Full prior-art treatment
├── paper/                  # Research paper (in progress)
├── LIMITATIONS.md
├── CONTRIBUTING.md
├── CITATION.cff
└── README.md
```

---

## Open Problems

1. **Unbounded verification is open.** TLC checks one bounded instance
   (`time ≤ 4`). An inductive invariant proof or a Lean/Coq formalization of
   the general theorem has not been attempted.
2. **Scale.** The verified instance is minimal (6 principals, 2 chains, 3
   domains). Whether the theorem and this TLA+ approach remain tractable at
   realistic scale is unexamined.
3. **RS's joint formulation requires primary-source verification.** The
   pairing of time-bounded revocation propagation with transitive attestation
   as a single compatibility condition is claimed as novel. A systematic
   search of the 1990s–2010s trust-management literature is required.
4. **CBAT / RT overlap not yet fully reconciled.** RT's linked roles are cited
   as the closest prior mechanism for CBAT's bounding clause; a precise
   statement of where CBAT extends RT versus restates it is not yet written.
   See `docs/POSITIONING.md`.
5. **Comparison to SentinelAgent and AgentRFC.** The delegation layer overlaps
   with SentinelAgent's DCC; the composition concern overlaps with AgentRFC's
   Composition Safety principle. Direct comparison on the same instance is
   required for the paper.

Full limitation list: `LIMITATIONS.md`.

---

## Author

**Abhijith S** — independent security researcher and red teamer. Solo project.

- GitHub: [@kakashi-kx](https://github.com/kakashi-kx)
- Handle: `kakashi4kx`
- LinkedIn: [www.linkedin.com/in/abhixjith](https://www.linkedin.com/in/abhixjith)

---

## License

- **Code** (`tla/`, `redteam/`): Apache License 2.0 — see `LICENSE`
- **Documentation** (`docs/`, `README.md`): CC-BY 4.0 — see `LICENSE-spec`

---

## Citation

If you use this work, cite it via `CITATION.cff` or:

> Abhijith S (kakashi-kx). "SynectivSec: A Composition Theory for Federated
> Agent Authority." 2026. https://github.com/kakashi-kx/synectivsec

---

*Last updated: 2026-09-27*
