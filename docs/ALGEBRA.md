# The SynectivSec Composition Algebra

**Formal specification of the composition operator ⊗ and the compatibility
conditions PC, RS, CBAT.**

---

## 0. Scope

This document specifies the algebra of the SynectivSec composition model. It
defines:

- The **objects** of the algebra (§1)
- The **transition relation** over composition states (§2)
- The **composition operator ⊗** (§3)
- The **invariants** CI1–CI6 (§4)
- The **three compatibility conditions** PC, RS, CBAT (§5)
- The **theorems** Composition Preservation and Emergent Authority (§6)
- The **proof strategy** and its relation to the TLA+ verification (§7)

This algebra describes what is implemented in `tla/Composition.tla`. It is the
specification; the TLA+ module is the artifact; `tla/RESULT.md` is the verified
result. The **complete proof** of the composition theorem is in `PROOF.md`.

**Prior art.** The primitives (delegation, speaks-for, attestation
transitivity, revocation validity) are from prior work cited in
`POSITIONING.md`. This document does not redefine them; it composes them.

---

## 1. Objects

### 1.1 Principal

A **principal** is a named entity that can sign statements, be delegated
authority, and perform actions.

```
Principal = { p₁, p₂, … }
```

In the verified TLA+ instance, `Principal = {R1, PA, PB, R2, PC, PD}` — six
principals arranged in two chains.

### 1.2 Capability

A **capability** is an atomic permission to perform an action of a given class.

```
Capability = { c₁, c₂, … }
```

Capabilities form a **lattice** `⟨C, ⊑⟩`:

- `⊑` is a partial order
- `c ⊑ c'` means "c is at least as strong as c'" (c permits more)
- Each principal has a capability set `κ(p) ⊆ C`

In the verified instance, `Capability = {read, write, send}` with the natural
inclusion ordering.

### 1.3 Delegation Chain

A **delegation chain** is a finite sequence of signed attenuations:

```
D = ⟨κ₀, σ₀, κ₁, σ₁, …, κₙ, σₙ⟩
```

where:
- `κ₀ ⊇ κ₁ ⊇ … ⊇ κₙ` (capability attenuation — authority only narrows)
- `σᵢ` is a signature by the holder of `κᵢ₋₁` attesting to `κᵢ`
- The root `κ₀` is granted by a root principal

`Reach(D)` is the set of actions producible under `D` without violating
attenuation.

**Prior art.** This is the standard delegation-chain model. See Lampson et al.
1992 §3.3 (handoff), SPKI RFC 2693 §6.3 (certificate chain reduction), and
SentinelAgent arXiv 2604.02767 (delegation chain calculus).

### 1.4 Sequence Context

A **sequence context** is a pair:

```
S = ⟨Σ, φ⟩
```

where:
- `Σ` is a finite action alphabet
- `φ : Σ* → {⊤, ⊥}` is a decidable predicate over finite action histories

`φ(h) = ⊤` means the history `h` satisfies the sequence policy.

`Reach(S)` is the set of histories `h ∈ Σ*` with `φ(h) = ⊤`.

In the verified instance, `φ(h)` is "no two consecutive `send` actions."

**Prior art.** Sequence policies over agent actions are a modern concern. See
Bounded Agents arXiv 2608.15888 (Agentic Principal Chain) and Schneider 2000
(Enforceable Security Policies) for the general framework.

### 1.5 Trust Domain and Federation Graph

A **trust domain** is a named region of policy and trust authority.

```
Domain = { T₁, T₂, … }
```

A **federation graph** is a tuple:

```
F = ⟨Τ, Α, δ⟩
```

where:
- `Τ = {T₁, T₂, …, Tₘ} ⊆ Domain` is the set of domains
- `Α ⊆ Τ × Τ` is the **attestation relation** — `Α(Tᵢ, Tⱼ)` means Tᵢ attests
  Tⱼ's claims
- `δ ∈ ℕ` is the **revocation propagation bound** — revocation must be effective
  in all reachable domains within δ steps

**Attestation reachability.** `Reach(F, T)` is the set of domains reachable
from `T` via `Α`, including `T` itself and direct attestations.

In the verified instance, `Τ = {T1, T2, T3}` and `Α = {(T1, T2), (T2, T3)}`.

**Prior art.** Federation without a trusted center is discussed in Wang's
Federated Governance Testbed and COA-MAS v2. Cross-domain attestation
transitivity is from Lampson et al. 1992 §3.2 and SPKI RFC 2693 §6.3 (see
CBAT in §5.3).

### 1.6 Composition State

A **composition state** is a tuple:

```
s = ⟨d, h, T, r, t⟩
```

where:
- `d ∈ Reach(D)` is the current position in a delegation chain
- `h ∈ Σ*` is the current action history
- `T ∈ Τ` is the current trust domain
- `r : Principal → ℕ` is the revocation timestamp map (∞ for never revoked)
- `t ∈ ℕ` is the logical time

**Set of all composition states:** `States(D, S, F)`.

### 1.7 Execution Trace

An **execution trace** is a finite sequence of composition states:

```
τ = ⟨s₀, s₁, …, sₙ⟩
```

where each consecutive pair is related by the transition relation (§2).

---

## 2. Transition Relation

The transition relation → on composition states is defined by three rules:

### 2.1 Action Transition

A principal `p` performs an action `a ∈ Σ` in domain `T`:

```
⟨d, h, T, r, t⟩ → ⟨d', h', T', r', t+1⟩
```

subject to guards:
- **G1 (Reachability):** `p ∈ ChainRoot(D)` and `T ∈ Reach(F, RootDomain(D))`
- **G2 (Authorization):** `a ∈ κ(p)` and `t < r[p]`
- **G3 (Sequence):** `φ(h ⌢ ⟨a⟩) = ⊤`
- **G4 (Length):** `|h| < MaxHistory`
- **G5 (Boundary):** `DomainPolicy(T, a) = ⊤`

Updates:
- `h' = h ⌢ ⟨⟨p, a, t⟩⟩` (record actor, action, time)
- `T' = T`
- `r' = r`
- `d' = d`

### 2.2 Revocation Transition

A principal `p` is revoked at time `t`:

```
⟨d, h, T, r, t⟩ → ⟨d, h, T, r', t+1⟩
```

subject to: `r[p] = ∞` (not already revoked).

Update: `r'[p] = t`.

### 2.3 Domain Transition

A principal `p` moves to a new domain `T'`:

```
⟨d, h, T, r, t⟩ → ⟨d, h, T', r, t+1⟩
```

subject to: `T' ∈ Reach(F, RootDomain(D))`.

Update: `T' = T`.

**Actions in the verified TLA+ model correspond directly to these three
transitions: `DoAction`, `Revoke`, `CrossDomain`.**

---

## 3. The Composition Operator ⊗

### 3.1 Definition

The **composition** `D ⊗ S ⊗ F` is the labelled transition system:

```
D ⊗ S ⊗ F = ⟨States, →, s₀⟩
```

where:
- `States = Reach(D) × Σ* × Τ` (with revocation state and time implicit in the
  execution)
- `→` is the transition relation from §2
- `s₀ = ⟨d₀, ε, T₀, r₀, 0⟩` is the initial state, with `r₀[p] = ∞` for all `p`

`Reach(D ⊗ S ⊗ F)` is the transitive closure of → from `s₀`.

### 3.2 The Operator

⊗ is a **binary composition over layers**, associative by construction:

```
(D ⊗ S) ⊗ F = D ⊗ (S ⊗ F)
```

This is a claim about the algebra; it is implicit in the TLA+ model (layers
share state, not components) but not separately verified. It is stated here
for completeness, not claimed as a contribution.

### 3.3 Non-Commutativity

⊗ is **not commutative in general**:

```
D ⊗ S ≠ S ⊗ D
```

because the sequence policy constrains actions, and actions are only produced
under delegation. Order matters: the composition is hierarchical, not
symmetric.

**This mirrors AgentRFC's Composition Safety principle** (arXiv 2603.23801):
composed systems behave differently from their components, and the composition
is order-sensitive.

---

## 4. Invariants

The composition preserves six invariants. Each is a predicate on execution
traces.

### CI1 — Authority Containment

Every action in the history is authorized by some principal's capability set.

```
CI1(s) ≡ ∀ i ∈ 1..|h| : ∃ p ∈ Principal : aᵢ ∈ κ(p)
```

where `h[i] = ⟨pᵢ, aᵢ, tᵢ⟩`.

**Meaning.** No action in the trace is outside the total capability set of the
system. In the verified model, `CI1_AuthorityContainment`.

### CI2 — Sequence Soundness

The action history satisfies the sequence policy.

```
CI2(s) ≡ φ(h)
```

**Meaning.** No sequence of actions violates the policy. This is the invariant
that catches **sequence composition attacks** — the "structuring" attacks
OAP §8.1 describes as open.

In the verified model, `CI2_SequenceSoundness`.

### CI3 — Revocation Freshness

No action is recorded for a principal after its revocation time.

```
CI3(s) ≡ ∀ i ∈ 1..|h| : h[i].time < r[h[i].principal]
```

**Meaning.** A revoked principal cannot act after revocation. This is the
invariant that catches **revocation races** across domains.

In the verified model, `CI3_RevocationFreshness`. This invariant is
non-trivial: removing the guard that enforces it (in `ActionPermitted`) causes
CI3 to fail, as demonstrated by `redteam/rs/revocation_race.py`.

### CI4 — Attestation Soundness

The current principal acts only in domains its chain root can reach.

```
CI4(s) ≡ currentDomain ∈ Reach(F, RootDomain(currentPrincipal))
```

**Meaning.** No principal acts outside its domain-reach closure. This is the
invariant that catches **attestation laundering** and **cross-boundary replay**.

In the verified model, `CI4_AttestationSoundness`.

### CI5 — Boundary Determinism

At every state, the applicable domain policy is unique.

```
CI5(s) ≡ ∀ T ∈ Τ. ∀ a ∈ Σ. DomainPolicy(T, a) = ⊤ ∨ DomainPolicy(T, a) = ⊥
```

**Meaning.** No action falls into an undefined policy state. This is the
invariant that catches **boundary confusion** attacks.

In the verified model, `CI5_BoundaryDeterminism`. This is trivially true in
the current model because `DomainPolicyOK` is total; it becomes non-trivial
when policies are layered or uncertain.

### CI6 — Composition Closure

The composition preserves CI1–CI5 under arbitrary extension.

```
CI6(s) ≡ ∀ s' ∈ Reach(s) : CI1(s') ∧ CI2(s') ∧ CI3(s') ∧ CI4(s') ∧ CI5(s')
```

**Meaning.** No future transition violates any of CI1–CI5. CI6 is what the
theorem is really about; CI1–CI5 are the component invariants it preserves.

**CI6 is not separately verified in the current TLA+ model** — it is what the
theorem claims, not what TLC checks. The TLC model checks CI1–CI5 on all
reachable states, which is equivalent to CI6 for the bounded instance.

---

## 5. Compatibility Conditions

Three conditions on the composition operator ensure that CI1–CI6 hold. Each is
sufficient in the theorem's hypothesis. Each is individually non-redundant per
`redteam/RESULTS.md`.

### 5.1 PC — Policy Compatibility

Every action producible under any delegation chain is classified by the
sequence policy's alphabet.

```
PC(D, S) ≡ ∀ d ∈ Reach(D). Actions(d) ⊆ Σ
```

**Meaning.** The sequence policy's action alphabet must cover all possible
actions from any delegation chain. If an action exists that the policy does not
recognize, it escapes the sequence constraint.

**Attacks prevented:** alphabet escape (CA-5), chain extension (CA-1),
cross-chain sequence laundering (CA-2).

**Non-redundancy demonstrated by:** `redteam/pc/alphabet_escape.py` — disabling
the guard-level sequence policy produces a CI2 violation.

**Prior art.** Not directly identified. This is a composition constraint
specific to our framework.

### 5.2 RS — Revocation Synchronization

If a principal is revoked in domain Tᵢ at time t, then revocation is effective
in every domain reachable from Tᵢ by any attestation path in Α, within δ:

```
RS(F, δ) ≡ ∀ Tᵢ, Tⱼ ∈ Τ. path(Α, Tᵢ, Tⱼ) ⟹
              revoke(Tᵢ, t) ⟹ effective(Tⱼ, t + δ)
```

**Meaning.** Revocation propagates across domains within δ. If it doesn't, a
revoked principal may continue acting in a domain that hasn't seen the
revocation.

**Attacks prevented:** revocation race across domains (CA-4), split-brain
revocation.

**Non-redundancy demonstrated by:** `redteam/rs/revocation_race.py` — removing
the guard-level revocation check produces a CI3 violation.

**Prior art.** SPKI RFC 2693 §5.4 formalizes validity intervals — the
per-certificate time bound. RS applies this to a domain graph with an explicit
propagation bound δ. **Whether the joint formulation is novel requires
primary-source verification** (flagged in POSITIONING.md §5).

### 5.3 CBAT — Cross-Boundary Attestation Transitivity

If Tᵢ attests Tⱼ, and Tⱼ attests Tₖ, then Tᵢ attests Tₖ — unless the transitive
reach is explicitly bounded:

```
CBAT(F) ≡ ∀ Tᵢ, Tⱼ, Tₖ ∈ Τ. Α(Tᵢ, Tⱼ) ∧ Α(Tⱼ, Tₖ) ⟹
              Α(Tᵢ, Tₖ) ∨ explicitly_bounded(Tᵢ, Tₖ)
```

**Meaning.** Attestation is transitive across domains, unless a domain
explicitly bounds its transitive trust. If transitivity fails without explicit
bounding, attestation can be laundered through intermediate domains.

**Attacks prevented:** attestation laundering (CA-3), replay across boundaries
(CA-6).

**Non-redundancy demonstrated by:** `redteam/cbat/attestation_laundering.py` —
disabling guard-level attestation reachability produces a CI4 violation.

**Prior art (verified).** CBAT **restates** the "speaks for" transitivity from
Lampson, Abadi, Burrows, Wobber, "Authentication in Distributed Systems:
Theory and Practice," ACM TOCS 10(4):265–310, 1992, §3.2. The paper states
transitivity as a derived property and explicitly notes in §3.3 that the
general form is "too powerful" and suggests qualified variants — the exact
"unless explicitly bounded" clause in CBAT. **CBAT is not a novel condition.**
See POSITIONING.md §2.2 for the full prior-art accounting.

---

## 6. Theorems

### 6.1 Composition Preservation Theorem

**Statement.** If PC ∧ RS ∧ CBAT hold, then for every invariant `CIk` in
{CI1, …, CI5}:

```
CIk(D ⊗ S ⊗ F) ⟹ CIk(D) ∧ CIk(S) ∧ CIk(F)
```

The composition preserves every component invariant.

**Proof.** A complete structural induction over the transition relation (§2)
is given in `PROOF.md`. The proof establishes that the base case satisfies
CI1–CI5 and that each of the three transition rules (Action, Revoke, Cross)
preserves all five invariants, assuming PC ∧ RS ∧ CBAT.

**Summary of the proof structure.**

- **Base case.** The initial state `s₀` satisfies CI1–CI5 (vacuously for CI1,
  CI2, CI3; by reachability reflexivity for CI4; by totality of `DomainPolicy`
  for CI5).
- **Inductive step.** Each transition preserves CI1–CI5:
  - **Action:** PC ensures the new action is in `Σ` (CI2, CI5);
    the G2 guard ensures authorization and freshness (CI1, CI3);
    CBAT ensures reachability (CI4).
  - **Revoke:** history and current domain unchanged; only `revokedAt`
    changes (CI1–CI5 preserved).
  - **Cross:** history unchanged; CBAT ensures reachability (CI4).

Each compatibility condition is used in a distinct part of the proof. See
`PROOF.md` §4 for the explicit dependencies.

**Verification.** The theorem is checked in TLA+ for the minimal instance
described in `tla/Composition.tla`. TLC exhausts the reachable state space
(11,185,890 states generated, 300,447 distinct, 0 violations of CI1–CI5). See
`tla/RESULT.md`.

### 6.2 Emergent Authority Theorem

**Statement (contrapositive of §6.1).** If ¬PC ∨ ¬RS ∨ ¬CBAT, then there exists
a trajectory `τ` in `Reach(D ⊗ S ⊗ F)` that violates at least one of CI1–CI5.

**Meaning.** Every failure of a compatibility condition yields a concrete
attack. This turns each compatibility condition into an attack surface.

**Note on terminology.** This theorem establishes **independence** of the
hypothesis: it shows each condition is non-redundant. It does not establish
**necessity** in the strong sense — that would require proving no weaker set
of conditions suffices. The weaker claim is the correct one, and it is what
the attack harness demonstrates.

**Non-redundancy demonstrated by.** Each condition's non-redundancy is
demonstrated by a runnable attack in `redteam/`:

- `redteam/pc/alphabet_escape.py` — breaks PC, CI2 violated
- `redteam/rs/revocation_race.py` — breaks RS, CI3 violated
- `redteam/cbat/attestation_laundering.py` — breaks CBAT, CI4 violated

All three attacks succeed. See `redteam/RESULTS.md`.

### 6.3 Independence of the Hypothesis

**Corollary.** PC, RS, CBAT are **jointly sufficient** and **individually
non-redundant** for the preservation of CI1–CI5 under composition.

**Meaning.** The hypothesis is independent: no condition can be dropped
without admitting a counterexample. This is not a claim of necessity in the
strong sense — no claim is made that no weaker condition set exists.

**Verification.** §6.1 establishes sufficiency (via the proof in `PROOF.md`).
§6.2 establishes non-redundancy (via the attack harness). Together they
establish independence.

---

## 7. Relation to the TLA+ Verification

### 7.1 What TLC Checks

TLC model-checks the following:

- All reachable states satisfy CI1, CI2, CI4, CI5 in `tla/Composition.tla`
- All reachable states satisfy CI3 with non-trivial action-level tracking
- Zero invariant violations across the entire reachable state space

### 7.2 What TLC Does Not Check

- **Unbounded executions.** The state space is bounded (`time ≤ 4`,
  `Len(history) ≤ MaxHistory`). Unbounded verification is open.
- **CI6 as a general closure property.** TLC checks CI1–CI5 on all reachable
  states, which is equivalent to CI6 for this bounded instance, but not
  as a general statement.
- **The proof of §6.1 as a mathematical theorem.** TLC verifies the theorem on
  one instance. The general proof is by structural induction (`PROOF.md`) and
  is not mechanically checked.

### 7.3 What the Attack Harness Checks

- Each compatibility condition is individually non-redundant (via guard-level
  weakening)
- Each attack produces a concrete TLA+ counterexample
- The set {PC, RS, CBAT} is independent

### 7.4 Bounded Instance Summary

| Parameter | Value |
|---|---|
| Principals | 6 (R1, PA, PB, R2, PC, PD) |
| Delegation chains | 2 (D1 rooted T1, D2 rooted T2) |
| Trust domains | 3 (T1, T2, T3) |
| Capabilities | {read, write, send} |
| Sequence policy | No two consecutive `send` |
| Attestation relation | T1 → T2, T2 → T3 |
| State constraint | `time ≤ 4`, `Len(history) ≤ 3` |
| Invariants checked | CI1, CI2, CI3, CI4, CI5 (all non-trivial) |
| States generated | 11,185,890 |
| Distinct states | 300,447 |
| Violations | 0 |
| Runtime | ~33 seconds |

### 7.5 Scaling

The minimal instance is designed to be tractable in seconds. Scaling to larger
instances (more principals, chains, domains, longer histories) is future work:

- **Larger instances** — attempted but the state space grows beyond what TLC
  can handle in reasonable time. See `LIMITATIONS.md`.
- **Unbounded verification** — planned. Inductive or symbolic proof.

---

## 8. Relation to Prior Work

The primitives in this algebra are cited to their sources in POSITIONING.md.
This section summarizes the relationship.

| Element | Source | Status |
|---|---|---|
| Delegation chain | Lampson et al. 1992; SPKI RFC 2693; SentinelAgent | Restatement |
| Speaks-for transitivity | Lampson et al. 1992 §3.2 | Restatement |
| Bounded transitivity | Lampson et al. 1992 §3.3 (note on P10); RT 2002 | Restatement |
| Revocation validity interval | SPKI RFC 2693 §5.4 | Restatement |
| Sequence policy | Bounded Agents 2026; Schneider 2000 | Modern restatement |
| Negative composition result | Spera 2026; AgentRFC 2026 | Cited |
| **Composition operator ⊗** | **This work** | **Novel** |
| **Three compatibility conditions (PC, RS, CBAT)** | **This work as a set** | **Novel as a set** |
| **Composition Preservation Theorem** | **This work** | **Novel** |
| **Independence result** | **This work** | **Novel** |
| **Attack harness methodology** | **This work** | **Novel** |

**The algebra is a synthesis.** It cites each primitive to its source and
claims novelty only for the composition itself.

---

## 9. Open Items

1. **Unbounded verification.** The current TLA+ model is bounded. A general
   proof (inductive or symbolic) is required for the theorem to be claimed in
   full generality. The pen-and-paper proof in `PROOF.md` covers the general
   case, but is not mechanically checked.

2. **Scaling.** The minimal instance has 6 principals. A larger instance with
   tens of principals and multiple chains is required to demonstrate that the
   theorem holds beyond the minimal case. See `LIMITATIONS.md`.

3. **CI5 as a non-trivial invariant.** In the current model, `DomainPolicyOK`
   is total, so CI5 is trivially true. A model with layered or uncertain
   policies would make CI5 non-trivial and test the boundary determinism
   property.

4. **Federation graph as first-class state.** The current model treats the
   attestation relation Α as a compile-time constant. A model where Α evolves
   (domains joining or leaving the federation) would be a stronger test.

5. **Comparison to SentinelAgent's DCC and AgentRFC's composition principle.**
   A direct comparison on the same instance is required for the paper's
   related-work section (flagged in POSITIONING.md §5).

6. **The proof has not been mechanized.** The structural induction in
   `PROOF.md` is written in natural language. A formalization in Lean, Coq,
   Isabelle, or TLAPS would strengthen the claim beyond the TLA+ instance.

---

*Last updated: 2026-09-27*
