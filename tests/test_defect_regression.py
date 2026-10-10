import math
import pytest
from cura_frame.core import CuraFrame, Constraint, EvaluationStatus, Candidate, ConstraintGroup, LogicOp, Severity
from cura_frame.comparators import less_than

def test_strict_false_or_group_false_acceptance():
    c1 = Constraint(name="c1", threshold=100.0, comparator=less_than, rationale="Test c1", severity=Severity.CRITICAL)
    c2 = Constraint(name="c2", threshold=100.0, comparator=less_than, rationale="Test c2", severity=Severity.CRITICAL)
    cg = ConstraintGroup(name="test_or_group", op=LogicOp.OR, children=[c1, c2])

    cf = CuraFrame(safety_constraints=[cg])

    # c1 is failing (150 > 100), c2 is missing
    # FAIL + MISSING should be INDETERMINATE, but currently evaluates as ACCEPTED
    candidate = Candidate("test_cand", {"c1": 150.0})
    res = cf.evaluate(candidate, strict=False)

    # We assert the expected corrected behavior to make the test fail on baseline
    assert res.status == EvaluationStatus.INDETERMINATE

def test_strict_false_and_group_partial_acceptance():
    c1 = Constraint(name="c1", threshold=100.0, comparator=less_than, rationale="Test c1", severity=Severity.CRITICAL)
    c2 = Constraint(name="c2", threshold=100.0, comparator=less_than, rationale="Test c2", severity=Severity.CRITICAL)
    cg = ConstraintGroup(name="test_and_group", op=LogicOp.AND, children=[c1, c2])

    cf = CuraFrame(safety_constraints=[cg])

    # c1 is passing, c2 is missing
    # PASS + MISSING should be ACCEPTED for non-strict mode partial evaluation
    candidate = Candidate("test_cand", {"c1": 50.0})
    res = cf.evaluate(candidate, strict=False)

    # We assert the expected corrected behavior to make the test fail on baseline
    assert res.status == EvaluationStatus.ACCEPTED

def test_strict_false_and_group_fail_and_missing():
    c1 = Constraint(name="c1", threshold=100.0, comparator=less_than, rationale="Test c1", severity=Severity.CRITICAL)
    c2 = Constraint(name="c2", threshold=100.0, comparator=less_than, rationale="Test c2", severity=Severity.CRITICAL)
    cg = ConstraintGroup(name="test_and_group", op=LogicOp.AND, children=[c1, c2])

    cf = CuraFrame(safety_constraints=[cg])

    # c1 is failing, c2 is missing
    # FAIL + MISSING should be REJECTED (since AND requires both to pass, one failing is an immediate failure)
    candidate = Candidate("test_cand", {"c1": 150.0})
    res = cf.evaluate(candidate, strict=False)

    # We assert the expected corrected behavior to make the test fail on baseline
    assert res.status == EvaluationStatus.REJECTED

def test_strict_false_or_group_pass_and_missing():
    c1 = Constraint(name="c1", threshold=100.0, comparator=less_than, rationale="Test c1", severity=Severity.CRITICAL)
    c2 = Constraint(name="c2", threshold=100.0, comparator=less_than, rationale="Test c2", severity=Severity.CRITICAL)
    cg = ConstraintGroup(name="test_or_group", op=LogicOp.OR, children=[c1, c2])

    cf = CuraFrame(safety_constraints=[cg])

    # c1 is passing, c2 is missing
    # PASS + MISSING should be ACCEPTED in OR group (one branch explicitly satisfied)
    candidate = Candidate("test_cand", {"c1": 50.0})
    res = cf.evaluate(candidate, strict=False)

    assert res.status == EvaluationStatus.ACCEPTED
