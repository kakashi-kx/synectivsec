# Limitations

**This document lists what SynectivSec does not do, does not prove, and does
not yet know.**

It is deliberately candid. A research artifact that hides its limitations is
not a research artifact.

---

## Verification Limitations

### The theorem is verified on a bounded instance

The TLA+ verification (`tla/Composition.tla`) exhausts the reachable state
space of a **bounded** instance:

- `time ≤ 4` — no execution longer than 4 logical steps
- `Len(history) ≤ MaxHistory = 3` — no action history longer than 3

**The verification does not establish the theorem for unbounded executions.**
An inductive or symbolic proof is required.

### The theorem is verified on a minimal instance

The verified instance has:

- 6 principals
- 2 delegation chains
- 3 trust domains
- 3 capabilities

**The verification does not establish the theorem for larger instances.**
Scaling to tens of principals and multiple chains is future work.

### The theorem is verified, not proved

TLC checks the theorem on one instance. The general proof is by structural
induction and is sketched in `docs/ALGEBRA.md` §6.1. **It is not mechanically
verified in a proof assistant.**

### CI5 is trivially satisfied in the current model

The boundary determinism invariant (`CI5`) is total in the current model
because `DomainPolicyOK` is a total function. **A model with layered or
uncertain policies would make CI5 non-trivial.**

### The federation graph is static

The attestation relation Α is a compile-time constant. **Domains do not join
or leave the federation during a composition.** Dynamic federation is future
work (`docs/FEDERATION.md` §5).

### Revocation is immediate (δ = 0)

The verified model treats revocation as instantaneous and global.
**A realistic model with propagation bound δ > 0 is future work**
(`docs/FEDERATION.md` §4.3).

### The audit layer is specified but not verified

`docs/AUDIT.md` describes the audit model, but the TLA+ verification does not
include the audit layer. **Tamper-evidence, Merkle proofs, and query privacy
are specified, not mechanically verified.**

---

## Novelty Limitations

### CBAT is not novel

Cross-Boundary Attestation Transitivity **restates** the speaks-for
transitivity from Lampson, Abadi, Burrows, Wobber, "Authentication in
Distributed Systems: Theory and Practice," ACM TOCS 10(4):265–310, 1992,
§3.2. The bounded variant is suggested in §3.3 of the same paper.
**CBAT is a restatement, not a contribution.**

### RS's joint formulation requires verification

Revocation Synchronization applies SPKI's validity-interval concept
(RFC 2693 §5.4) to a domain graph with an explicit propagation bound δ. The
**joint formulation** — pairing time-bounded revocation propagation with
transitive attestation as a single compatibility condition — is claimed as
novel but **requires a systematic primary-source search** to confirm.
See `docs/POSITIONING.md` §5.

### PC is a modern restatement

Policy Compatibility relates to Bounded Agents (arXiv 2608.15888, 2026) and
Schneider's enforceable security policies (ACM TISSEC 3(1), 2000). **The
condition itself is not novel.** Its role as a composition guard may be.

### The composition itself may be subsumed

The composition operator ⊗ and the preservation theorem may be subsumed by
existing composition frameworks (McLean 1994, Canetti's UC 2001, AgentRFC
2026). **A direct comparison is required** and is not done in this repository.

### Prior-art verification is incomplete

The following claims require primary-source verification before publication:

- Whether RS's joint formulation has prior art (`docs/FEDERATION.md` §7.1)
- The full scope of SentinelAgent's DCC (`docs/POSITIONING.md` §5.3)
- The full scope of AgentRFC's composition principle (§5.4)
- Direct comparison to Wang's testbed and COA-MAS v2 (§5.6)

**These are open, acknowledged gaps.**

---

## Scope Limitations

### The model does not address content-level attacks

SynectivSec constrains **actions and action sequences**. It does not:

- Filter the content of tool calls
- Detect prompt injection in tool responses
- Sanitize model outputs
- Verify model alignment

These are out of scope. See OAP (`docs/POSITIONING.md` §2.5) for content-level
concerns.

### The model assumes trusted enforcement infrastructure

The composition theorem assumes the enforcement point (where the guards are
checked) is trusted. **If the enforcement infrastructure is compromised, the
theorem's guarantees do not hold.** TEE-based attestation could reduce this
assumption; it is not part of the current model.

### The model does not address availability

Denial-of-service, resource exhaustion, and liveness are out of scope.
The theorem concerns safety invariants only.

### The model does not address key compromise

The model assumes signing keys are not compromised. **Root key compromise
invalidates the delegation and federation layers.** The audit layer provides
detection, not prevention.

### The model is not deployed

There is no production implementation of SynectivSec. The TLA+ model and
attack harness are research artifacts. **A deployment would require:**

- Integration with MCP, A2A, or similar agent frameworks
- A concrete policy language implementation
- A federation protocol implementation
- A production audit log

None of these exist.

---

## Method Limitations

### The prior-art analysis used AI assistance

Primary-source verification was performed with the assistance of an AI
verification process (Claude, Anthropic). The process is documented in
`docs/POSITIONING.md` §7. **The AI-assisted analysis may have missed
relevant prior art.** Independent human review before publication is
recommended.

### The OCR of the 1992 TOCS paper may contain errors

The Lampson et al. 1992 paper was obtained as PostScript and OCR'd to extract
text. **Some characters may be mangled.** The paper's speaks-for symbol (`⇒`)
and quoting operator (`|`) were rendered as various glyphs in the OCR
output. Verification against a text-native version of the paper is
recommended before publication.

### The attack harness is a demonstration, not a fuzzer

The attacks in `redteam/` demonstrate that each compatibility condition is
individually necessary. **They are not an exhaustive search** for all
possible attacks. A more systematic fuzzing approach could find additional
attacks or edge cases.

### The verification is not reproducible without the exact tool version

The TLA+ verification uses TLC 2.19 (`docs/ALGEBRA.md` §7.4). A different
TLC version could produce different state counts or — in edge cases — different
results. The Dockerfile or environment specification for reproducibility is
not included.

---

## Practical Limitations

### The state space grows exponentially

The minimal instance generates 11 million states in 17 seconds. **A larger
instance (12 principals, 4 chains, 5 domains) would generate states in the
billions.** Verifying it requires either significant compute or a symbolic
approach.

### The audit log's privacy relies on trust

The current audit design uses encrypted records and a trustworthy federation
to evaluate queries. **The federation sees everything.** A production audit
log with stronger privacy guarantees (functional encryption, PIR) is future
work.

### The federation protocol is not specified

`docs/FEDERATION.md` describes the federation model, but not the **protocol**
by which domains agree on attestation relations, propagate revocations, or
reconcile policies. **A protocol specification is future work.**

### There is no reference implementation

Everything in this repository is either specification (Markdown), formal model
(TLA+), or attack harness (Python). **There is no compiled, deployable
software.** A reference node implementation is future work.

---

## What This Project Is

**SynectivSec is a research artifact.** It states a theorem, verifies it on a
bounded instance, demonstrates the theorem's tightness, and honestly
documents what it does not prove.

**It is not:**

- A product
- A production system
- A complete standard
- A substitute for existing agent security tools

**It is a contribution to the formal foundations** of agent action
governance. It is meant to be cited, attacked, extended, and — if wrong —
corrected.

---

## How to Report a Limitation

If you find a limitation not listed here:

1. Open an issue describing the limitation
2. Include a reproduction if applicable
3. We will add it to this document

**Finding limitations is a contribution, not a criticism.** The value of this
project depends on the accuracy of its claims, including its claims about
what it does not claim.

---

*Maintained by Abhijith S ([@kakashi-kx](https://github.com/kakashi-kx), [LinkedIn](https://www.linkedin.com/in/abhixjith)).*

*Last updated: 2026-09-27*
