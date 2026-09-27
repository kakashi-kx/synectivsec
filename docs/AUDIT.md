# The SynectivSec Audit Model

**Formal specification of the audit layer.**

---

## 0. Scope

This document specifies the audit layer of the SynectivSec model. It defines:

- **What is logged** — the audit record structure (§1)
- **Tamper-evidence** — Merkle-chained log design (§2)
- **Verification** — how the log is verified locally and by third parties (§3)
- **Privacy-preserving query** — searching without leaking unrelated records (§4)
- **Relation to the composition** — how audit enforcement integrates with the
  transition relation (§5)
- **What is NOT verified in the current TLA+ model** (§6)
- **Relation to prior work** (§7)
- **Open items** (§8)

The audit layer is **specified but not verified** in the current TLA+ instance.
It is part of the SynectivSec design but is orthogonal to the composition
theorem's core claim.

---

## 1. Audit Records

### 1.1 What Gets Logged

Every action transition (`ALGEBRA.md` §2.1) produces a signed **audit record**:

```
Record = ⟨
    record_id : bytes32,
    timestamp : Nat,
    principal : Principal,
    action : Action,
    domain : Domain,
    chain : DelegationChain,       — the full authority chain at action time
    policy_hash : bytes32,          — hash of the sequence policy in force
    decision : { ALLOW, DENY, ESCALATE },
    reason : bytes32,               — for DENY/ESCALATE
    prev_hash : bytes32,            — link to previous record
    signature : Signature           — signed by the audit node
⟩
```

**Every ALLOW produces a record. Every DENY produces a record. Nothing is
silent.**

### 1.2 Revocation Events

Revocation transitions (`ALGEBRA.md` §2.2) produce audit records as well:

```
RevokeRecord = ⟨
    record_id : bytes32,
    timestamp : Nat,
    revoked_principal : Principal,
    revoking_domain : Domain,
    reason : bytes32,
    prev_hash : bytes32,
    signature : Signature
⟩
```

### 1.3 Domain Events

Domain transitions (`ALGEBRA.md` §2.3) produce records:

```
DomainRecord = ⟨
    record_id : bytes32,
    timestamp : Nat,
    principal : Principal,
    from_domain : Domain,
    to_domain : Domain,
    prev_hash : bytes32,
    signature : Signature
⟩
```

### 1.4 Record Identifier

Each `record_id` is a hash of the record's content:

```
record_id = H(⟨timestamp, principal, action, domain, chain_hash,
               policy_hash, decision, reason, prev_hash⟩)
```

where `H` is a collision-resistant hash function (SHA-256 by convention, or
BLAKE3 for modern deployments).

**The record_id is deterministic given the content.** This makes the log
reproducible: given the same inputs, the same record_ids are produced.

---

## 2. Tamper-Evidence: Merkle-Chained Log

### 2.1 The Chain Structure

Records are chained by their `prev_hash` field:

```
r₀ ← r₁ ← r₂ ← … ← rₙ
```

where `rᵢ₊₁.prev_hash = rᵢ.record_id`.

**The chain is append-only.** A record cannot be modified without breaking
every subsequent `prev_hash` reference.

### 2.2 Merkle Tree over the Chain

For efficient verification of individual records, the chain is also organized
as a **Merkle tree**:

- **Leaves:** the `record_id` of each record.
- **Internal nodes:** `H(left_child || right_child)`.
- **Root:** the Merkle root, published periodically.

**A Merkle proof of a single record** is the set of sibling hashes along the
path from the leaf to the root. Its size is `O(log n)`. Verification is
`O(log n)` hash operations.

### 2.3 Publication and Anchoring

The Merkle root is periodically published — signed by the audit node — to:

- A **federation-wide log** (visible to all domains in the federation)
- An **external timestamping service** (independent of the federation)
- Optional: a **public transparency log** (e.g., Certificate Transparency
  model, RFC 6962)

**Publication establishes that the log at time t had a specific root.** Any
later modification of earlier records would produce a different root and be
detectable.

### 2.4 Split-View Resistance

The classic attack on transparency logs is **split-view**: showing different
logs to different verifiers. Mitigated by:

- **Gossip protocols** — verifiers exchange signed roots and detect divergence.
- **Cross-domain anchoring** — the federation log anchors each domain's log,
  and vice versa.
- **Public transparency logs** — the strongest mitigation, at the cost of
  public disclosure of roots (not records).

**In the current specification**, split-view resistance relies on cross-domain
anchoring and periodic public publishing of roots.

---

## 3. Verification

### 3.1 Local Verification

Given a record `r` and a Merkle root `R`, a verifier checks:

- **Inclusion proof:** `r` is a leaf of the Merkle tree with root `R`.
- **Signature:** `r.signature` is a valid signature by the audit node.
- **Chain linkage:** `r.prev_hash` matches the previous record's
  `record_id`.

**Local verification requires only `r`, the inclusion proof, and `R`.** No
access to the full log is required.

### 3.2 Third-Party Verification

An **external auditor** (regulator, compliance officer, or independent
researcher) verifies:

- **Consistency proofs:** the log at time `t₂` is a superset of the log at
  time `t₁ < t₂` (standard Merkle consistency proof).
- **Root continuity:** signed roots form a chain — each published root is
  consistent with the previous.
- **Cross-federation agreement:** the same records appear in the domain logs
  and the federation log.

**The auditor does not need to trust the org's infrastructure.** Given the
signed roots and Merkle proofs, the verification is cryptographic.

### 3.3 Tamper-Evidence Summary

| Attack | Detection |
|---|---|
| Modify a record | Breaks `prev_hash` chain; Merkle proof fails |
| Delete a record | Breaks `prev_hash` chain; inclusion proof for later records fails |
| Insert a record | Changes `record_id`; breaks Merkle tree structure |
| Forge a record | Signature verification fails |
| Rewrite history | Consistency proof against published roots fails |
| Split view | Cross-domain anchoring, gossip, or public log detects divergence |

**Every modification of the log is detectable by any verifier who has seen a
previously published root.**

---

## 4. Privacy-Preserving Query

### 4.1 The Tension

Audit logs must be:

- **Queryable** — auditors need to find specific records (e.g., all actions by
  principal `p` in domain `T` between times `t₁` and `t₂`).
- **Private** — the query should not leak information about records that are
  not returned.

**A naïve implementation** (streaming the entire log to the auditor) fails
privacy: the auditor sees everything, including records they are not
authorized to see.

### 4.2 Design: Encrypted Records with Selective Disclosure

Each record is stored in encrypted form:

```
E(r) = Enc(K_federation, r)
```

where `K_federation` is a federation-wide encryption key. The encrypted record
is what appears in the log.

**Query protocol:**

1. The auditor specifies a query `Q` (predicate over records).
2. The federation evaluates `Q` against the decrypted records.
3. Matching records are returned, with Merkle inclusion proofs.
4. Non-matching records are not disclosed.

**The auditor trusts the federation** to evaluate `Q` honestly. To reduce this
trust:

- **Auditable queries:** the query `Q` is itself recorded in the log. The
  auditor can later verify that the federation evaluated exactly what was
  requested.
- **Multiple federations:** cross-federation queries require agreement from
  multiple parties; no single party can unilaterally disclose.
- **Zero-knowledge proofs (future):** prove that `Q` was evaluated correctly
  without revealing the log content.

### 4.3 Searchable Encryption (Future Work)

Modern cryptographic techniques — searchable encryption, functional encryption,
private information retrieval — would allow querying without decrypting
everything. **These are not implemented in the current specification.**

The design is: encrypted log + trustworthy federation + auditable queries. It
is honest about the trust assumption.

---

## 5. Relation to the Composition

### 5.1 Audit as a Post-Transition Effect

Audit records are produced **after** an action, revocation, or domain
transition. They do not affect the transition's outcome:

- If the transition is allowed, an ALLOW record is produced.
- If the transition is denied, a DENY record is produced, and the transition
  did not occur.
- If the transition is escalated, an ESCALATE record is produced, and the
  action is deferred pending approval.

**Audit does not change the transition relation.** It records its outcome.

### 5.2 CI5 and Audit

The boundary determinism invariant (CI5, `ALGEBRA.md` §4.5) requires that
every action's policy is uniquely determined. **The audit record includes
`policy_hash`**, so any dispute about which policy was in force can be
resolved by inspecting the record.

**This is one of the practical benefits of the audit layer:** it makes the
composition's decisions *forensically reconstructable*.

### 5.3 Audit and the Composition Theorem

The composition theorem (`ALGEBRA.md` §6) does not depend on the audit layer.
The theorem concerns the preservation of safety invariants under composition;
audit is a separate concern.

**However**, the audit layer makes the theorem's claims *checkable* in the real
world. Without audit, you have a formal proof but no way to know whether a real
system is satisfying it. With audit, every decision is logged and verifiable.

**The audit layer is what makes the formal model operational.**

### 5.4 Relation to OAP's Signed Decision Records

**OAP (arXiv 2603.20953, 2026)** produces a signed decision record for every
tool-call authorization decision. The SynectivSec audit layer is the same
idea at a broader scope:

- OAP: single-action authorization records.
- SynectivSec: records that include the authority chain, domain, policy hash,
  and cross-domain context.

**The composition adds context.** The audit is not just "action X was allowed"
but "action X was allowed under chain C, in domain T, with policy P, with
revocation state r."

---

## 6. What Is NOT Verified in the Current TLA+ Model

**The audit layer is specified but not verified.** The TLA+ model
(`tla/Composition.tla`) does not include:

- Audit record production
- Merkle chaining
- Merkle proof verification
- Consistency proofs
- Signature verification
- Query evaluation
- Privacy guarantees

**This is a limitation, not a contradiction.** The composition theorem is about
the enforcement of safety invariants; audit is a separate layer that records
enforcement decisions. The theorem holds whether or not audit is present.

**Extending the TLA+ model to include audit is future work.** The audit layer's
correctness properties (tamper-evidence, inclusion proof correctness,
consistency) are well-studied and can be verified separately.

---

## 7. Relation to Prior Work

### 7.1 Transparency Logs

**Certificate Transparency (RFC 6962)** — the standard model for append-only
Merkle logs with public roots. SynectivSec's audit log follows the same design.

**Merkle trees** — Ralph Merkle, "A Digital Signature Based on a Conventional
Encryption Function," CRYPTO '87. The foundational structure for tamper-evident
logs.

**Merkle consistency proofs** — Crosby & Wallach, "Efficient Data Structures
for Tamper-Evident Logging," USENIX Security 2009. Formalizes the proof
protocols used by Certificate Transparency and SynectivSec.

### 7.2 Signed Decision Records

**OAP (arXiv 2603.20953, 2026)** — Open Agent Passport. Produces signed
per-decision records for tool-call authorization. SynectivSec's audit layer
extends this idea with chain, domain, and policy context.

**Sigstore / Rekor** — transparency logs for software supply chain. Same
principles.

**Ledger / blockchain** — append-only logs with consensus. Overkill for a
single-org audit log, but related.

### 7.3 Privacy-Preserving Audit

**Confidential Computing** — Trusted Execution Environments (TEEs) for
audit-log evaluation. Complements the encrypted-log design in §4.2.

**Functional Encryption** — allows evaluating queries without decrypting.
Theoretically relevant; practical implementations are limited.

**Private Information Retrieval (PIR)** — allows querying without revealing the
query. Theoretically relevant; practical implementations are limited.

**SynectivSec's current design is deliberately simple:** encrypted log +
trustworthy federation + auditable queries. This is honest about the trust
assumption and provides a basis for future extension.

### 7.4 What Is Novel

**The audit layer itself is not novel.** Merkle-chained logs, Certificate
Transparency, and signed decision records are all established.

**What is novel is the integration with the composition:**

- Audit records that include the **full authority chain** at action time.
- Audit records that include the **policy hash**, making CI5's boundary
  determinism verifiable.
- Audit records that include **cross-domain context**, making CBAT and RS
  decisions checkable.
- Audit as the operational counterpart to the formal theorem.

**The audit layer is the piece that makes the formal model deployable.**

---

## 8. Open Items

1. **Formal verification of the audit layer.** The audit layer's correctness
   properties (tamper-evidence, inclusion proof validity, consistency proof
   validity) are specified here and are well-studied, but not formally verified
   in this project. A separate TLA+ or Coq verification is future work.

2. **Query protocol specification.** The query protocol (§4.2) is described
   informally. A full specification — including the message formats, the
   auditable-query logging, and the federation's obligations — is future work.

3. **Privacy guarantees.** The current design relies on the federation to
   evaluate queries honestly. Formal privacy guarantees (zero-knowledge,
   functional encryption) are future work.

4. **Scale.** Merkle proofs scale to billions of records. But the query protocol
   has not been stress-tested at scale. A performance evaluation is future
   work.

5. **Cross-federation audit.** When two federations interact, their audit logs
   must be reconciled. The protocol for this is future work.

6. **Deletion and retention.** Real audit logs have retention policies. A
   record may be deleted after 90 days, 7 years, or never. The Merkle chain
   must survive retention policy changes — a "deletion" must be a marked
   logical event, not an actual removal. Formalizing this is future work.

7. **Root key rotation and audit.** The audit log's Merkle root is signed by a
   key. Rotating that key requires preserving the log's integrity across
   rotations. Same problem as the federation root key rotation (FEDERATION.md
   §7 open item 5).

---

## 9. Formal Summary

| Element | Definition |
|---|---|
| Audit record | `⟨record_id, timestamp, principal, action, domain, chain, policy_hash, decision, reason, prev_hash, signature⟩` |
| Record ID | `H(⟨…⟩)` — hash of record content |
| Chain | `rᵢ₊₁.prev_hash = rᵢ.record_id` |
| Merkle root | `H(…H(H(r₀.record_id || r₁.record_id) || …))` |
| Inclusion proof | `O(log n)` sibling hashes proving a record is in the tree |
| Consistency proof | `O(log n)` proof that one root is a prefix of another |
| Verification | Merkle proof + signature + prev_hash check |
| Query protocol | Encrypted log + federation evaluation + auditable queries |

**The audit layer is specified, not verified.** It provides the operational
counterpart to the composition theorem: every decision is logged, tamper-
evident, and externally verifiable.

---

*Last updated: 2026-09-27*
