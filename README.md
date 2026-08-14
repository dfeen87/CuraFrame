# CuraFrame: Constraint-Driven Therapeutic Design Reasoning

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/dfeen87/CuraFrame/actions/workflows/ci.yml/badge.svg)](https://github.com/dfeen87/CuraFrame/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)

## Table of Contents
- [Abstract](#abstract)
- [Overview](#overview)
- [Key Features](#key-features)
- [Repository Structure](#repository-structure)
- [Theoretical Foundation](#theoretical-foundation)
- [Installation](#installation)
- [Usage](#usage)
- [Advanced Example: CardiAnx-1 Dual-Domain Evaluation](#advanced-example-cardianx-1-dual-domain-evaluation)
- [Use Cases](#use-cases)
- [Testing and Validation](#testing-and-validation)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)
- [Citation and Attribution](#citation-and-attribution)
- [Related Work and Scientific Context](#related-work-and-scientific-context)
- [Design Philosophy Summary](#design-philosophy-summary)
- [Concluding Remarks](#concluding-remarks)
- [Acknowledgments](#acknowledgments)

---

## Abstract

CuraFrame is a transparent, safety-first computational framework for constraint-based evaluation of hypothetical therapeutic candidates. Grounded in principles of medicinal chemistry, pharmacology, and safety pharmacology, CuraFrame provides a systematic approach to assess whether proposed molecular designs satisfy established pharmacokinetic (PK), pharmacodynamic (PD), and safety criteria before advancing to experimental validation.

Unlike generative drug discovery systems, CuraFrame operates as a **falsification engine**: it evaluates designs against explicit, evidence-based constraints and produces auditable rejection criteria when safety or feasibility boundaries are violated. The framework is designed to support rigorous scientific reasoning, hypothesis refinement, and risk assessment in early-stage therapeutic design—not to automate discovery or make clinical recommendations.

**Core Principle**: CuraFrame helps scientists identify **where and why designs fail** under current pharmacological understanding, making unsafe or infeasible concepts fail early, clearly, and transparently.

---

## Overview

### What CuraFrame Is

CuraFrame is a **scientific reasoning framework** designed to:

1. **Encode Pharmacological Knowledge**: Represent established PK/PD principles, ADMET (Absorption, Distribution, Metabolism, Excretion, Toxicity) criteria, and safety margins as formal computational constraints.

2. **Enable Systematic Evaluation**: Assess hypothetical therapeutic candidates against multi-dimensional constraint sets derived from medicinal chemistry, cardiology, neuropharmacology, and population-specific risk factors.

3. **Support Transparent Decision-Making**: Provide auditable, reproducible evaluations with explicit provenance for each constraint, including literature references, regulatory guidance, and domain expertise.

4. **Facilitate Risk Stratification**: Allow conservative constraint tightening for vulnerable populations (e.g., elderly, pediatric, asthmatics, comorbid patients) to make safety assumptions explicit rather than implicit.

5. **Promote Scientific Rigor**: Treat constraint violations as informative outcomes that guide hypothesis refinement rather than dead ends.

**Scope of Application**: CuraFrame evaluates constraints derived from:
- Lipinski's Rule of Five and medicinal chemistry heuristics
- hERG channel inhibition and QTc prolongation risk
- Blood-brain barrier (BBB) penetration criteria
- Receptor selectivity profiles (e.g., β₁/β₂, 5-HT₁ₐ/5-HT₂ₐ)
- Pharmacokinetic parameters (half-life, bioavailability, clearance)
- Population-stratified safety margins

---

### What CuraFrame Is NOT

CuraFrame explicitly **does not**:

- **Generate molecular structures** (no de novo design or scaffold hopping)
- **Optimize properties** (no gradient-based or evolutionary algorithms)
- **Train predictive models** (no machine learning or statistical inference)
- **Make clinical recommendations** (no patient-specific treatment guidance)
- **Replace domain expertise** (operates under supervision of medicinal chemists and pharmacologists)
- **Claim therapeutic efficacy** (evaluates constraints only, not biological outcomes)

**Intentional Limitations**: CuraFrame is a **falsification tool**, not a discovery engine. A design that satisfies all constraints is "not yet rejected"—not "validated" or "optimal." Experimental validation remains the gold standard.

> **Design Philosophy**: In CuraFrame, the answer *"this cannot be done safely under current assumptions"* is considered a **successful scientific outcome**. Rejection is informative and prevents resource investment in fundamentally flawed designs.

---

## Key Features

### 1. Constraint-as-Object Formalism
Each constraint is a first-class computational object with structured metadata:
- **Threshold**: Quantitative limit (e.g., logP ≤ 5.0, hERG IC₅₀ ≥ 10 μM)
- **Comparator**: Evaluation semantics (≤, ≥, range, etc.)
- **Rationale**: Scientific justification (e.g., "Lipinski's Rule of Five for oral bioavailability")
- **Severity**: Impact classification (CRITICAL, SEVERE, WARNING)
- **Provenance**: Data source (literature, regulatory guidance, expert consensus)
- **Confidence**: Epistemic uncertainty acknowledgment

### 2. Population Stratification
Constraints are not universal constants. CuraFrame supports **conservative tightening** for high-risk populations:
- **Elderly patients**: Reduced metabolic clearance, increased fall risk (e.g., CNS sedation thresholds)
- **Pediatric populations**: Developing physiology, altered PK/PD relationships
- **Asthmatics**: Absolute contraindication for β₂-antagonism (requires 200× β₁/β₂ selectivity)
- **Cardiac comorbidities**: Tightened QTc prolongation margins

This stratification makes assumptions **auditable and falsifiable** rather than hidden in implicit model biases.

### 3. Auditable Evaluation Pipeline
Every evaluation produces:
- **Violation report**: Which constraints failed, observed vs. required values
- **Severity classification**: Prioritization for design revision
- **Traceability**: Full provenance chain for each constraint
- **Reproducibility**: Deterministic evaluation with versioned constraint sets

### 4. Multi-Domain Constraint Bundles
Pre-validated constraint sets for common therapeutic domains:
- **Core Safety**: Universal ADMET and hERG/QTc criteria
- **CNS Drugs**: BBB penetration, P-glycoprotein efflux, receptor selectivity
- **Cardiology**: β-blocker selectivity, cardiac ion channel safety
- **CardiAnx-1**: Dual-domain β₁-blocker / 5-HT₁ₐ hybrid for heart-brain comorbidity

### 5. Pure Python Implementation
Zero external dependencies in the core engine ensures:
- Reproducibility across environments
- Integration into CI/CD pipelines
- Long-term maintainability
- Transparent inspection and validation

---

## Repository Structure
```
CuraFrame/
├── cura_frame/                   # Core reasoning engine (library)
│   ├── core.py                   # Constraint evaluation engine
│   ├── constraints_library.py    # Canonical constraint definitions
│   ├── bundles.py                # Bundle registry helpers
│   ├── comparators.py            # Comparator semantics
│   ├── db.py                     # SQLite-backed auth/user helpers
│   └── cli.py                    # Command-line interface
├── apps/                         # Application interfaces
│   ├── console_streamlit/        # Streamlit interactive console
│   │   ├── app.py
│   │   └── db_auth.py
│   └── web/                      # FastAPI web application
│       ├── main.py
│       ├── api/
│       ├── core/
│       ├── db/
│       └── templates/
├── constraints/                  # Domain constraint datasets (JSON)
│   ├── anti_infective/
│   ├── cardiac/
│   ├── cns/
│   ├── formulation/
│   ├── hepatic/
│   ├── immunologic/
│   ├── metabolic/
│   ├── oncology/
│   ├── pkpd/
│   ├── renal/
│   ├── safety/
│   └── systemic_exposure/
├── simulations/candidates/       # Example candidate payloads
├── pipelayer/                    # Sideboom pipelayer governance domain
├── constraint_core/              # C++ constraint core headers
├── scoring/                      # C++ scoring engine components
├── docs/                         # Philosophical + technical documentation
├── tests/                        # Unit/integration test suite
├── CMakeLists.txt                # C++ build configuration
├── launch_console.py             # Root-level Streamlit launcher
├── render.yaml                   # Render deployment configuration
├── requirements.txt              # Python dependencies
├── pyproject.toml                # Python build metadata
├── setup.py                      # Package setup script
├── pytest.ini                    # Test configuration
├── CITATION.cff                  # Software citation metadata
├── README.md                     # This file
└── LICENSE                       # MIT License
```

### Architectural Intent

- **`cura_frame/`** is the engine  
  It contains no UI code and no external tooling assumptions.

- **`apps/`** is the presentation layer  
  It contains both the Streamlit interactive console (`console_streamlit/`) and the FastAPI web application (`web/`). Neither influences core reasoning.

- **`pipelayer/`** is a separate governance domain  
  It demonstrates CuraFrame's AILEE trust pipeline applied to heavy machinery (sideboom pipelayer) safety decisions.

- **`docs/`** are constitutional  
  They define scope, ethics, limits, and philosophy.

- **Root scripts** are launchers, not libraries.

---

## Theoretical Foundation

### Constraint-Based Reasoning in Drug Design

Traditional drug discovery often employs optimization-driven approaches (e.g., quantitative structure-activity relationship [QSAR] models, deep generative networks) that maximize predicted activity while implicitly encoding safety and feasibility as soft penalties. This can lead to designs that score well mathematically but violate fundamental pharmacological principles.

CuraFrame inverts this paradigm by implementing **constraint satisfaction** rather than objective optimization:

1. **Hard Constraints**: Safety and feasibility criteria are treated as non-negotiable boundaries, not tunable parameters.
2. **Falsification Logic**: Designs are systematically tested for violations; a single critical violation rejects the candidate.
3. **Epistemic Honesty**: Constraint provenance and confidence are explicit; uncertainty is documented, not hidden.

This approach aligns with **Popperian falsificationism** in scientific methodology: hypotheses (designs) are subjected to rigorous tests (constraints), and failure to reject constitutes provisional acceptance—not proof of efficacy.

### Population-Specific Risk Modeling

Pharmacological constraints exhibit significant inter-population variability due to:
- **Genetic polymorphisms**: CYP enzyme activity, receptor density
- **Physiological factors**: Age-related metabolic decline, organ function
- **Disease-state modulation**: Cardiac conduction in heart failure, BBB integrity in neuroinflammation

CuraFrame addresses this by allowing **conservative constraint adjustment** for vulnerable populations. For example:
- **Asthmatic patients**: β₁/β₂ selectivity threshold increased from 100× to 200× to minimize β₂-antagonism risk
- **Elderly**: QTc prolongation margins tightened by 20% due to reduced repolarization reserve

This stratification is **declarative and auditable**, enabling researchers to explicitly state assumptions about population-specific safety margins.

### Rejection as Informative Outcome

In CuraFrame, constraint violation is not a failure of the framework—it is a **successful scientific outcome**. A rejection provides:

- **Diagnostic information**: Which pharmacological principles are violated
- **Quantitative gaps**: Magnitude of deviation from acceptable limits
- **Design guidance**: Prioritized list of properties requiring modification
- **Epistemic insight**: Confidence intervals on constraint thresholds

This transforms constraint evaluation from a binary pass/fail into a **structured hypothesis refinement process**.

---

## Installation

### System Requirements

- **Python**: 3.9 or higher
- **Operating System**: Platform-independent (Linux, macOS, Windows)
- **Dependencies**: None (core engine is pure Python)

### Installation from Source

```bash
# Clone the repository
git clone https://github.com/dfeen87/CuraFrame.git
cd CuraFrame

# Install in development mode
pip install -e .
```

### Optional Dependencies

Install all application dependencies (Streamlit console, FastAPI web app) at once:
```bash
pip install -r requirements.txt
```

Or selectively:
```bash
# For the interactive Streamlit console
pip install streamlit

# For the FastAPI web application
pip install fastapi uvicorn[standard] jinja2 python-multipart
```

For development and testing:
```bash
pip install pytest
```

### Verification

Verify installation by running the test suite:
```bash
pytest tests/
```

---

## Usage

### Quick Start: Core Library

The following example demonstrates basic constraint evaluation:

```python
from cura_frame import CuraFrame, Candidate
from cura_frame.constraints_library import core_safety_constraints

# Initialize framework with safety constraint bundle
framework = CuraFrame(
    core_safety_constraints(),
    name="SafetyEvaluator"
)

# Define a hypothetical therapeutic candidate
candidate = Candidate(
    name="test_compound_001",
    properties={
        "logP": 3.5,              # Lipophilicity
        "hERG_IC50": 15.0,        # μM (cardiac safety)
        "beta1_selectivity": 120.0  # β₁/β₂ selectivity ratio
    }
)

# Evaluate against constraints
result = framework.evaluate(candidate)

# Interpret results
if result.is_accepted():
    print("✓ Candidate satisfies all constraints")
else:
    print("✗ Constraint violations detected:")
    for violation in result.violations:
        print(f"  [{violation.severity}] {violation.constraint}")
        print(f"    Observed: {violation.observed}")
        print(f"    Required: {violation.threshold}")
        print(f"    Rationale: {violation.rationale}\n")
```

**Output Interpretation**:
- `is_accepted()`: Returns `True` if all critical and severe constraints are satisfied
- `violations`: List of `Violation` objects with diagnostic information
- Each violation includes severity classification, observed vs. required values, and scientific rationale

---

### Command-Line Interface (CLI)

For integration into automated pipelines, CI/CD workflows, or batch processing:

```bash
# Evaluate a candidate from JSON file
python -m cura_frame.cli candidate.json --bundle core-safety

# Use different constraint bundles
python -m cura_frame.cli candidate.json --bundle cns
python -m cura_frame.cli candidate.json --bundle cardiology

# Machine-readable output for parsing
python -m cura_frame.cli candidate.json --bundle core-safety --format json
```

**Candidate JSON Structure**:
```json
{
  "name": "example_candidate_001",
  "properties": {
    "logP": 3.2,
    "molecular_weight": 425.0,
    "hERG_IC50": 12.0,
    "beta1_selectivity": 140.0
  }
}
```

**Available Constraint Bundles**:
```bash
# List all available bundles
python -m cura_frame.cli --list-bundles
```

Output:
- `core-safety`: Universal ADMET and cardiac safety
- `lipinski`: Rule of Five for oral bioavailability
- `cns`: BBB penetration and CNS-specific constraints
- `cardiology`: β-blocker selectivity and cardiovascular safety
- `cardianx`: Dual-domain β₁/5-HT₁ₐ hybrid constraints

---

### Using the Streamlit Console

Launch the interactive console:
```bash
# Recommended
python launch_console.py

# Or directly
streamlit run apps/console_streamlit/app.py
```

The console allows you to:

- Select constraint bundles (Core Safety, CNS, Cardiology, CardiAnx-1, etc.)
- Define hypothetical candidates via JSON or a form-based calculator
- Apply population modifiers
- View detailed violations and warnings
- Export results and constraint metadata

---

### Using the FastAPI Web Application

CuraFrame also ships a full web application (`apps/web/`) built with FastAPI. It includes user registration, login, a dashboard, and an interactive constraint calculator.

Run it locally:
```bash
uvicorn apps.web.main:app --host 0.0.0.0 --port 8000
```

Or deploy to Render.com using the included `render.yaml`:

**Render.com deployment with managed database**

CuraFrame stores users and evaluation logs in a managed PostgreSQL database. The included `render.yaml` provisions all services automatically — here is what it configures and how to deploy:

1. **Connect your repo to Render.com**
   - Go to [render.com](https://render.com), sign in, and click **New → Blueprint**.
   - Select the CuraFrame repository. Render will detect `render.yaml` and provision the services automatically.

2. **What `render.yaml` configures**
   - A **managed PostgreSQL database** (`curaframe-db`) on Render's free database plan (PostgreSQL 18).
   - A **web service** (`curaframe-web`) on the **Starter plan**, with `DATABASE_URL` injected automatically from the managed database.
   - `CURAFRAME_SECURE_COOKIES=1` — marks session cookies as `Secure` (required for HTTPS on Render).
   - A second **web service** (`curaframe-console`) running the Streamlit console on the free plan, also connected to the database.

3. **Required secret (set manually in Render dashboard)**
   - `JWT_SECRET` — a cryptographically random secret used to sign authentication tokens. Generate one with:
     ```bash
     python -c "import secrets; print(secrets.token_hex(32))"
     ```
     Add it as an environment variable on the `curaframe-web` service before the first deploy.

4. **Manual setup (if you prefer not to use the Blueprint)**
   - Create a **Web Service** with environment `Python`, build command `pip install -r requirements.txt && pip install -e .`, and start command `uvicorn apps.web.main:app --host 0.0.0.0 --port $PORT`.
   - Create a **PostgreSQL** database on Render and link it to the web service via `DATABASE_URL`.
   - Add environment variables `CURAFRAME_SECURE_COOKIES=1` and `JWT_SECRET` (see above).

The database tables (`users`, `logs`, `form_submissions`) are created automatically on first startup — no manual schema migration is required.

Routes:
- `GET /` → redirects to `/dashboard` (authenticated) or `/login`
- `GET/POST /register` → user registration
- `GET/POST /login` → authentication
- `GET /dashboard` → evaluation dashboard (requires login)
- `GET/POST /calculator` → constraint calculator (requires login)
- `GET /logout` → session logout

---

### Pipelayer Domain Module

The `pipelayer/` package demonstrates the AILEE trust pipeline applied to a completely different safety-critical domain: **sideboom pipelayer machines** used in pipeline construction.

`PipelayerGovernor` evaluates machine telemetry (tipping moments, hydraulic pressure, engine temperature), environmental conditions (wind speed, ground slope, soil stability), and operator fatigue to produce governance decisions (`PROCEED_NORMAL`, `WARN_OPERATOR`, `HALT_IMMEDIATELY`, etc.).

```python
from pipelayer.pipelayer import PipelayerGovernor, PipelayerSignals, MachineTelemetry, SiteConditions, OperationMode

governor = PipelayerGovernor()
signals = PipelayerSignals(
    operation_trust_score=0.90,
    measurement_reliability=0.85,
    machine_telemetry=MachineTelemetry(
        load_kg=18000, boom_angle_deg=45, counterweight_position_pct=60,
        engine_rpm=1800, engine_temp_c=85, hydraulic_pressure_bar=200,
        tipping_moment_pct=70, load_moment_pct=80,
    ),
    site_conditions=SiteConditions(
        wind_speed_kmh=20, ambient_temp_c=15, visibility_m=1000,
        ground_slope_pitch_deg=5, ground_slope_roll_deg=3,
        soil_stability_index=0.8,
    ),
    operation_mode=OperationMode.LIFTING,
)
result = governor.evaluate(signals)
print(result.decision_outcome)  # e.g. PROCEED_NORMAL
```

This module is self-contained and does not depend on `cura_frame`. See `pipelayer/test_pipelayer_usage.py` for usage examples.

---

## Advanced Example: CardiAnx-1 Dual-Domain Evaluation

### Scientific Context

CardiAnx-1 represents a conceptual dual-domain therapeutic targeting the heart-brain axis in comorbid anxiety-cardiovascular disease (Krüger & Feeney, 2025). The design hypothesis combines:

1. **β₁-selective adrenergic blockade**: Reduces heart rate and myocardial oxygen demand without bronchoconstriction
2. **5-HT₁ₐ partial agonism**: Anxiolytic effects via serotonergic modulation in prefrontal cortex and amygdala

**Pharmacological Challenges**:
- Maintaining β₁/β₂ selectivity >100× to avoid respiratory complications
- Achieving 5-HT₁ₐ affinity <20 nM while avoiding 5-HT₂ₐ and D₂ cross-reactivity
- Balancing lipophilicity for BBB penetration without excessive CNS side effects
- Ensuring acceptable oral bioavailability and half-life

### CuraFrame Evaluation

```python
from cura_frame import CuraFrame, Candidate
from cura_frame.constraints_library import cardiAnx_dual_domain_constraints

# Initialize dual-domain constraint framework
framework = CuraFrame(
    cardiAnx_dual_domain_constraints(),
    name="CardiAnx-1_Evaluator"
)

# Define population-specific safety margins
framework.add_population("asthmatic", {
    # Require 200× β₁/β₂ selectivity (2× safety factor)
    "beta1_selectivity": lambda c: c.threshold * 2.0
})

# Hypothetical candidate properties
candidate = Candidate(
    name="CardiAnx-A1",
    properties={
        # ADMET properties
        "logP": 3.2,                      # BBB-compatible lipophilicity
        "polar_surface_area": 75.0,      # Å² (within CNS range)
        "molecular_weight": 485.0,       # g/mol
        
        # Cardiac safety
        "hERG_IC50": 15.0,               # μM (>30× therapeutic margin)
        
        # β-adrenergic selectivity
        "beta1_selectivity": 170.0,      # β₁/β₂ ratio
        
        # Serotonergic profile
        "Kd_5HT1A": 12.0,                # nM (target: <20 nM)
        "Kd_5HT2A": 650.0,               # nM (off-target avoidance)
        "Kd_D2": 1200.0,                 # nM (antipsychotic liability)
        
        # Pharmacokinetics
        "plasma_half_life": 12.0         # hours (QD dosing)
    }
)

# Evaluate for general population
result_general = framework.evaluate(candidate)

# Evaluate for asthmatic population
result_asthmatic = framework.evaluate(candidate, population="asthmatic")

# Compare population-stratified outcomes
print("=== General Population ===")
print(result_general.summary())

print("\n=== Asthmatic Population ===")
print(result_asthmatic.summary())

if not result_asthmatic.is_accepted():
    print("\n⚠ REJECTED for asthmatic population:")
    for violation in result_asthmatic.violations:
        if "selectivity" in violation.constraint.lower():
            print(f"  β₁/β₂ selectivity: {violation.observed}× (required: {violation.threshold}×)")
            print(f"  Rationale: {violation.rationale}")
```

**Expected Outcome**: This candidate is **rejected** for asthmatic patients due to insufficient β₁/β₂ selectivity (170× vs. 200× required), demonstrating how population stratification prevents unsafe designs from advancing.

---

## Use Cases

### 1. Early-Stage Hypothesis Validation

**Scenario**: A medicinal chemist proposes a novel β-blocker scaffold with enhanced β₁ selectivity.

**CuraFrame Application**:
- Evaluate predicted molecular properties against `cardiology_oriented_constraints()`
- Identify which ADMET or safety criteria are violated before synthesis
- Prioritize property optimization targets (e.g., reduce logP for oral bioavailability)

**Outcome**: Prevent resource investment in fundamentally flawed designs; guide synthetic chemistry toward viable parameter space.

---

### 2. Multi-Target Drug Design Assessment

**Scenario**: Researchers explore a dual-mechanism drug targeting serotonergic and dopaminergic systems.

**CuraFrame Application**:
- Apply `cns_drug_constraints()` to ensure BBB penetration
- Use `off_target_5ht2a_avoidance()` and `dopamine_d2_avoidance()` to check receptor selectivity
- Evaluate population-stratified safety for elderly patients (reduced metabolic clearance)

**Outcome**: Systematic identification of polypharmacology risks; transparent documentation of selectivity assumptions.

---

### 3. Regulatory Pre-Assessment

**Scenario**: A biotech company prepares IND (Investigational New Drug) application documentation.

**CuraFrame Application**:
- Evaluate candidate against FDA/ICH safety criteria (hERG inhibition, QTc prolongation)
- Generate auditable constraint violation reports for safety pharmacology section
- Document population-specific safety margins for vulnerable groups

**Outcome**: Proactive identification of regulatory red flags; transparent safety argumentation.

---

### 4. Educational Tool for Pharmacology Training

**Scenario**: Graduate students learn structure-activity relationships in medicinal chemistry course.

**CuraFrame Application**:
- Explore how molecular property changes (logP, MW, PSA) affect constraint satisfaction
- Visualize trade-offs between CNS penetration and peripheral safety
- Understand population stratification principles through concrete examples

**Outcome**: Hands-on learning of pharmacological reasoning with immediate feedback.

---

### 5. Literature-Driven Constraint Validation

**Scenario**: A researcher questions whether published β₁/β₂ selectivity thresholds are appropriate for asthmatics.

**CuraFrame Application**:
- Adjust `beta1_selectivity` constraint threshold based on new literature
- Re-evaluate historical candidates to assess impact of threshold change
- Document provenance and confidence for updated constraint

**Outcome**: Systematic integration of new evidence; reproducible constraint evolution.

---

### 6. Automated CI/CD Safety Checks

**Scenario**: A computational chemistry team uses automated workflows to screen virtual libraries.

**CuraFrame Application**:
- Integrate `python -m cura_frame.cli` into CI pipeline
- Reject designs violating core safety constraints before expensive docking/MD simulations
- Generate machine-readable JSON reports for downstream analysis

**Outcome**: Computational efficiency gains by early filtering; automated safety enforcement.

---

## Testing and Validation

### Unit Testing

CuraFrame employs comprehensive unit tests to ensure constraint evaluation correctness:

```bash
# Run all tests
pytest tests/

# Run with coverage report
pytest tests/ --cov=cura_frame --cov-report=term-missing

# Run specific test modules
pytest tests/test_core.py -v
```

**Test Coverage Areas**:
- **Constraint semantics**: Verification of comparator logic (≤, ≥, range, exact match)
- **Population stratification**: Correctness of constraint modification for different populations
- **Error handling**: Graceful handling of missing properties, invalid inputs
- **Auditability**: Provenance tracking and violation reporting
- **Reproducibility**: Deterministic evaluation across repeated runs
- **Edge cases**: Boundary conditions, extreme values, null handling

### Continuous Integration

CuraFrame's CI pipeline focuses on **tooling reliability**, not scientific validation:

**CI Scope** (what is tested):
- Installation in clean Python environments (3.9, 3.10, 3.11)
- Unit test suite execution (100% pass rate required)
- CLI entrypoint functionality in headless environments
- Package metadata integrity

**CI Limitations** (what is NOT tested):
- Scientific correctness of constraint thresholds (requires domain expertise)
- Computational performance benchmarks (not a design goal)
- External tool integrations (cheminformatics libraries, etc.)
- Therapeutic outcome predictions (outside scope)

> **Rationale**: CI ensures CuraFrame is a **reliable tool** that can be integrated into research workflows. It does not certify the medical or scientific validity of constraint definitions, which require ongoing literature review and expert consensus.

---

## Documentation

### Essential Reading

The following documents are **constitutional** to CuraFrame's design and must be consulted before extending or deploying the framework:

| Document | Purpose | Key Topics |
|----------|---------|------------|
| **`PHILOSOPHY.md`** | Foundational design principles | Safety-first reasoning, epistemic honesty, rejection as success |
| **`CONSTRAINT_REASONING.md`** | Technical implementation details | Constraint semantics, comparator logic, evaluation pipeline |
| **`POPULATION_STRATIFICATION.md`** | Population-specific safety modeling | Age, comorbidity, genetic polymorphisms, conservative adjustment |
| **`LIMITATIONS.md`** | Explicit scope boundaries | What CuraFrame cannot and will not do |
| **`ETHICAL_USE.md`** | Usage constraints and misuse prevention | Prohibited applications, responsible deployment |
| **`INSPIRATION.md`** | Scientific origins and motivating examples | CardiAnx-1 case study, dual-domain therapeutics |

### Core Philosophical Tenets

From `PHILOSOPHY.md`:

> **Purpose**: CuraFrame exists to support safe, disciplined, systems-level reasoning in medicine. The primary goal is to help scientists **think more carefully, not faster**.

> **Safety-First Principle**: In CuraFrame, safety constraints precede creativity. All exploration occurs inside clearly defined boundaries. If a design violates safety assumptions, it is rejected—even if therapeutically attractive.

> **Acceptable Outcomes**: It is acceptable for CuraFrame to say *"This cannot be done safely."* That answer is considered **success**, not failure.

### Documentation Philosophy

CuraFrame treats documentation as **part of the system**, not supplementary material:

- **Constitutional Documents**: Define invariant principles that constrain future development
- **Provenance Requirements**: Every constraint includes literature references or expert consensus
- **Epistemic Honesty**: Uncertainty is documented explicitly, not hidden in probabilistic outputs
- **Version Control**: Constraint definitions are tracked in version control alongside code

> **Note**: Extending CuraFrame without consulting these documents may violate core safety principles. Contributors must demonstrate familiarity with `PHILOSOPHY.md` and `LIMITATIONS.md` before submitting pull requests.

---

## Contributing

### Contribution Philosophy

CuraFrame prioritizes **scientific rigor and conservative design** over feature velocity. Contributions must align with the framework's core principles:

1. **Safety over performance**: Reject optimizations that compromise auditability or transparency
2. **Provenance over convenience**: Every constraint requires documented scientific justification
3. **Restraint over ambition**: Resist scope creep into generative design or predictive modeling
4. **Clarity over cleverness**: Code should be readable by domain scientists, not just programmers

### Prerequisites

Before contributing, you **must**:
- Read `docs/PHILOSOPHY.md` and `docs/LIMITATIONS.md` in full
- Understand the constraint-first reasoning paradigm
- Commit to maintaining the separation between core reasoning (in `cura_frame/`) and presentation layers (in `apps/`)

### Contribution Guidelines

**Adding New Constraints**:
- Include full provenance (literature DOI, regulatory document, expert consultation)
- Document epistemic confidence (e.g., "established consensus" vs. "emerging evidence")
- Specify severity level with rationale
- Add unit tests verifying constraint evaluation logic

**Modifying Existing Constraints**:
- Provide justification for threshold changes (new data, regulatory updates, error correction)
- Maintain backward compatibility or clearly document breaking changes
- Update all affected documentation

**New Features**:
- Maintain zero external dependencies in core `cura_frame/` module
- Add comprehensive tests (target: >90% coverage for new code)
- Update README and relevant `docs/` files
- Ensure features align with framework philosophy (no generative capabilities, no optimization)

**Pull Request Requirements**:
- Clear scientific rationale in PR description
- All tests passing in CI
- Code formatted with `black` (if applicable)
- Documentation updates included
- No decrease in test coverage

### Code of Conduct

CuraFrame operates under a **scientific integrity code**:
- No exaggeration of capabilities
- No hidden assumptions or undocumented constraints
- No feature additions that enable misuse (e.g., clinical decision support)
- Transparency about limitations and uncertainty

**Prohibited Contributions**:
- Generative molecule design features
- Optimization algorithms targeting constraint satisfaction
- Predictive models for biological activity
- Clinical recommendation logic
- Integration with undocumented or closed-source constraint sources

### Getting Help

For questions about:
- **Scientific rationale**: Open a GitHub Discussion with `[Science]` tag
- **Bug reports**: Use GitHub Issues with reproducible example
- **Feature proposals**: Open Discussion with `[Proposal]` tag and philosophy alignment argument

---

## License

CuraFrame is licensed under the **MIT License**.

See the [LICENSE](LICENSE) file for complete legal text.

**Ethical Obligations** (not legally binding, but strongly encouraged):
- Do not use CuraFrame for clinical decision-making without appropriate medical oversight
- Document any modifications to constraint thresholds or evaluation logic
- Acknowledge limitations when presenting results
- Do not misrepresent CuraFrame as a drug discovery or optimization tool

---

## Citation and Attribution

### Software Citation

If CuraFrame is used in research, publications, or technical reports, please cite:

```bibtex
@software{curaframe2026,
  title = {CuraFrame: Constraint-Driven Therapeutic Design Reasoning},
  author = {Feeney, Don Michael},
  year = {2026},
  version = {5.0.0},
  url = {https://github.com/dfeen87/CuraFrame},
  license = {MIT}
}
```

### Methodological Citation

For references to the constraint-based reasoning approach:

```bibtex
@misc{curaframe_methodology2026,
  title = {Constraint-First Reasoning for Therapeutic Safety Assessment},
  author = {Feeney, Don Michael},
  year = {2026},
  howpublished = {GitHub Repository},
  url = {https://github.com/dfeen87/CuraFrame/blob/main/docs/CONSTRAINT_REASONING.md}
}
```

### Scientific Inspiration

CardiAnx-1 dual-domain therapeutic concept:

```bibtex
@article{kruger2025cardianx,
  title = {CardiAnx-1: A Conceptual Dual-Domain β₁-Blocker / 5-HT₁ₐ Hybrid for Heart–Brain Comorbidity},
  author = {Krüger, Marcel and Feeney, Don Michael},
  year = {2025},
  month = {December},
  note = {Conceptual design study}
}
```

### Acknowledgment in Text

For informal references in documentation or presentations:

> "Constraint evaluation was performed using CuraFrame (Feeney, 2026), a falsification framework for therapeutic design safety assessment."

---

## Related Work and Scientific Context

### Constraint-Based Drug Design

CuraFrame builds on established principles in medicinal chemistry:

- **Lipinski et al. (1997)**: Rule of Five for oral bioavailability
- **Veber et al. (2002)**: Molecular property guidelines for CNS drugs
- **ICH E14 Guideline**: Cardiac safety and QTc prolongation assessment
- **Waring et al. (2015)**: ADMET property optimization strategies

### Safety Pharmacology

Constraint thresholds derive from regulatory guidance and safety pharmacology literature:

- **hERG inhibition**: Redfern et al. (2003), "Safety pharmacology—a progressive approach"
- **β-adrenergic selectivity**: Baker (2005), "The selectivity of beta-adrenoceptor antagonists"
- **CNS penetration**: Hitchcock & Pennington (2006), "Structure−brain exposure relationships"

### Computational Frameworks

CuraFrame's falsification-first approach contrasts with:

- **QSAR models**: Predictive (probabilistic) rather than constraint-based (deterministic)
- **Generative models**: Optimization-driven rather than safety-driven
- **ADMET filters**: Often implicit scoring rather than explicit provenance

> **Unique Contribution**: CuraFrame treats constraints as **first-class scientific objects** with provenance, confidence, and population stratification—not as soft penalties in an optimization objective.

---

## Design Philosophy Summary

CuraFrame is intentionally **conservative, transparent, and safety-first**.

### Core Tenets

1. **Falsification over Optimization**  
   Designs are tested for violations, not scored for attractiveness. A design that "passes" is "not yet rejected"—not "validated" or "optimal."

2. **Constraints as Scientific Objects**  
   Each constraint carries provenance, rationale, confidence, and severity. They are not hyperparameters to tune—they are **encoded domain knowledge**.

3. **Transparency over Performance**  
   Auditable reasoning is prioritized over computational speed. Every rejection includes full diagnostic information.

4. **Honesty about Uncertainty**  
   Epistemic gaps are documented explicitly. CuraFrame does not hide uncertainty behind probabilistic outputs—it states what it knows and what it assumes.

5. **Rejection as Success**  
   If CuraFrame prevents even one unsafe design from being pursued uncritically, it has fulfilled its purpose.

### Operational Principles

> *"Clarity over cleverness."*  
> Code and constraints must be interpretable by domain scientists, not just software engineers.

> *"Restraint over ambition."*  
> CuraFrame intentionally does **not** generate, optimize, or predict. Scope discipline prevents mission creep into unsafe territory.

> *"Safety margins are not negotiable."*  
> Constraints derived from regulatory guidance and safety pharmacology are enforced without softening or probabilistic relaxation.

> *"Population-specific reasoning is explicit."*  
> Vulnerable populations (elderly, pediatric, comorbid) receive conservative constraint adjustments that are auditable and reversible.

---

## Concluding Remarks

CuraFrame exists to make **unsafe assumptions visible**—not to hide them behind automation.

It is a tool for **scientists who want to think more carefully** about therapeutic design, not for those seeking shortcuts to drug discovery.

If you believe a design is worth pursuing, CuraFrame will tell you **where it fails** and **what evidence would be needed** to reconsider. That is not obstruction—it is **scientific rigor**.

**Questions CuraFrame Helps Answer**:
- Which pharmacological principles does this design violate?
- What are the quantitative gaps between observed and required properties?
- How do safety margins change across patient populations?
- What literature supports these constraint thresholds?
- Where is the epistemic uncertainty in this evaluation?

**Questions CuraFrame Cannot Answer**:
- What molecule should I synthesize next?
- What is the predicted biological activity?
- How can I optimize this scaffold?
- Is this design better than existing drugs?
- Will this work in patients?

> **Final Principle**: CuraFrame is a **reasoning framework**, not a discovery engine. Use it to explore, question, and refine—never to replace experimental validation or clinical judgment.

---

## Acknowledgments

CuraFrame's development has been informed by:
- Decades of medicinal chemistry literature on structure-property relationships
- Regulatory guidance from FDA, EMA, and ICH on drug safety assessment
- Safety pharmacology research on cardiac, CNS, and respiratory toxicity
- Conceptual work on dual-domain therapeutics for comorbid disease (CardiAnx-1)

Thank you to the scientific community for establishing the knowledge base that CuraFrame attempts to encode faithfully and transparently.

I would like to acknowledge **Microsoft Copilot**, **Anthropic Claude**, and **Google Jules** for their meaningful assistance in refining concepts, improving clarity, and strengthening the overall quality of this work.

## Enterprise Consulting & Integration
This architecture is available under the MIT License. If your organization requires custom scaling, proprietary integration, or dedicated technical consulting to deploy these models at an enterprise level, please reach out at: dfeen87@gmail.com
