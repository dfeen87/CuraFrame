# CuraFrame — Constraint Reasoning

## Overview

Constraint reasoning is the core operational principle of CuraFrame.

CuraFrame does not search for “optimal” drugs, generate molecules, or automate
therapeutic decisions. Instead, it provides a structured environment in which
**design ideas are evaluated against explicit, non-negotiable constraints**.

In CuraFrame, constraints are not obstacles to creativity — they are the
conditions under which responsible creativity is allowed.

---

## Why Constraints Come First

Biological systems are coupled, nonlinear, and fragile.

Historically, many therapeutic failures arise not from lack of efficacy, but
from:
- unrecognized off-target effects
- population-specific vulnerabilities
- over-optimization of single endpoints
- implicit assumptions left unexamined

CuraFrame treats constraints as **first-class scientific objects**, ensuring
that safety, feasibility, and system stability are evaluated *before* any
discussion of benefit.

---

## Types of Constraints

CuraFrame supports multiple classes of constraints, all of which are evaluated
explicitly and independently.

### 1. Safety Constraints

Safety constraints define **hard boundaries** that must not be crossed.

Examples include:
- hERG / QT prolongation risk
- excessive bradycardia from β₁ blockade
- dangerous blood–brain barrier penetration
- known high-risk off-target receptor engagement

Safety constraints are **non-negotiable**.
A violation results in rejection, not tradeoff.

---

### 2. Pharmacokinetic Constraints

Pharmacokinetic (PK) constraints bound systemic exposure and distribution.

Examples:
- peak concentration (Cmax)
- half-life and accumulation risk
- oral bioavailability assumptions
- CNS penetration windows

PK constraints ensure that proposed concepts remain compatible with realistic
dosing and administration.

---

### 3. Pharmacodynamic Constraints

Pharmacodynamic (PD) constraints govern **target engagement behavior**.

Examples:
- required receptor occupancy ranges
- selectivity ratios (e.g., β₁ vs β₂)
- partial vs full agonism limits
- coupled domain modulation balance

These constraints prevent over-driving one domain at the expense of another.

---

### 4. Physicochemical Constraints

Physicochemical constraints act as **proxy safety and feasibility filters**.

Examples:
- molecular weight
- lipophilicity (logP)
- polar surface area (PSA)
- hydrogen bond donor / acceptor counts

These constraints help ensure compatibility with BBB penetration, metabolic
stability, and formulation feasibility.

---

## Constraint Evaluation Model

Each candidate concept is evaluated against all active constraints.

Evaluation produces:
- **Pass** — constraint satisfied
- **Violation** — constraint exceeded or unmet
- **Indeterminate** — insufficient data or uncertainty too high

Violations are not silent failures. They are recorded with:
- constraint name
- violated threshold
- observed value
- rationale
- confidence / uncertainty

This ensures that rejection is **informative**, not opaque.

---

## Population-Specific Constraint Modulation

CuraFrame recognizes that safety is **population-dependent**.

Constraints may be *modulated*, but never removed, based on population context.

Examples:
- elderly patients (reduced autonomic reserve, QT vulnerability)
- asthmatic patients (β₂ sensitivity)
- pediatric populations
- comorbid cardiac or neurological disease

Population modifiers:
- increase conservatism
- narrow allowable ranges
- strengthen selectivity requirements

All population adjustments are explicit, documented, and reversible.

---

## Constraint Violations as Scientific Signals

In CuraFrame, a constraint violation is not merely a rejection.

It is a **signal**.

Violations indicate:
- which assumptions failed
- where tradeoffs are emerging
- whether the design space itself is misaligned with reality

Repeated violations across iterations often indicate that:
- the target profile is over-ambitious
- coupled domains are in conflict
- the therapeutic concept requires reframing

---

## Directional Guidance, Not Optimization

CuraFrame may provide **directional suggestions** in response to violations.

These suggestions:
- indicate *which property* is driving risk
- suggest *directional movement* (increase / decrease)
- include a pharmacological rationale
- avoid proposing concrete molecular structures

Example guidance:
- “Reducing lipophilicity may reduce hERG affinity”
- “Increasing β₁ selectivity may mitigate bronchoconstriction risk”

CuraFrame never:
- generates molecules
- selects functional groups
- claims convergence toward a solution

Human expertise remains central.

---

## No Safe Path as a Valid Outcome

CuraFrame explicitly allows for the outcome:

> **No safe path forward identified**

This occurs when:
- constraints conflict irreconcilably
- improvements in one domain worsen another
- safety margins collapse under realistic assumptions

This outcome is considered **scientifically successful**.
It prevents wasted effort and protects downstream patients.

---

## Epistemic Humility

All constraint evaluations are bounded by uncertainty.

CuraFrame tracks:
- data provenance
- prediction source
- confidence estimates
- missing or unreliable inputs

When uncertainty is too high, CuraFrame prefers:
- indeterminate classification
- conservative rejection
- explicit acknowledgment of ignorance

Silence is treated as risk.

---

## Relationship to Optimization

CuraFrame is **not an optimizer**.

It does not:
- maximize scores
- minimize loss functions
- search for global optima

Instead, it defines:
> **Where science is allowed to operate safely**

Optimization, if used at all, must occur *outside* CuraFrame and *within*
its boundaries.

---

## Long-Term Intent

Constraint reasoning in CuraFrame is designed to:
- slow science down where it matters
- prevent harm before it becomes visible
- encode institutional memory into software
- help future scientists avoid repeating known failures

If CuraFrame helps someone decide *not* to pursue a dangerous idea, it has
already succeeded.

---

## Closing Principle

In CuraFrame, the most important output is often:

> **“This cannot be done safely under the current assumptions.”**

That statement is not a limitation.
It is the foundation of responsible science.
