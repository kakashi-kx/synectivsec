# Contributing to SynectivSec

Thank you for your interest. This document explains what kinds of
contributions are welcome and how to make them.

---

## Before You Contribute

**Read these first:**

1. `docs/POSITIONING.md` — what is novel, what is not, and the prior art
2. `docs/ALGEBRA.md` — the formal model
3. `LIMITATIONS.md` — what doesn't work yet

The most useful contribution you can make is **breaking the model**. If you
find a way to violate an invariant that the theorem claims should hold, that
is a genuine contribution.

---

## What We Welcome

### 1. Attacks

**This is the most valuable contribution.** A working attack against:

- The composition theorem
- The TLA+ model (`tla/Composition.tla`)
- The attack harness (`redteam/`)
- The federation model
- The audit model

**How to submit:** Open an issue in the `redteam/` directory with a runnable
reproduction. Include:

- The invariant you claim is violated
- A minimal reproduction (TLA+ trace, Python script, or PoC)
- The expected vs. actual behavior

**If your attack succeeds, we will:**

- Acknowledge it in `redteam/RESULTS.md`
- Update the theorem if necessary
- Cite your contribution in the paper

### 2. Verification Extensions

- **Larger TLA+ instances** — more principals, more chains, more domains
- **Proof-assistant formalization** — Lean, Coq, or Isabelle translation of
  the composition theorem
- **Unbounded verification** — inductive or symbolic proof that the theorem
  holds generally, not just on bounded instances

### 3. Prior Art

- **Primary-source verification** of any claim in `docs/POSITIONING.md` or
  `docs/FEDERATION.md`
- **Additional prior art** that weakens a novelty claim — this is welcome,
  not unwelcome
- **Corrections** to any citation

### 4. Specification Improvements

- **Clarifications** in the spec documents
- **Typos and corrections**
- **Additional examples** that illuminate a concept

### 5. Case Studies

- **Real-world agent deployments** where the composition theorem applies
- **Tooling** that integrates with existing agent frameworks (MCP, A2A, etc.)

---

## What We Do Not Welcome

- **Claims without reproduction** — "I think this attack works" without a
  runnable PoC
- **Novelty claims without prior-art search** — asserting something is new
  without checking
- **PRs that weaken invariants** — if your change makes an invariant easier
  to violate, explain why it's still correct
- **Promotional content** — linking to commercial products without
  justification

---

## Contribution Process

### For Small Changes (typos, clarifications, examples)

1. Fork the repository
2. Make the change
3. Open a PR with a brief description

### For Substantial Changes (new attacks, verification extensions, spec changes)

1. Open an issue first, describing the proposed change
2. Wait for discussion
3. Fork, implement, and open a PR referencing the issue

### For Attacks

1. Open an issue in `redteam/` with a runnable reproduction
2. If the attack succeeds, we will coordinate disclosure and acknowledgment

---

## The Invariants Are Load-Bearing

The composition theorem depends on the exact statements of:

- **CI1–CI5** (invariants) in `docs/ALGEBRA.md` §4
- **PC, RS, CBAT** (compatibility conditions) in `docs/ALGEBRA.md` §5
- **The transition relation** in `docs/ALGEBRA.md` §2

**Do not modify these definitions in a PR without discussion.** A small change
to a condition can invalidate the theorem. If you believe a definition is
wrong, open an issue first.

---

## Style Guidelines

### For documentation

- Use **Markdown** with `##` for sections, `###` for subsections
- Code blocks use triple backticks with language (`tla`, `python`, `bash`)
- Math uses Unicode symbols (`∀`, `∃`, `∧`, `∨`, `⟹`) — no LaTeX in .md files
- Cite primary sources with section or page numbers where applicable

### For TLA+

- Each module starts with `---- MODULE <Name> ----` and ends with `====`
- Constants are declared on one line
- Operators are defined before use
- Invariants cite the attacks they defend against in comments

### For Python (attack harness)

- Python 3.10+
- Standard library only (no external dependencies)
- Each script exits `0` if the attack succeeds, `1` if it fails, `2` on error
- Output goes to stdout with a `[PREFIX]` line

---

## Licensing

By contributing, you agree that your contributions will be licensed under:

- **Apache License 2.0** for code (`tla/`, `redteam/`)
- **Creative Commons Attribution 4.0** for documentation (`docs/`, `README.md`)

See `LICENSE` and `LICENSE-spec`.

---

## Questions

Open an issue. If you're unsure whether a contribution is welcome, ask first.

---

*Maintained by Abhijith S ([@kakashi-kx] [@kakashi4kx]  (https://github.com/kakashi-kx), [LinkedIn](https://www.linkedin.com/in/abhixjith)).*

*Last updated: 2026-09-27*
