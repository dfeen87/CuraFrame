# Copyright (c) Don Michael Feeney Jr. Licensed under the MIT License.
import pytest
from cura_frame import (
    CuraFrame,
    Candidate,
    Constraint,
    Provenance,
    Severity,
    core_safety_constraints,
)
from cura_frame.comparators import less_than_or_equal, greater_than_or_equal
from cura_frame.interactions import (
    analyze_interactions,
    calculate_safety_margin,
)


def test_calculate_safety_margin():
    # Test less than or equal
    assert calculate_safety_margin("less_than_or_equal", 4.0, 3.0) == 0.25  # (4 - 3)/4 = 0.25
    assert calculate_safety_margin("less_than_or_equal", 4.0, 5.0) == -0.25  # (4 - 5)/4 = -0.25

    # Test greater than or equal
    assert calculate_safety_margin("greater_than_or_equal", 10.0, 15.0) == 0.5  # (15 - 10)/10 = 0.5
    assert calculate_safety_margin("greater_than_or_equal", 10.0, 5.0) == -0.5  # (5 - 10)/10 = -0.5

    # Test within range
    assert calculate_safety_margin("within_range", (2.0, 4.0), 3.0) == 0.5  # mid range: min(3-2, 4-3)/2 = 0.5
    assert calculate_safety_margin("within_range", (2.0, 4.0), 1.0) == -0.5  # (1 - 2)/2 = -0.5
    assert calculate_safety_margin("within_range", (2.0, 4.0), 5.0) == -0.5  # (4 - 5)/2 = -0.5


def test_analyze_interactions_accepted():
    # Setup framework with core safety constraints (logP <= 4.0, hERG >= 10.0, beta1 >= 100.0)
    constraints = core_safety_constraints()
    framework = CuraFrame(constraints, name="TestFramework")

    # This candidate satisfies all constraints:
    # logP = 3.0 (margin = 1.0/4.0 = 0.25)
    # hERG_IC50 = 20.0 (margin = 10.0/10.0 = 1.0)
    # beta1_selectivity = 150.0 (margin = 50.0/100.0 = 0.5)
    candidate = Candidate(
        name="safe_candidate",
        properties={
            "logP": 3.0,
            "hERG_IC50": 20.0,
            "beta1_selectivity": 150.0
        }
    )

    analysis = analyze_interactions(candidate, framework)

    assert analysis["candidate_name"] == "safe_candidate"
    assert analysis["status"] == "accepted"
    assert len(analysis["margins"]) == 3

    # Verify margins
    margins_by_name = {m["name"]: m for m in analysis["margins"]}
    assert margins_by_name["logP"]["margin"] == 0.25
    assert margins_by_name["logP"]["satisfied"] is True

    assert margins_by_name["hERG_IC50"]["margin"] == 1.0
    assert margins_by_name["hERG_IC50"]["satisfied"] is True

    # Physical weakest link for accepted candidate should be the one closest to boundary
    # That is logP (margin = 0.25)
    assert analysis["physical_weakest_link"] is not None
    assert analysis["physical_weakest_link"]["name"] == "logP"


def test_analyze_interactions_rejected():
    constraints = core_safety_constraints()
    framework = CuraFrame(constraints, name="TestFramework")

    # This candidate violates logP (logP=5.0 vs <=4.0, margin = -0.25)
    candidate = Candidate(
        name="unsafe_candidate",
        properties={
            "logP": 5.0,
            "hERG_IC50": 20.0,
            "beta1_selectivity": 150.0
        }
    )

    analysis = analyze_interactions(candidate, framework)

    assert analysis["status"] == "rejected"
    assert analysis["physical_weakest_link"] is not None
    assert analysis["physical_weakest_link"]["name"] == "logP"
    assert analysis["physical_weakest_link"]["satisfied"] is False
    assert analysis["physical_weakest_link"]["margin"] < 0


def test_analyze_interactions_epistemic_weakest_link():
    # Setup custom constraints to test epistemic weakest link
    c1 = Constraint(
        name="param1",
        threshold=10.0,
        comparator=less_than_or_equal,
        rationale="test param 1",
        severity=Severity.CRITICAL,
        provenance=Provenance(source_type="literature", confidence=0.95, references=["ref1", "ref2", "ref3"])
    )
    c2 = Constraint(
        name="param2",
        threshold=5.0,
        comparator=greater_than_or_equal,
        rationale="test param 2",
        severity=Severity.SEVERE,
        provenance=Provenance(source_type="expert", confidence=0.45, references=["ref1"])
    )
    framework = CuraFrame([c1, c2], name="EpistemicFramework")

    candidate = Candidate(
        name="test_candidate",
        properties={
            "param1": 8.0,
            "param2": 6.0
        }
    )

    analysis = analyze_interactions(candidate, framework)

    # Epistemic weakest link has the lowest confidence score, which is param2 (confidence = 0.45)
    assert analysis["epistemic_weakest_link"] is not None
    assert analysis["epistemic_weakest_link"]["name"] == "param2"
    assert analysis["epistemic_weakest_link"]["confidence"] == 0.45
