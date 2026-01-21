# CuraFrame

**Constraint-Driven Therapeutic Design Reasoning**

CuraFrame is a transparent, safety-first framework for reasoning about hypothetical therapeutic designs using explicit, non-negotiable constraints.

It is designed to help scientists, engineers, and researchers understand **where designs fail**, **why they fail**, and **under what assumptions they might be reconsidered** — without automating discovery or making clinical claims.

**CuraFrame does not try to find drugs.**  
**It tries to make unsafe ideas fail early, clearly, and honestly.**

---

## What CuraFrame Is

CuraFrame is:

- A **constraint evaluation engine** for therapeutic concepts
- A system for **explicit safety boundaries**
- A framework for **auditable, reproducible reasoning**
- A tool for **education, documentation, and design exploration**

It evaluates whether a hypothetical candidate satisfies known limits derived from:

- Medicinal chemistry
- Pharmacology
- Safety pharmacology
- Population-specific risk considerations

---

## What CuraFrame Is NOT

CuraFrame is **not**:

- ❌ A drug discovery engine
- ❌ A molecule generator
- ❌ An optimizer
- ❌ A machine-learning model
- ❌ A clinical decision support system
- ❌ A replacement for medicinal chemistry expertise

**No molecules are generated.**  
**No properties are optimized.**  
**No medical recommendations are made.**

> If CuraFrame says *"this cannot be done safely"*, that is considered a **successful outcome**.

---

## Repository Structure
```
CuraFrame/
├── cura_frame/                  # Core reasoning engine (library)
│   ├── __init__.py              # Public API + metadata
│   ├── core.py                  # Constraint evaluation engine
│   ├── comparators.py           # Pure comparison semantics
│   ├── constraints_library.py   # Canonical constraint definitions
│   └── tests/
│       └── test_core.py         # Enforcement & regression tests
│
├── apps/
│   └── console_streamlit/       # Presentation layer
│       ├── app.py               # Streamlit UI
│       ├── __init__.py          # Package metadata
│       └── __main__.py          # Module launcher
│
├── docs/                        # Constitutional documentation
│   ├── PHILOSOPHY.md            # Core principles
│   ├── CONSTRAINT_REASONING.md  # Technical approach
│   ├── POPULATION_STRATIFICATION.md
│   ├── LIMITATIONS.md           # Explicit boundaries
│   ├── ETHICAL_USE.md           # Usage constraints
│   └── INSPIRATION.md           # Scientific origins
│
├── launch_console.py            # Root-level UI launcher
├── README.md                    # This file
├── LICENSE                      # MIT License
└── pyproject.toml               # Package configuration
```

### Architectural Intent

- **`cura_frame/`** is the engine  
  It contains no UI code and no external tooling assumptions.

- **`apps/`** is the presentation layer  
  It visualizes reasoning but does not influence it.

- **`docs/`** are constitutional  
  They define scope, ethics, limits, and philosophy.

- **Root scripts** are launchers, not libraries.

---

## Core Concepts

### Constraint-First Reasoning

CuraFrame treats **constraints as first-class objects**, each with:

- A **threshold** (the limit)
- A **comparator** (how to evaluate)
- A **rationale** (why this limit exists)
- A **severity** (CRITICAL, SEVERE, WARNING)
- **Explicit provenance** and confidence

**Constraints are not targets.**  
**They are boundaries.**

### Population Stratification

Safety margins are not universal.

CuraFrame allows constraints to be **conservatively tightened** for populations such as:

- Elderly patients
- Pediatric populations
- Asthmatics
- Comorbid risk groups

This makes assumptions **explicit** instead of implicit.

### Rejection Is Informative

A rejected candidate includes:

- Which constraints failed
- Observed vs. required values
- Severity of violation
- Epistemic confidence
- Human-readable rationale

**Rejection is not a dead end — it is documentation.**

---

## Installation

### From Source
```bash
git clone https://github.com/dfeen87/CuraFrame.git
cd CuraFrame
pip install -e .
```

### Dependencies

Core dependencies:
- Python 3.9+
- No external libraries (core is pure Python)

For the Streamlit console:
```bash
pip install streamlit
```

---

## Quick Start

### Using the Core Library
```python
from cura_frame import CuraFrame, Candidate
from cura_frame.constraints_library import core_safety_constraints

# Build framework with safety constraints
framework = CuraFrame(
    core_safety_constraints(),
    name="SafetyEvaluator"
)

# Define a hypothetical candidate
candidate = Candidate(
    name="test_compound",
    properties={
        "logP": 3.5,
        "hERG_IC50": 15.0,  # μM
        "beta1_selectivity": 120.0
    }
)

# Evaluate
result = framework.evaluate(candidate)

if result.is_accepted():
    print("✓ All constraints satisfied")
else:
    print("✗ Violations detected:")
    for violation in result.violations:
        print(f"  - {violation.constraint}: {violation.rationale}")
```

### Using the Streamlit Console

Launch the interactive console:
```bash
# Recommended
python launch_console.py

# Or directly
streamlit run apps/console_streamlit/app.py

# Or as a module
python -m apps.console_streamlit
```

The console allows you to:

- Select constraint bundles (Core Safety, CNS, Cardiology, CardiAnx-1, etc.)
- Define hypothetical candidates via JSON
- Apply population modifiers
- View detailed violations and warnings
- Export results and constraint metadata

---

## Example: CardiAnx-1 Dual-Domain Evaluation

CardiAnx-1 is a conceptual dual-domain β₁-blocker / 5-HT₁ₐ hybrid for heart-brain comorbidity (Krüger & Feeney, 2025).
```python
from cura_frame import CuraFrame, Candidate
from cura_frame.constraints_library import cardiAnx_dual_domain_constraints

# Build CardiAnx-1 framework
framework = CuraFrame(
    cardiAnx_dual_domain_constraints(),
    name="CardiAnx-1_Evaluator"
)

# Add population-specific constraints
framework.add_population("asthmatic", {
    "beta1_selectivity": lambda c: c.threshold * 2.0  # 200x required
})

# Define candidate
candidate = Candidate(
    name="CardiAnx-A1",
    properties={
        "logP": 3.2,
        "polar_surface_area": 75.0,
        "molecular_weight": 485.0,
        "hERG_IC50": 15.0,
        "beta1_selectivity": 170.0,
        "Kd_5HT1A": 12.0,  # nM
        "Kd_5HT2A": 650.0,
        "Kd_D2": 1200.0,
        "plasma_half_life": 12.0  # hours
    }
)

# Evaluate
result = framework.evaluate(candidate, population="asthmatic")

print(result.summary())
```

---

## Testing

The core engine is enforced with unit tests:
```bash
pytest cura_frame/tests
```

Tests focus on:

- Constraint semantics
- Population stratification behavior
- Error handling
- Auditability
- Reproducibility

---

## Documentation (Required Reading)

The following documents define CuraFrame's scope and intent and **should be read** before extending or using the framework:

- **`PHILOSOPHY.md`**  
  Foundational principles and design intent.

- **`CONSTRAINT_REASONING.md`**  
  How constraints are evaluated and why this approach was chosen.

- **`POPULATION_STRATIFICATION.md`**  
  How and why constraints change across patient populations.

- **`LIMITATIONS.md`**  
  Explicit boundaries of what CuraFrame does not attempt.

- **`ETHICAL_USE.md`**  
  Ethical constraints and misuse prevention.

- **`INSPIRATION.md`**  
  Scientific and conceptual origins (including the CardiAnx-1 work).

**These documents are not optional; they are part of the system.**

---

## Philosophy in Brief

From `PHILOSOPHY.md`:

> CuraFrame exists to support **safe, disciplined, systems-level reasoning in medicine**.
>
> It is a framework for exploring therapeutic design spaces under explicit pharmacological, physiological, and ethical constraints — not a tool for automated drug creation or clinical decision-making.
>
> **The primary goal of CuraFrame is to help scientists think more carefully, not faster.**

### Safety First Principle

> In CuraFrame, **safety constraints precede creativity**.
>
> All exploration occurs inside clearly defined boundaries. If a design violates safety assumptions, it is rejected by the framework — even if it appears therapeutically attractive.

### Acceptable Outcomes

> It is acceptable for CuraFrame to say:
>
> *"This cannot be done safely."*
>
> That answer is considered **success**.

---

## Contributing

CuraFrame is intentionally **conservative** and **disciplined**.

Contributions should:

- Maintain separation between core reasoning and presentation
- Include provenance for all constraints
- Add tests for new functionality
- Update documentation when changing scope
- Respect the philosophy of restraint over ambition

Before contributing, please read `PHILOSOPHY.md` and `LIMITATIONS.md`.

---

## License

This project is released under the **MIT License**.

You are free to use, modify, and distribute this software, provided the license terms are respected.

See `LICENSE` file for full details.

---

## Citation

If you use CuraFrame in your research or reference its design principles, please cite:
```bibtex
@software{curaframe2025,
  title = {CuraFrame: Constraint-Driven Therapeutic Design Reasoning},
  author = {Feeney, Don},
  year = {2025},
  url = {https://github.com/dfeen87/CuraFrame}
}
```

**Inspiration:**
```bibtex
@article{kruger2025cardianx,
  title = {CardiAnx-1: A Conceptual Dual-Domain β₁-Blocker / 5-HT₁ₐ Hybrid for Heart–Brain Comorbidity},
  author = {Krüger, Marcel and Feeney, Don},
  year = {2025},
  month = {December}
}
```

---

## Final Note

CuraFrame is intentionally conservative.

It exists to make **unsafe assumptions visible** — not to hide them behind automation.

If this framework prevents even one unsafe design from being pursued uncritically, it has done its job.

> *"Clarity over cleverness."*  
> *"Transparency over performance."*  
> *"Restraint over ambition."*  
> *"Honesty about uncertainty."*

— From the CuraFrame Philosophy
