# The SynectivSec Sequence Policy Language

**Formal specification of the sequence policy layer.**

---

## 0. Scope

This document specifies the sequence policy layer of the composition algebra
(see `ALGEBRA.md` §1.4 for the object definition). It defines:

- The **syntax** of sequence policies (§1)
- The **semantics** over action histories (§2)
- **Enforcement** during composition (§3)
- **Examples** including the verified instance (§4)
- **Relation to prior work** (§5)
- **Open items** (§6)

The sequence policy layer is the **S** component of the composition operator
`D ⊗ S ⊗ F`. It constrains the ordering and multiplicity of actions over time.

---

## 1. Syntax

### 1.1 Action Alphabet

A **sequence policy** is defined over a finite **action alphabet**:

```
Σ = { a₁, a₂, …, aₙ }
```

Each `aᵢ` is an atomic action class — an element of the capability set `C` used
in the delegation layer (`ALGEBRA.md` §1.2). The two sets may be identical or
the action alphabet may be a projection of the capability lattice onto
observable action classes.

**Convention.** In this document, `Σ` denotes the action alphabet and `a`
ranges over actions in `Σ`. The terms "action" and "action class" are
interchangeable.

### 1.2 History

A **history** is a finite sequence of actions:

```
h = ⟨a₁, a₂, …, aₖ⟩ ∈ Σ*
```

where `Σ*` is the free monoid on `Σ`. The empty history is denoted `ε`.

In the composition model, a history is not just a sequence of actions — each
element records the acting principal and the time of the action. But for the
purposes of the sequence policy, only the action symbol matters. The policy
sees the projection of the execution history onto `Σ*`.

### 1.3 Policy Predicate

A **sequence policy** is a predicate:

```
φ : Σ* → {⊤, ⊥}
```

`φ(h) = ⊤` means the history `h` satisfies the policy. `φ(h) = ⊥` means it
does not.

The policy must be **decidable**: for any finite `h`, `φ(h)` must be computable
in bounded time. This is a requirement for the composition to enforce the
policy at runtime.

### 1.4 Policy Classes

We distinguish three expressiveness classes, in increasing order:

**Class 1 — Regular policies.** `φ` is a regular language over `Σ`. Recognizable
by a finite automaton. Includes: prefix, suffix, substring, no-repetition
patterns of bounded length.

**Class 2 — Bounded-history policies.** `φ(h)` depends only on a bounded suffix
of `h`. The policy has a **window size** `w`, meaning `φ(h) = φ(suffix(h, w))`.
Includes: the "no two consecutive `send`" policy of the verified instance.

**Class 3 — Aggregate policies.** `φ(h)` depends on counts or aggregates over
`h`, not just the suffix. Includes: rate limits (no more than `k` actions of
type `a` in any window of size `w`), cumulative limits (no more than `k` total
actions of type `a` per session).

**The verified TLA+ instance uses Class 2:** the policy is `¬∃i. h[i] = send ∧
h[i+1] = send` — a bounded-suffix predicate with window size 2.

**The composition theorem applies to all three classes**, subject to
enforcement conditions (§3).

---

## 2. Semantics

### 2.1 Satisfaction over Histories

For a history `h ∈ Σ*`, the policy is satisfied iff `φ(h) = ⊤`. We write:

```
h ⊨ φ  iff  φ(h) = ⊤
```

### 2.2 Prefix Closure

A sequence policy φ is **prefix-closed** if:

```
h ⊨ φ ⟹ ∀ i ≤ |h|. prefix(h, i) ⊨ φ
```

That is: if a history satisfies the policy, so does every prefix. This is the
natural property for policies that constrain the *occurrence* of actions (e.g.,
"no two consecutive sends") rather than the *absence* of actions.

**Not all policies are prefix-closed.** A policy like "every session must end
with an `ack` action" is not prefix-closed: a prefix of a satisfying history
may not itself satisfy.

**The composition theorem assumes prefix-closure** for the sequence layer. This
is a restriction, not a limitation — it covers the practically important class
of safety policies (in the sense of Alpern-Schneider). Liveness policies
require separate treatment.

**Prior art.** Alpern & Schneider, "Defining Liveness," Information Processing
Letters 21(4):181–185, 1985. Schneider, "Enforceable Security Policies," ACM
TISSEC 3(1):30–50, 2000.

### 2.3 Alphabet Consistency

The policy is defined over `Σ`, but the composition includes actions from
delegation chains whose capability sets may include actions outside `Σ`. The
**Policy Compatibility** condition (PC, `ALGEBRA.md` §5.1) requires:

```
∀ d ∈ Reach(D). Actions(d) ⊆ Σ
```

That is: every action producible under any chain must be in the policy's
alphabet. If an action exists outside `Σ`, it escapes the policy constraint.

**This is the first source of composition attacks** — see `redteam/pc/` and
`redteam/RESULTS.md`.

### 2.4 Policy Composition

Two sequence policies φ₁, φ₂ over the same alphabet compose by conjunction:

```
(φ₁ ∧ φ₂)(h) ≡ φ₁(h) ∧ φ₂(h)
```

The composed policy enforces both constraints. This is the standard
intersection of languages.

**Distributed policies.** If different domains in the federation apply
different sequence policies, the effective policy is the conjunction of all
applicable policies at the current domain. This is what makes the boundary
determinism invariant (CI5, `ALGEBRA.md` §4.5) non-trivial when domains have
distinct policies.

---

## 3. Enforcement

### 3.1 Enforcement Point

The sequence policy is enforced at the **action transition** (`ALGEBRA.md`
§2.1, guard G3):

```
φ(h ⌢ ⟨a⟩) = ⊤
```

An action `a` is permitted iff appending it to the current history `h` preserves
the policy.

### 3.2 Prefix Enforcement

Because the policy is prefix-closed (§2.2), enforcement can be **incremental**:
the policy is checked at each action, and the previous satisfaction is stable.

For a bounded-history policy (Class 2), enforcement is local — it checks only
the bounded suffix. For an aggregate policy (Class 3), enforcement requires
carrying aggregate state.

### 3.3 Policy State

For Class 2 policies (bounded window `w`), the policy state is the last `w-1`
actions. This is `O(w)` space.

For Class 3 policies (aggregates), the policy state includes running counters.
This is `O(k)` space where `k` is the number of distinct aggregates.

**The verified instance uses O(1) policy state** — the last action is sufficient
to check "no two consecutive `send`."

### 3.4 Policy as a Guard

In the composition, the sequence policy is one of five guards on the action
transition (G1–G5, `ALGEBRA.md` §2.1). Sequence policy failure blocks the
action without affecting the delegation or federation layers.

**This is why policy composition is well-behaved:** the sequence policy is
orthogonal to delegation and federation, and its enforcement is local to the
transition.

### 3.5 Enforcement and Composition

The composition theorem's PC condition ensures the policy sees every possible
action. The sequence soundness invariant CI2 (`ALGEBRA.md` §4.2) ensures the
policy is never violated.

**Attacks against the sequence layer** are addressed by:

- **PC necessity** — `redteam/pc/alphabet_escape.py` disables the guard-level
  sequence policy, and CI2 fails.
- **Sequence laundering** — if two chains can interleave actions to produce a
  forbidden sequence that neither chain's local policy catches, CI2 fails.

**The composition theorem's PC condition is precisely what prevents sequence
laundering across chains.**

---

## 4. Examples

### 4.1 Verified Instance: No Two Consecutive Sends

The verified instance (`tla/Composition.tla`) uses:

```
φ(h) ≡ ∀ i ∈ 1..(|h| - 1). ¬(h[i] = send ∧ h[i+1] = send)
```

**Class 2** (window size 2). **Prefix-closed.** **O(1) policy state.**

This policy is simple enough to be checked locally, but nontrivial enough to
demonstrate that the composition constrains interleavings.

### 4.2 Rate Limit

A policy that permits no more than 3 `send` actions in any 10-action window:

```
φ(h) ≡ ∀ i ∈ 1..(|h| - 9). |{j ∈ i..i+9 : h[j] = send}| ≤ 3
```

**Class 3** (aggregate). **Prefix-closed.** **O(w) policy state** where `w = 10`.

Rate limits are a natural policy for agent governance — they prevent an agent
from spamming actions in a short window.

### 4.3 Sequence Pattern

A policy that requires any `write` action to be preceded by a `read` action:

```
φ(h) ≡ ∀ i ∈ 1..|h|. h[i] = write ⟹ ∃ j < i. h[j] = read
```

**Class 3** (aggregate: requires tracking whether `read` has occurred).
**Not prefix-closed:** a prefix ending in `write` without a prior `read`
violates the policy even if the full history satisfies it. This is a
**safety-then-liveness** hybrid.

**The composition theorem's prefix-closure assumption excludes this class.**
A more expressive enforcement mechanism (edit automata, see Ligatti, Bauer,
Walker 2005) is required to handle it.

### 4.4 Session Framing

A policy that requires each session to begin with `login` and end with `logout`:

```
φ(h) ≡ (h = ε) ∨ (h = ⟨login⟩) ∨ (∃ s, t. h = ⟨login⟩ ⌢ s ⌢ ⟨logout⟩)
```

**Not prefix-closed.** Belongs to the liveness class.

**The verified instance does not include this policy.** Future work would
extend the sequence layer to liveness constraints, at the cost of a more
expressive enforcement mechanism.

### 4.5 Composition of Multiple Policies

Two policies composed by conjunction:

```
φ(h) ≡ (no two consecutive sends) ∧ (write preceded by read)
```

Enforcement checks both. Failure of either blocks the action.

**The composition theorem applies:** PC ensures both policies see all actions;
CI2 ensures both are preserved.

---

## 5. Relation to Prior Work

### 5.1 Sequence Policies in Agent Governance

**Bounded Agents (arXiv 2608.15888, 2026)** — Agentic Principal Chain. Carries
scope and budgets across sequences of actions. This is the closest modern
analog to our sequence layer. **The sequence policy concept is not novel.**

### 5.2 Runtime Enforcement

**Schneider, "Enforceable Security Policies," ACM TISSEC 3(1):30–50, 2000** —
foundational theory of runtime enforcement. Classifies properties into safety
and liveness; characterizes what can be enforced by an inline monitor.

**Alpern & Schneider, "Defining Liveness," Information Processing Letters
21(4):181–185, 1985** — the safety/liveness dichotomy. Our prefix-closed
policies are safety properties in the Alpern-Schneider sense.

**Ligatti, Bauer, Walker, "Edit Automata: Enforcement Mechanisms for
Run-Time Security Policies," International Journal of Information Security
4(1–2):2–16, 2005** — extension of Schneider's framework with edit automata,
which can modify actions rather than only block them. Required for non-
prefix-closed policies.

### 5.3 Policy Languages

**PCAS (arXiv 2602.16708, 2026)** — Datalog-derived policy language. More
expressive than our sequence layer; may subsume it.

**OPA / Rego** — general-purpose policy language. Not specialized for
sequence policies.

**Cedar** — AWS policy language. Similar expressiveness to OPA for stateless
policies; limited sequence support.

**The SynectivSec sequence policy layer is intentionally simple** — a predicate
over histories. This makes the composition theorem tractable. A more
expressive policy language would require re-proving the theorem under stronger
enforcement mechanisms.

### 5.4 What Is Novel

**Nothing in the sequence layer itself is novel.** The policy language is a
standard history predicate. The enforcement point is standard.
Prefix-closure is standard. The rate limit and pattern examples are standard.

**What is novel is the PC condition** — the requirement that the sequence
policy's alphabet cover all actions producible under any delegation chain.
This is the condition that binds the sequence layer to the delegation layer
and makes composition attacks possible.

See `ALGEBRA.md` §5.1 for the PC formalization, and `redteam/pc/` for the
demonstration that PC is necessary.

---

## 6. Open Items

1. **Liveness policies.** The current layer handles prefix-closed safety
   policies only. Session framing, completion requirements, and other liveness
   constraints require a more expressive enforcement mechanism (edit automata,
   contract monitors).

2. **Composition of orthogonal policies.** The paper does not characterize when
   two sequence policies can be enforced independently vs. requiring joint
   evaluation. If two policies share state, the enforcement complexity is
   different.

3. **Distributed policy evaluation.** When domains have different sequence
   policies, the effective policy at a boundary is the conjunction. This is
   stated in §2.4 but not formalized as a distributed protocol.

4. **Policy learning.** Bounded Agents and AgentGuardian (arXiv 2601.10440,
   2026) demonstrate learned policies from execution traces. Integration with
   learned policies is future work — the composition theorem as stated assumes
   static policies.

5. **Runtime complexity bounds.** The enforced policy check is `O(w)` for Class
   2 and `O(k)` for Class 3. A formal complexity analysis for the composition
   as a whole (including delegation and federation checks) is future work.

---

## 7. Formal Summary

| Element | Definition |
|---|---|
| Action alphabet | `Σ = {a₁, …, aₙ}` |
| History | `h ∈ Σ*` |
| Sequence policy | `φ : Σ* → {⊤, ⊥}` (decidable) |
| Satisfaction | `h ⊨ φ` iff `φ(h) = ⊤` |
| Prefix-closure | `h ⊨ φ ⟹ ∀i. prefix(h, i) ⊨ φ` |
| PC condition | `∀ d ∈ Reach(D). Actions(d) ⊆ Σ` |
| Enforcement point | Action transition guard G3 (`ALGEBRA.md` §2.1) |
| Composition | `(φ₁ ∧ φ₂)(h) ≡ φ₁(h) ∧ φ₂(h)` |
| Invariant | CI2 (Sequence Soundness, `ALGEBRA.md` §4.2) |

---

*Last updated: 2026-09-27*
