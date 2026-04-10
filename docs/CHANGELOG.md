# Changelog

All notable changes to the C++ parallel evaluation universe will be documented in this file.

## [2.5.0] - Constraint-Bundle Universe

### Added
- **C++ Core Architecture:** Introduced `Candidate.hpp`, `EvaluationReport.hpp`, `ConstraintBundle.hpp`, `ConstraintRegistry.hpp`, and `MultiBundleEvaluator.hpp` in the `constraint_core/` directory to serve as the unified parallel evaluation layer.
- **Metabolic Constraints:** Clearance pressure, metabolic load, reactive metabolite risk, half-life instability, saturation thresholds.
- **Systemic Exposure Constraints:** Exposure window, distribution pressure, cumulative toxicity, systemic overload flags.
- **Organ-Specific Constraints:**
  - *Hepatic:* Enzyme saturation, hepatotoxicity heuristics, bile-clearance pressure.
  - *Renal:* Filtration pressure, nephrotoxicity heuristics, solute-load thresholds.
  - *Cardiac:* QT-risk heuristics, conduction-instability signals, perfusion-pressure penalties.
  - *CNS:* BBB penetration, neuro-instability, excitotoxicity flags.
- **Therapeutic Area Constraints:**
  - *Anti-Infective:* Pathogen-pressure heuristics, resistance-risk signals, microbiome disruption penalties.
  - *Oncology:* Proliferative-pressure, off-target cytotoxicity, therapeutic window alignment.
  - *Immunologic:* Cytokine-storm risk, immune-activation thresholds, tolerance-breakdown heuristics.
- **Physical & Pharmacology Constraints:**
  - *Formulation:* Solubility, stability, delivery-vector compatibility.
  - *PK/PD:* Dose-response curves, saturation thresholds, effect-window alignment.
  - *Safety:* Multi-organ stress, systemic penalties, aggregated risk flags.
- **Documentation:** Added `constraint_bundles.md` and `evaluation_pipeline.md` detailing the newly introduced domains, output formats, and evaluation flow.
