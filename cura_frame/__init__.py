"""
CuraFrame

A constraint-driven reasoning framework for safe, systems-level
therapeutic design exploration.

CuraFrame is NOT a drug discovery engine, optimizer, or clinical tool.
It exists to help scientists reason within explicit safety and ethical
boundaries.

See docs/PHILOSOPHY.md and docs/ETHICAL_USE.md for guiding principles.
"""

__version__ = "3.0.0"

from .core import (
    CuraFrame,
    Constraint,
    Provenance,
    Candidate,
    EvaluationResult,
    EvaluationStatus,
    Severity,
    Violation,
)
from .cli import main as cli_main

# Constraint library (explicit, opt-in usage)
from .constraints_library import (
    # Individual constraints
    logP_max,
    logP_range,
    molecular_weight_range,
    polar_surface_area_max,
    hydrogen_bond_donors_max,
    hydrogen_bond_acceptors_max,
    hERG_ic50_min,
    qtc_prolongation_risk_low,
    beta1_over_beta2_selectivity_min,
    serotonin_5ht1a_affinity_range,
    off_target_5ht2a_avoidance,
    dopamine_d2_avoidance,
    plasma_half_life_range,
    oral_bioavailability_min,
    hepatic_clearance_max,
    cyp3a4_inhibition_min,
    therapeutic_index_min,
    protein_binding_max,
    aqueous_solubility_min,

    # Constraint bundles
    core_safety_constraints,
    lipinski_rule_of_five,
    cns_drug_constraints,
    cardiology_oriented_constraints,
    cardiAnx_dual_domain_constraints,
    oncology_constraints,
    anti_infective_constraints,
    metabolic_disease_constraints,
)

__all__ = [
    # Core engine & primitives
    "CuraFrame",
    "Constraint",
    "Provenance",
    "Candidate",
    "EvaluationResult",
    "EvaluationStatus",
    "Severity",
    "Violation",
    "cli_main",

    # Constraint library (explicit exports)
    "logP_max",
    "logP_range",
    "molecular_weight_range",
    "polar_surface_area_max",
    "hydrogen_bond_donors_max",
    "hydrogen_bond_acceptors_max",
    "hERG_ic50_min",
    "qtc_prolongation_risk_low",
    "beta1_over_beta2_selectivity_min",
    "serotonin_5ht1a_affinity_range",
    "off_target_5ht2a_avoidance",
    "dopamine_d2_avoidance",
    "plasma_half_life_range",
    "oral_bioavailability_min",
    "hepatic_clearance_max",
    "cyp3a4_inhibition_min",
    "therapeutic_index_min",
    "protein_binding_max",
    "aqueous_solubility_min",

    # Bundles
    "core_safety_constraints",
    "lipinski_rule_of_five",
    "cns_drug_constraints",
    "cardiology_oriented_constraints",
    "cardiAnx_dual_domain_constraints",
    "oncology_constraints",
    "anti_infective_constraints",
    "metabolic_disease_constraints",
]
