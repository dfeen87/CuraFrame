import pytest
import json
from cura_frame import (
    CuraFrame,
    Candidate,
    EvaluationStatus,
    Severity,
    core_safety_constraints,
    lipinski_rule_of_five,
    cns_drug_constraints,
    cardiology_oriented_constraints,
)

def test_dynamic_parameter_union():
    # Gather constraints from multiple bundles
    bundles_to_test = {
        "Core Safety": core_safety_constraints,
        "Lipinski Ro5": lipinski_rule_of_five,
        "CNS Constraints": cns_drug_constraints,
    }

    # Verify we can extract and merge unique parameter names
    all_selected_constraints = []
    for fn in bundles_to_test.values():
        all_selected_constraints.extend(fn())

    property_names = sorted(list(set(c.name for c in all_selected_constraints)))

    # Ensure key parameters are in the union
    assert "logP" in property_names
    assert "hERG_IC50" in property_names
    assert "molecular_weight" in property_names
    assert "polar_surface_area" in property_names
    assert "hydrogen_bond_donors" in property_names


def test_multi_bundle_evaluation():
    # Setup candidate properties spanning multiple domains
    properties = {
        "logP": 3.0,
        "hERG_IC50": 25.0,            # satisfies Core (>=10) and Cardiology (>=15)
        "beta1_selectivity": 150.0,    # satisfies Core (>=100)
        "molecular_weight": 350.0,     # satisfies CNS & Lipinski
        "polar_surface_area": 60.0,    # satisfies CNS (40-80)
        "hydrogen_bond_donors": 1,
        "hydrogen_bond_acceptors": 5,
    }

    cand = Candidate(
        name="multi_domain_candidate",
        properties=properties
    )

    # Evaluate across multiple bundles
    selected_bundles = {
        "Core Safety": core_safety_constraints,
        "Lipinski Ro5": lipinski_rule_of_five,
        "CNS Constraints": cns_drug_constraints,
    }

    matrix_results = {}
    for name, fn in selected_bundles.items():
        constraints = fn()
        cura = CuraFrame(constraints, name=f"CuraFrame::{name}")
        result = cura.evaluate(cand, strict=True)
        matrix_results[name] = result

    # Verify that they all pass under this highly compliant profile
    assert matrix_results["Core Safety"].status == EvaluationStatus.ACCEPTED
    assert matrix_results["Lipinski Ro5"].status == EvaluationStatus.ACCEPTED
    assert matrix_results["CNS Constraints"].status == EvaluationStatus.ACCEPTED


def test_cross_therapeutic_profile_warnings():
    # Candidate with good CNS profile but failing Cardiology due to hERG (critical violation)
    properties = {
        "logP": 3.0,
        "hERG_IC50": 4.0,              # fails Cardiology/Core Safety (critical hERG violation)
        "beta1_selectivity": 150.0,
        "molecular_weight": 350.0,
        "polar_surface_area": 60.0,
        "hydrogen_bond_donors": 1,
        "hydrogen_bond_acceptors": 5,
    }

    cand = Candidate(
        name="contradictory_candidate",
        properties=properties
    )

    selected_bundles = {
        "CNS Constraints": cns_drug_constraints,
        "Cardiology-Oriented": cardiology_oriented_constraints,
    }

    matrix_results = {}
    for name, fn in selected_bundles.items():
        constraints = fn()
        cura = CuraFrame(constraints, name=f"CuraFrame::{name}")
        result = cura.evaluate(cand, strict=True)
        matrix_results[name] = result

    assert matrix_results["CNS Constraints"].status == EvaluationStatus.ACCEPTED
    assert matrix_results["Cardiology-Oriented"].status == EvaluationStatus.REJECTED

    # Detect cross-therapeutic contradictions dynamically
    cross_warnings = []
    accepted_list = ["CNS Constraints"]
    rejected_list = ["Cardiology-Oriented"]

    for acc in accepted_list:
        for rej in rejected_list:
            rej_result = matrix_results[rej]
            # Find critical violations
            crit_violations = [v for v in rej_result.violations if v.severity == Severity.CRITICAL]
            for cv in crit_violations:
                warning_text = (
                    f"Cross-Therapeutic Warning: Candidate meets {acc} criteria but fails {rej} constraints "
                    f"due to a CRITICAL violation: {cv.constraint} (observed: {cv.observed}, required: {cv.threshold})."
                )
                cross_warnings.append(warning_text)

    # Verify a critical cross-therapeutic warning was successfully triggered
    assert len(cross_warnings) == 1
    assert "hERG_IC50" in cross_warnings[0]
    assert "CNS Constraints" in cross_warnings[0]
    assert "Cardiology-Oriented" in cross_warnings[0]
