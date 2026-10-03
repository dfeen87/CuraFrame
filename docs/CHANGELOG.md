# Changelog

All notable CuraFrame changes, including the Python engine and C++ parallel
evaluation universe, are documented in this file.

## [7.0.0] - 2026-10-03 - BEDROCK hardening baseline

### Security and safety
- Non-finite numeric candidate evidence now produces an indeterminate result instead of being able to satisfy minimum constraints.
- The pipelayer governor now fails closed on non-finite, out-of-domain, or unsupported decision evidence without contaminating trust-pipeline history, and enforces configured trust/reliability minima as authorization gates.
- Governance records reject NaN and infinity rather than writing non-standard JSON numeric tokens.

### Added
- Regression coverage for finite therapeutic evidence, governance JSON integrity, and malformed pipelayer telemetry/state isolation.
- `--version` CLI output and a detailed BEDROCK engineering release report.

### CI
- Python tests and package/version smoke checks now run on supported boundary versions 3.9 and 3.11.
- The C++ constraint and scoring library is configured and compiled in Release mode.

This major increment establishes a new engineering baseline. It includes
incompatible validation changes for inputs that were never valid physical or
JSON evidence; otherwise the public architecture and accepted finite-input
behavior are preserved.

## [6.1.1] - 2026-09-28

### Changed
- Bumped codebase project version to 6.1.1 across all configuration and documentation sources.
- Added a pinned, non-root development container that runs Make targets from `/repro`.

## [6.1.0] - 2026-09-27

### Changed
- Bumped codebase project version to 6.1.0 across all configuration and documentation sources.

## [5.0.0] - 2026-04-11

### Changed
- Bumped project version to 5.0.0.

## [3.0.0] - 2026-04-10 - Weighted Scoring Engine

### Added
- **Weighted Multi-Constraint Scoring Engine**: Introduced a unified scoring engine that computes a Composite Stability Score (0-100) from constraint bundle outputs.
- **Scoring Pipeline & Reports**: Added `ScoringPipeline` and `ScoringReport` to aggregate penalties, bonuses, falsification impacts, and generate narrative summaries.
- **Weight Profiles**: Introduced configurable `WeightProfile` abstractions, including `DefaultResearchProfile` and `HighSafetyProfile`, for dynamic domain and signal weighting.
- **Integration**: Updated `MultiBundleEvaluator` to seamlessly pass evaluation reports into the scoring engine via `score` and `score_with_profile` methods without altering underlying constraint logic.
- **Documentation**: Added `scoring_engine.md` and `weight_profiles.md` detailing the scoring architecture and weight profile designs.

### Changed
- Bumped project version to 3.0.0.

## [2.5.0] - 2026-04-10 - Constraint-Bundle Universe

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
