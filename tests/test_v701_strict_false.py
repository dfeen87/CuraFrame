import pytest
from cura_frame.core import CuraFrame, Constraint, EvaluationStatus, Candidate, ConstraintGroup, LogicOp, Severity

def less_than_comparator(value, threshold):
    return value < threshold

def test_strict_false_root_status_sync():
    # If c1 passes, but c2 is missing, under strict=False the overall evaluation should be ACCEPTED.
    # The gap_analysis should correctly read "Passed" at the root level, but c2 should read "Indeterminate".
    c1 = Constraint(name="c1", threshold=100.0, comparator=less_than_comparator, rationale="test")
    c2 = Constraint(name="c2", threshold=100.0, comparator=less_than_comparator, rationale="test")

    cf = CuraFrame(safety_constraints=[c1, c2])
    candidate = Candidate("test", {"c1": 50.0})
    res = cf.evaluate(candidate, strict=False)

    assert res.status == EvaluationStatus.ACCEPTED
    assert res.gap_analysis["status"] == "Passed", "Root level status in gap analysis should sync with ACCEPTED"

    # c2 should still read Indeterminate at the child level
    c2_report = next((c for c in res.gap_analysis["constraints"] if c["name"] == "c2"), None)
    assert c2_report is not None
    assert c2_report["status"] == "Indeterminate", "Child level details must be preserved"
