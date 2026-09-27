# The SynectivSec Federation Model

**Formal specification of the federation layer.**

---

## 0. Scope

This document specifies the federation layer of the composition algebra (see
`ALGEBRA.md` §1.5 for the object definition). It defines:

- **Trust domains** and their identification (§1)
- The **attestation relation** and its reachability closure (§2)
- **Cross-Boundary Attestation Transitivity (CBAT)** with prior-art citation
  (§3)
- **Revocation propagation** and the RS condition (§4)
- **Federation graph evolution** as an open item (§5)
- **Relation to prior work** (§6)
- **Open items** (§7)

The federation layer is the **F** component of the composition operator
`D ⊗ S ⊗ F`. It governs how authority crosses organizational boundaries.

---

## 1. Trust Domains

### 1.1 Definition

A **trust domain** is a named administrative region of policy and trust
authority. Each domain is associated with:

- A **root key** `K_T` — the public key that anchors authority in the domain
- A **policy set** `Π_T ⊆ Policy` — the sequence and action policies enforced
  within the domain (see `POLICY.md`)
- A **name** `T` — a globally unique identifier

```
Domain = ⟨T, K_T, Π_T⟩
```

### 1.2 Domain Identity

Domains are identified by their root key's hash, following the SDSI/SPKI
convention (RFC 2693 §2.5). A domain's name `T` is a label; the canonical
identifier is `hash(K_T)`.

**Prior art.** Lampson et al. 1992 §2 introduces "principals" with keys as
identifiers. SPKI RFC 2693 §2.5 formalizes "inescapable identifiers" via key
hashes. SDSI 1.0 (Rivest & Lampson 1996) defines local name spaces anchored by
keys.

### 1.3 The Set of Domains

A federation graph includes a finite set of domains:

```
Τ = { T₁, T₂, …, Tₘ } ⊆ Domain
```

Domains not in `Τ` are external — the federation graph does not constrain
their behavior, and they cannot participate in attestation within the graph.

### 1.4 Root Authority

Each domain `T` grants authority to principals within it. A principal's **root
domain** is the domain whose root key authorized its delegation chain. In the
composition algebra (`ALGEBRA.md` §1.6), `RootDomain(p)` is a function from
principals to their root domains.

**Root authority is not transitive by default.** A principal rooted in `T₁`
has authority in `T₁` but not necessarily in `T₂`. Crossing to `T₂` requires
attestation (§2).

---

## 2. The Attestation Relation

### 2.1 Definition

The **attestation relation** over domains is:

```
Α ⊆ Τ × Τ
```

`Α(Tᵢ, Tⱼ)` means "Tᵢ attests Tⱼ's claims" — that is, Tᵢ accepts Tⱼ's authority
assertions as valid input to its policy decisions.

**Attestation is not trust in the informal sense.** It is a directional,
declared relation: Tᵢ has decided to recognize Tⱼ's authority claims for some
class of statements. The relation may be mutual, one-directional, or absent
depending on policy.

### 2.2 Attestation Reachability

The **reachable set** from domain `T` under `Α` is:

```
Reach(F, T) = { T } ∪ { T' : (T, T') ∈ Α }
           ∪ { T'' : ∃ T'. (T, T') ∈ Α ∧ (T', T'') ∈ Α }
           ∪ …
```

Closure over the transitive closure of `Α`.

**Base case:** A domain always reaches itself (`T ∈ Reach(F, T)`).

**Direct attestation:** `Α(T, T')` implies `T' ∈ Reach(F, T)`.

**Transitive reach:** If `Α(T, T')` and `Α(T', T'')`, then `T'' ∈ Reach(F, T)`
— this is the CBAT closure, formalized in §3.

### 2.3 Reachability is Bounded by CBAT

Without CBAT, reachability is:

```
Reach_no_CBAT(F, T) = { T } ∪ { T' : (T, T') ∈ Α }
```

Only direct attestations. This is the case that permits **attestation
laundering**: a domain T' can be induced to accept claims from T'' that T
authorized, even though T did not directly attest T''.

**CBAT (§3) extends reachability to the transitive closure.** This prevents
laundering by requiring that the trust is either transitive or explicitly
bounded.

### 2.4 Attestation Relation in the Verified Instance

The verified TLA+ instance (`tla/Composition.tla`) uses:

```
Τ = { T1, T2, T3 }
Α = { (T1, T2), (T2, T3) }
```

Reachability:
- `Reach(F, T1) = { T1, T2, T3 }` (direct + transitive via T2)
- `Reach(F, T2) = { T2, T3 }` (direct)
- `Reach(F, T3) = { T3 }` (no attestations out)

**This asymmetry is intentional.** The instance is designed so that principals
rooted in T1 can act in all three domains, principals rooted in T2 can act in
T2 and T3, and principals rooted in T3 cannot cross to other domains. The
composition theorem must hold under this asymmetric reachability.

---

## 3. Cross-Boundary Attestation Transitivity (CBAT)

### 3.1 Statement

The **CBAT condition** is:

```
CBAT(F) ≡ ∀ Tᵢ, Tⱼ, Tₖ ∈ Τ.
    Α(Tᵢ, Tⱼ) ∧ Α(Tⱼ, Tₖ) ⟹
        Α(Tᵢ, Tₖ) ∨ explicitly_bounded(Tᵢ, Tₖ)
```

**Informally:** If Tᵢ attests Tⱼ, and Tⱼ attests Tₖ, then Tᵢ must attest Tₖ —
either by transitivity or by explicitly declaring a bound.

**When the condition is not satisfied:** there exists a triple (Tᵢ, Tⱼ, Tₖ)
where Α holds on both steps but neither Α(Tᵢ, Tₖ) nor an explicit bound exists.
In this case, reachability is ambiguous: does Tᵢ accept Tₖ's claims or not?

**This ambiguity is the attack surface for attestation laundering.**

### 3.2 The "Explicitly Bounded" Clause

The `explicitly_bounded(Tᵢ, Tₖ)` predicate allows Tᵢ to declare that although
it attests Tⱼ, and Tⱼ attests Tₖ, Tᵢ does *not* transitively accept Tₖ's
claims. This is the "qualified speaks-for" idea from Lampson et al. 1992 §3.3.

**Formalization.** An explicit bound is a signed statement from Tᵢ:

```
bound(Tᵢ, Tₖ, scope)
```

where `scope` describes the class of claims for which transitivity does not
apply.

**In the verified instance**, no explicit bounds are present — CBAT is
satisfied by direct transitivity, since `Α(T1, T2)` and `Α(T2, T3)` imply
`Reach(F, T1)` includes T3.

### 3.3 Prior Art: CBAT Restates Lampson et al. 1992

**This is the crucial honest point about CBAT.** The condition is *not* novel.

**Primary source:** Lampson, Abadi, Burrows, Wobber, "Authentication in
Distributed Systems: Theory and Practice," ACM TOCS 10(4):265–310, 1992, §3.2.

The paper states, in §3.2 (verbatim from the OCR'd primary source):

> *"It is also easy to show that ⊢ is monotonic in both arguments and that ⇒
> is transitive."*

The `⇒` here is "speaks for" — the domain-level transitivity that CBAT
formalizes as a condition on `Α`.

The paper also states, in §3.3 (note on axiom P10):

> *"In this paper we take (P10) as an axiom for simplicity. However, it is
> preferable to assume only some instances of (P10)—the general axiom is too
> powerful, for example when A represents a group. If the conclusion uses a
> qualified form of ⇒ it may be more acceptable."*

The "qualified form of ⇒" is exactly CBAT's `explicitly_bounded` clause.

**Subsequent formalizations:**
- **SPKI RFC 2693 §6.3** — 5-tuple reduction implements cross-domain
  authorization propagation through the `S1 = I2` condition. This is the
  transitivity of certificate chains.
- **RT (Li, Mitchell, Winsborough, IEEE S&P 2002)** — linked roles
  (`A.r1.r2`) are an explicit mechanism for controlling how far a role or
  trust relationship propagates across domain boundaries. RT was built
  specifically because the blanket transitivity of ABLP/SPKI was recognized
  as too strong for cross-domain delegation.

**Conclusion.** CBAT restates Lampson et al. 1992's speaks-for transitivity
with the bounded variant the same paper suggests. It is not a novel condition.
See POSITIONING.md §2.2 for the full prior-art accounting.

### 3.4 What Makes CBAT Non-Trivial in the Composition

CBAT is trivial as a condition on its own — transitivity of a relation is
either true or false. **What is non-trivial is CBAT's role in the composition
theorem.**

The composition fails if CBAT is violated because:
- A principal rooted in Tᵢ can act in Tₖ without Tᵢ's policy having approved
  it.
- The attestation soundness invariant CI4 (`ALGEBRA.md` §4.4) requires that
  the acting principal's root domain reaches the current domain — and
  reachability is defined by CBAT-closed Α.

**This is why CBAT is a necessary condition** — not because the condition is
deep, but because its absence breaks a composition invariant.

The attack harness (`redteam/cbat/attestation_laundering.py`) demonstrates this
by disabling attestation reachability at the guard level and observing a CI4
violation.

---

## 4. Revocation Propagation

### 4.1 The RS Condition

The **Revocation Synchronization** condition is:

```
RS(F, δ) ≡ ∀ Tᵢ, Tⱼ ∈ Τ.
    path(Α, Tᵢ, Tⱼ) ⟹
        revoke(Tᵢ, t) ⟹ effective(Tⱼ, t + δ)
```

**Informally:** If a principal is revoked in domain Tᵢ at time t, then
revocation must be effective in every domain reachable from Tᵢ within δ time
units.

**δ** is the **revocation propagation bound** — a parameter of the federation
graph.

### 4.2 Revocation as a Domain-Level Event

Revocation in SynectivSec is a statement made by a domain:

```
revoke(Tᵢ, p, t)
```

where Tᵢ declares that principal `p` was revoked at time `t`.

**Revocation propagates through attestation.** If Tᵢ attests Tⱼ, then Tⱼ must
accept Tᵢ's revocation statements subject to the δ bound.

**Revocation is not symmetric.** Tᵢ revoking `p` does not imply Tⱼ can revoke
`p` in Tᵢ.

### 4.3 Freshness and the δ Bound

The bound δ is a **freshness parameter**. The design question is (following
SPKI RFC 2693 §5.4):

> *"How long are you willing to let the world believe and act on a statement
> you know to be false?"*

The answer defines δ. A short δ means tighter revocation (less window for stale
authority) but requires faster propagation. A long δ permits slower propagation
but leaves a longer attack window.

**In the verified instance**, δ is represented implicitly: revocation is
immediate (`revokedAt[p] = time` at the moment of revocation), and all domains
see the same revocation state. **This is the strongest possible RS** — δ = 0.
A more realistic model with asynchronous propagation is future work (§7).

### 4.4 Prior Art: RS Restates SPKI Validity Intervals

SPKI RFC 2693 §5.2 (Timed CRLs) and §5.4 (Setting the Validity Interval)
formalize the time-bounded validity of certificates. A certificate is valid
for an interval `[not-before, not-after]`; outside that interval, it is
treated as revoked.

**RS applies this concept to a domain graph with an explicit propagation bound
δ.** Where SPKI treats validity as a per-certificate concern, RS treats it as
a graph-wide synchronization requirement.

**Whether this joint formulation is novel** is flagged in POSITIONING.md §5 as
requiring primary-source verification. To the best of our knowledge at the
time of writing, no prior work formalizes bounded-time revocation propagation
as a joint compatibility condition with transitive attestation across a
domain graph.

**Note the honest framing:** RS is SPKI's validity-interval idea applied to a
domain graph. If the joint formulation turns out to have prior art, the
framing adjusts. The composition theorem's necessity of RS remains true
regardless — the attack harness demonstrates it.

### 4.5 Revocation and the Composition

RS is one of the three guards on the composition:

- G2 (`ALGEBRA.md` §2.1): `t < r[p]` — no action after revocation
- The RS condition ensures that `r[p]` is consistent across domains

**Without RS, the following attack is possible:** a principal is revoked in
Tᵢ, but Tⱼ has not yet received the revocation and permits the principal to
act. This is the "revocation race" — CA-4 in the attack catalog.

**The attack harness** (`redteam/rs/revocation_race.py`) demonstrates this by
disabling the guard-level revocation check and observing a CI3 violation.

---

## 5. Federation Graph Evolution

### 5.1 Static vs. Dynamic Federation

The composition algebra (`ALGEBRA.md` §1.5) treats the attestation relation Α
as a **compile-time constant**. Domains do not join or leave the federation
during the composition; Α is fixed.

**This is a simplification.** Real federations evolve: domains are added,
attestation relations are established or revoked, root keys rotate.

### 5.2 What Would Change with Dynamic Α

If Α is allowed to evolve during the composition, the following invariants
become harder to maintain:

- **CBAT** must hold *at every point in time*, not just initially.
- **RS** must propagate to domains that join *after* a revocation occurred.
- **Reachability** (`Reach(F, T)`) becomes a time-varying set.

**A dynamic-Α model is future work.** The current composition theorem assumes
static Α, and the verified instance reflects that.

### 5.3 Why Static Α Is Sufficient for the Initial Result

The composition theorem's structure — three compatibility conditions, three
invariants, one preservation result — is orthogonal to whether Α is static or
dynamic. **The theorem holds for static Α; extending to dynamic Α requires
restating the theorem under a temporal operator.**

**The initial result claims the static case.** This is honest: the theorem is
verified for static federation graphs, and the dynamic case is open.

---

## 6. Relation to Prior Work

### 6.1 Attestation and Trust Management

| Work | Contribution | Relation to SynectivSec |
|---|---|---|
| Lampson et al. 1992 (TOCS) | Speaks-for relation, transitivity, bounded variant | CBAT restates this |
| SPKI RFC 2693 | Certificate chain reduction, validity intervals | RS restates §5.4; CBAT restates §6.3 |
| SDSI 1.0 (Rivest & Lampson 1996) | Local names anchored by keys | Domain identity convention |
| RT (Li, Mitchell, Winsborough 2002) | Linked roles bound cross-domain trust | Closest prior art to CBAT's bounded variant |
| PolicyMaker/KeyNote (Blaze et al.) | Policy-assertion-based trust | Alternative framework; not directly composed |

### 6.2 Modern Federation Models

| Work | Contribution | Relation to SynectivSec |
|---|---|---|
| Wang, Federated Governance Testbed | Multi-principal federation without trusted center | Compatible framework; not directly composed |
| COA-MAS v2 | Cross-domain governance meta-framework | Compatible; SynectivSec is a specific instantiation |
| A2A (Linux Foundation) | Agent-to-agent transport | Transport layer; SynectivSec is above it |
| MCP (Anthropic) | Tool-calling protocol | SynectivSec composes above MCP |

### 6.3 Composition Frameworks

| Work | Contribution | Relation to SynectivSec |
|---|---|---|
| Spera 2026 (arXiv 2603.15973) | Negative composition result for AI agents | SynectivSec is the positive counterpart |
| AgentRFC 2026 (arXiv 2603.23801) | Composition Safety for protocols | Related principle; SynectivSec composes three specific layers |
| McLean 1994 | Composition theory for security properties | Foundational; SynectivSec's theorem instantiates it for agent authority |

### 6.4 What Is Novel

**Nothing in the federation layer itself is novel.** The primitives (attestation
transitivity, revocation validity intervals, key-anchored domain identity) are
all from the 1990s–2000s trust-management literature.

**What is novel is:**

1. **CBAT's role in the composition theorem** — CBAT is not novel as a
   condition, but its role as a compatibility condition for preserving CI4
   under composition is new.
2. **RS as a joint constraint with CBAT** — the pairing of attestation
   transitivity with a time-bounded revocation synchronization requirement
   across a domain graph. **Flagged as needing primary-source verification.**
3. **The specific instantiation to AI agent authority** across tool-calling
   protocols.

See POSITIONING.md §3 for the full novelty claim.

---

## 7. Open Items

1. **Systematic prior-art check for RS as a joint constraint.** The claim that
   no prior work couples time-bounded revocation propagation with transitive
   attestation across a domain graph requires a systematic literature search
   of the trust-management field (1993–2010) and modern agent-federation work
   (2023–2026). **This is the single most important open verification.**

2. **Dynamic federation graph.** The current model treats Α as static.
   Allowing domains and attestation relations to evolve during the composition
   requires restating the theorem with a temporal operator.

3. **Cross-domain policy reconciliation.** Different domains have different
   sequence policies (`POLICY.md` §2.4). The effective policy at a boundary is
   the conjunction, but the *protocol* by which domains agree on the effective
   policy is not specified.

4. **Revocation propagation protocol.** The RS condition specifies *what* must
   hold (revocation effective in δ time), not *how* to achieve it. A protocol
   for propagating revocations across the federation graph is future work.

5. **Root key rotation.** The federation model assumes static root keys.
   Key rotation — a domain updates its root key while preserving identity —
   requires extending the CBAT formalization.

6. **Comparison to Wang's testbed and COA-MAS v2.** A direct comparison of the
   composition theorem's conditions against the trust frameworks in these
   works is required for the paper's related-work section.

7. **δ as a runtime parameter.** The verified instance uses δ = 0 (immediate
   propagation). A model with δ > 0 requires explicit revocation state per
   domain and a mechanism for tracking propagation lag.

---

## 8. Formal Summary

| Element | Definition |
|---|---|
| Trust domain | `T = ⟨name, K_T, Π_T⟩` |
| Domain set | `Τ = {T₁, …, Tₘ}` |
| Attestation relation | `Α ⊆ Τ × Τ` |
| Reachability | `Reach(F, T)`, transitive closure over Α |
| CBAT condition | `∀ Tᵢ, Tⱼ, Tₖ. Α(Tᵢ, Tⱼ) ∧ Α(Tⱼ, Tₖ) ⟹ Α(Tᵢ, Tₖ) ∨ explicitly_bounded(Tᵢ, Tₖ)` |
| Revocation event | `revoke(Tᵢ, p, t)` |
| RS condition | `∀ Tᵢ, Tⱼ. path(Α, Tᵢ, Tⱼ) ⟹ revoke(Tᵢ, t) ⟹ effective(Tⱼ, t + δ)` |
| Invariant | CI4 (Attestation Soundness, `ALGEBRA.md` §4.4), CI3 (Revocation Freshness, `ALGEBRA.md` §4.3) |

---

*Last updated: 2026-09-27*
