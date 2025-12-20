# CuraFrame — Population Stratification

## Purpose

This document defines how **population stratification** is represented and
used within CuraFrame.

Population stratification exists to **increase safety**, not to predict
individual outcomes or replace clinical judgment. It allows CuraFrame to
apply more conservative reasoning when known vulnerabilities are present.

---

## Why Population Stratification Exists

Biological risk is not uniform across all people.

Age, comorbidities, and physiological sensitivity can substantially alter:
- tolerance to pharmacological modulation
- susceptibility to adverse effects
- safety margins for exposure and selectivity

Ignoring these differences leads to false confidence and unsafe generalization.

CuraFrame therefore supports population-aware constraint modulation as a
**protective mechanism**.

---

## Conceptual Definition

In CuraFrame, a *population* is defined as:

> A group with known, evidence-supported physiological sensitivities that
> warrant stricter safety constraints.

Population stratification does **not** attempt to model:
- individual genetics
- personal medical history
- clinical diagnoses
- demographic identity beyond physiological relevance

It is an abstraction designed to err on the side of caution.

---

## How Population Stratification Works

Population stratification in CuraFrame operates by **modifying constraints**,
never by removing them.

Specifically:
- constraint thresholds may be tightened
- selectivity requirements may be increased
- acceptable ranges may be narrowed

Constraints are never relaxed based on population context.

---

## Example Populations

Examples of populations that may require increased conservatism include:

- elderly individuals (reduced autonomic reserve, QT vulnerability)
- patients with reactive airway disease (β₂ sensitivity)
- individuals with known cardiac conduction risk
- populations with reduced metabolic clearance

These categories are illustrative, not exhaustive.

---

## Constraint Modulation Principles

All population-specific modifiers must satisfy the following principles:

### 1. Conservatism Only

Population modifiers may only **increase safety margins**.

They must not:
- widen acceptable ranges
- justify higher risk
- override baseline constraints

---

### 2. Explicitness

All modifiers must be:
- named
- documented
- traceable to a rationale

Implicit or hidden population adjustments are not allowed.

---

### 3. Reversibility

Population stratification is a **layer**, not a permanent transformation.

Base constraints must remain intact and accessible for inspection.

---

## Population Stratification Is Not Personalization

Population stratification must not be confused with personalization.

CuraFrame does **not**:
- tailor outputs to individuals
- infer patient-specific risk
- perform precision medicine

Population models exist to prevent harm, not to claim individualized insight.

---

## Ethical Use of Population Models

Population stratification must be applied with humility.

Users must avoid:
- stereotyping
- overgeneralization
- treating population categories as deterministic

Population categories are **protective approximations**, not labels.

---

## Interaction with Constraint Reasoning

Population stratification integrates directly with CuraFrame’s constraint
reasoning pipeline.

When a population context is active:
1. base constraints are loaded
2. population modifiers are applied
3. evaluation proceeds under stricter limits
4. violations are reported explicitly as population-relevant

This ensures transparency and auditability.

---

## Handling Uncertain or Overlapping Populations

When population membership is unclear or overlapping:
- the more conservative interpretation should be preferred
- uncertainty should be acknowledged explicitly
- indeterminate outcomes are acceptable

CuraFrame prioritizes safety over completeness.

---

## Limitations of Population Stratification

Population stratification in CuraFrame:
- does not capture intersectional complexity fully
- does not replace clinical risk assessment
- does not model dynamic physiological change

These limitations are intentional to avoid false precision.

---

## Scientific Rationale

Population-aware constraint tightening reflects established medical practice:
- lower dosing in vulnerable groups
- increased safety monitoring
- conservative exclusion criteria in trials

CuraFrame encodes this reasoning **upstream**, before harm can occur.

---

## Closing Principle

Population stratification exists to remind users that:

> What is safe in theory may not be safe in context.

If population-aware reasoning leads CuraFrame to reject an otherwise appealing
concept, that outcome should be considered a success.

Safety is not negotiable.

