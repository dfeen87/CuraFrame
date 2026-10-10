import pytest
from cura_frame.core import Constraint, Candidate, ConstraintGroup, LogicOp
from cura_frame.advisor import compute_gap_analysis

def less_than_comparator(value, threshold):
    return value < threshold

def test_standalone_advisor_precedence():
    # If the advisor is called standalone without a context:
    # AND group with 1 PASS and 1 FAIL should be Failed.
    # AND group with 1 FAIL and 1 INDETERMINATE should be Failed.
    # AND group with 1 PASS and 1 INDETERMINATE should be Indeterminate.
    c1 = Constraint(name="c1", threshold=100.0, comparator=less_than_comparator, rationale="test")
    c2 = Constraint(name="c2", threshold=100.0, comparator=less_than_comparator, rationale="test")

    cg_and = ConstraintGroup(name="and_group", op=LogicOp.AND, children=[c1, c2])

    # 1 pass, 1 fail
    candidate = Candidate("test", {"c1": 50.0, "c2": 150.0})
    res = compute_gap_analysis([cg_and], candidate)
    assert res["constraints"][0]["status"] == "Failed"

    # 1 fail, 1 missing
    candidate2 = Candidate("test2", {"c1": 150.0})
    res2 = compute_gap_analysis([cg_and], candidate2)
    assert res2["constraints"][0]["status"] == "Failed"

    # 1 pass, 1 missing
    candidate3 = Candidate("test3", {"c1": 50.0})
    res3 = compute_gap_analysis([cg_and], candidate3)
    assert res3["constraints"][0]["status"] == "Indeterminate"
