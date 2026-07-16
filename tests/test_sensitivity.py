import pytest
from cura_frame import (
    CuraFrame,
    Candidate,
    EvaluationStatus,
    core_safety_constraints,
)
from cura_frame.sensitivity import (
    run_1d_sweep,
    run_2d_sweep,
    find_inflection_points,
)

def test_1d_sweep_basic():
    # Setup baseline framework with core safety constraints
    # logP_max <= 4.0, hERG >= 10.0, beta1 >= 100.0
    constraints = core_safety_constraints()
    framework = CuraFrame(constraints, name="TestFramework")

    # Baseline candidate
    baseline = Candidate(
        name="test_candidate",
        properties={
            "logP": 2.0,
            "hERG_IC50": 15.0,
            "beta1_selectivity": 120.0
        }
    )

    # Sweep logP from 2.0 to 5.0 in 4 steps (2.0, 3.0, 4.0, 5.0)
    results = run_1d_sweep(
        framework=framework,
        baseline_candidate=baseline,
        property_name="logP",
        min_val=2.0,
        max_val=5.0,
        steps=4,
        strict=True
    )

    assert len(results) == 4
    assert results[0]["value"] == 2.0
    assert results[0]["status"] == EvaluationStatus.ACCEPTED
    assert results[1]["value"] == 3.0
    assert results[1]["status"] == EvaluationStatus.ACCEPTED
    assert results[2]["value"] == 4.0
    assert results[2]["status"] == EvaluationStatus.ACCEPTED
    assert results[3]["value"] == 5.0
    assert results[3]["status"] == EvaluationStatus.REJECTED
    assert "logP" in results[3]["violations"]

def test_find_inflection_points():
    constraints = core_safety_constraints()
    framework = CuraFrame(constraints, name="TestFramework")
    baseline = Candidate(
        name="test_candidate",
        properties={
            "logP": 2.0,
            "hERG_IC50": 15.0,
            "beta1_selectivity": 120.0
        }
    )

    # Sweep logP across the 4.0 boundary
    results = run_1d_sweep(
        framework=framework,
        baseline_candidate=baseline,
        property_name="logP",
        min_val=3.0,
        max_val=5.0,
        steps=5,  # 3.0, 3.5, 4.0, 4.5, 5.0
        strict=True
    )

    inflections = find_inflection_points(results)
    assert len(inflections) == 1
    inflection = inflections[0]
    assert inflection["value_from"] == 4.0
    assert inflection["status_from"] == EvaluationStatus.ACCEPTED
    assert inflection["value_to"] == 4.5
    assert inflection["status_to"] == EvaluationStatus.REJECTED
    assert "logP" in inflection["violations_to"]

def test_1d_sweep_population_stratification():
    constraints = core_safety_constraints()
    framework = CuraFrame(constraints, name="TestFramework")
    framework.add_population("elderly", {
        "hERG_IC50": lambda c: c.threshold * 1.5,  # 10.0 * 1.5 = 15.0
    })

    # Candidate with hERG_IC50 = 12.0
    # In general population (threshold 10.0): ACCEPTED
    # In elderly population (threshold 15.0): REJECTED
    baseline = Candidate(
        name="test_candidate",
        properties={
            "logP": 2.0,
            "hERG_IC50": 12.0,
            "beta1_selectivity": 120.0
        }
    )

    # Run general population sweep on hERG_IC50 (from 8.0 to 16.0)
    results_general = run_1d_sweep(
        framework=framework,
        baseline_candidate=baseline,
        property_name="hERG_IC50",
        min_val=8.0,
        max_val=16.0,
        steps=5,  # 8.0, 10.0, 12.0, 14.0, 16.0
        population=None
    )

    # 8.0 -> Rejected, 10.0 -> Accepted, 12.0 -> Accepted, etc.
    assert results_general[0]["status"] == EvaluationStatus.REJECTED
    assert results_general[1]["status"] == EvaluationStatus.ACCEPTED

    # Run elderly population sweep
    results_elderly = run_1d_sweep(
        framework=framework,
        baseline_candidate=baseline,
        property_name="hERG_IC50",
        min_val=8.0,
        max_val=16.0,
        steps=5,  # 8.0, 10.0, 12.0, 14.0, 16.0
        population="elderly"
    )

    # Threshold is 15.0, so:
    # 8.0 -> Rejected, 10.0 -> Rejected, 12.0 -> Rejected, 14.0 -> Rejected, 16.0 -> Accepted
    assert results_elderly[3]["status"] == EvaluationStatus.REJECTED  # 14.0 is rejected
    assert results_elderly[4]["status"] == EvaluationStatus.ACCEPTED  # 16.0 is accepted

def test_2d_sweep_basic():
    constraints = core_safety_constraints()
    framework = CuraFrame(constraints, name="TestFramework")
    baseline = Candidate(
        name="test_candidate",
        properties={
            "logP": 2.0,
            "hERG_IC50": 15.0,
            "beta1_selectivity": 120.0
        }
    )

    results2d = run_2d_sweep(
        framework=framework,
        baseline_candidate=baseline,
        prop1="logP",
        min1=3.0,
        max1=5.0,
        prop2="hERG_IC50",
        min2=8.0,
        max2=12.0,
        steps1=3,  # 3.0, 4.0, 5.0
        steps2=3,  # 8.0, 10.0, 12.0
    )

    assert len(results2d) == 9

    # Coordinate (logP=3.0, hERG_IC50=12.0) -> ACCEPTED
    accepted_coords = [r for r in results2d if r["status"] == EvaluationStatus.ACCEPTED]
    assert len(accepted_coords) > 0

    # Coordinate (logP=5.0, hERG_IC50=8.0) -> REJECTED (both violations)
    coord_double_violation = [r for r in results2d if r["value1"] == 5.0 and r["value2"] == 8.0][0]
    assert coord_double_violation["status"] == EvaluationStatus.REJECTED
    assert "logP" in coord_double_violation["violations"]
    assert "hERG_IC50" in coord_double_violation["violations"]

def test_sweep_invalid_steps():
    constraints = core_safety_constraints()
    framework = CuraFrame(constraints, name="TestFramework")
    baseline = Candidate(name="test", properties={"logP": 2.0})

    with pytest.raises(ValueError):
        run_1d_sweep(framework, baseline, "logP", 1.0, 5.0, steps=0)

    with pytest.raises(ValueError):
        run_2d_sweep(framework, baseline, "logP", 1.0, 5.0, "hERG_IC50", 1.0, 5.0, steps1=0)
