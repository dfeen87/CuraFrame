# Constraint Bundles

CuraFrame features a parallel C++ constraint-bundle universe evaluating therapeutics via multi-domain physical and physiological proxy checks. These bundles produce deterministic structured penalty signals, rigorous falsification flags, and an interpretable narrative summary.

## Domains

### Metabolic Stability (`MetabolicBundle`)
**Rationale:** Tracks physiological processing vectors, focusing on clearance pressure, reactive metabolite emergence, and half-life viability.
**Output Format:** Signals for `clearance_pressure`, `metabolic_load`, flags for `ENZYME_SATURATION_EXCEEDED`, etc.

### Systemic Exposure (`SystemicExposureBundle`)
**Rationale:** Simulates systemic overload constraints, volume of distribution pressures, and cumulative toxicity metrics over repeated dosing.

### Organ-Specific Constraints
- **Hepatic (`HepaticBundle`):** Hepatotoxicity heuristics, enzyme saturation, biliary-clearance pressure.
- **Renal (`RenalBundle`):** Filtration pressure bottlenecks, nephrotoxicity alerts, solute-load bounds.
- **Cardiac (`CardiacBundle`):** QT-prolongation surrogates, conduction-instability flags, perfusion-pressure penalties.
- **CNS (`CNSBundle`):** BBB over-penetration, neuro-instability, excitotoxicity.

### Therapeutic & Systemic Profiles
- **Anti-Infective (`AntiInfectiveBundle`):** Pathogen-pressure checks, resistance-risk triggers, microbiome dysbiosis metrics.
- **Oncology (`OncologyBundle`):** Proliferative-pressure requirements, off-target cytotoxicity, therapeutic window inversion checks.
- **Immunologic (`ImmunologicBundle`):** Cytokine-storm alerts, baseline immune activation thresholds, tolerance breakdown risks.

### Physicochemical & Pharmacological
- **Formulation (`FormulationBundle`):** Solubility deficits, chemical instability, delivery-vector incompatibilities.
- **PK/PD (`PKPDBundle`):** Dose-response slope analysis, receptor saturation, effect-window decoupling flags.
- **Safety (`SafetyBundle`):** Multi-organ stress aggregation, systemic catastrophe triggers.
