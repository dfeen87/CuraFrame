import pytest
from cura_frame.core import CuraFrame, Constraint, EvaluationStatus, Candidate, ConstraintGroup, LogicOp, Severity
from cura_frame.advisor import compute_gap_analysis

def less_than_comparator(value, threshold):
    return value < threshold

class CallCountingConstraint(Constraint):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.calls = 0

    def evaluate(self, value):
        self.calls += 1
        return super().evaluate(value)

class StatefulAlternatingConstraint(Constraint):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = True

    def evaluate(self, value):
        res = self.state
        self.state = not self.state
        return res

def test_empty_groups_value_error():
    with pytest.raises(ValueError, match="Empty constraint groups are not permitted"):
        ConstraintGroup(name="empty_and", op=LogicOp.AND, children=[])

def test_single_execution_optimization():
    c1 = CallCountingConstraint(name="c1", threshold=100.0, comparator=less_than_comparator, rationale="test", severity=Severity.CRITICAL)
    cf = CuraFrame(safety_constraints=[c1])
    candidate = Candidate("test", {"c1": 50.0})

    res = cf.evaluate(candidate, strict=False)

    assert c1.calls == 1, f"Expected 1 call, got {c1.calls}"

def test_stateful_alternating_advisor_consistency():
    c1 = StatefulAlternatingConstraint(name="c1", threshold=100.0, comparator=less_than_comparator, rationale="test", severity=Severity.CRITICAL)
    cf = CuraFrame(safety_constraints=[c1])
    candidate = Candidate("test", {"c1": 50.0})

    res = cf.evaluate(candidate, strict=False)

    assert res.status == EvaluationStatus.ACCEPTED
    assert res.gap_analysis["status"] == "Passed"

def test_advisor_and_core_status_agreement_fail_vs_indeterminate():
    c1 = Constraint(name="c1", threshold=100.0, comparator=less_than_comparator, rationale="test", severity=Severity.CRITICAL)
    c2 = Constraint(name="c2", threshold=100.0, comparator=less_than_comparator, rationale="test", severity=Severity.CRITICAL)
    cg_and = ConstraintGroup(name="and_group", op=LogicOp.AND, children=[c1, c2])

    cf = CuraFrame(safety_constraints=[cg_and])
    candidate = Candidate("test", {"c1": 150.0}) # c1 fails, c2 missing

    res = cf.evaluate(candidate, strict=False)

    assert res.status == EvaluationStatus.REJECTED
    assert res.gap_analysis["status"] == "Failed", f"Advisor said {res.gap_analysis['status']}, core said REJECTED"

def test_nested_empty_or():
    c1 = Constraint(name="c1", threshold=100.0, comparator=less_than_comparator, rationale="test")
    cg_or_empty = ConstraintGroup(name="or", op=LogicOp.OR, children=[c1])
    cg_or_empty.children = [] # bypass validation

    cg_or = ConstraintGroup(name="or2", op=LogicOp.OR, children=[c1, cg_or_empty])
    cf = CuraFrame(safety_constraints=[cg_or])
    candidate = Candidate("test", {"c1": 150.0}) # c1 fails

    res = cf.evaluate(candidate, strict=False)
    assert res.status == EvaluationStatus.INDETERMINATE

def test_duplicate_names_do_not_override():
    c1 = Constraint(name="dup", threshold=100.0, comparator=less_than_comparator, rationale="test1")
    c2 = Constraint(name="dup", threshold=200.0, comparator=less_than_comparator, rationale="test2")

    cg = ConstraintGroup(name="dup", op=LogicOp.AND, children=[c1, c2])

    # Bypass init validation that strictly prevents duplicate root level names since it only applies to constraints.
    # We test the core evaluator here. We must manually build the CF.
    cf = CuraFrame(safety_constraints=[])
    cf.safety_constraints = [cg]
    candidate = Candidate("test", {"dup": 150.0})

    res = cf.evaluate(candidate, strict=False)
    assert res.status == EvaluationStatus.REJECTED

    group_report = res.gap_analysis["constraints"][0]
    child_reports = group_report["children"]
    c1_report = child_reports[0]
    c2_report = child_reports[1]

    assert c1_report["status"] == "Failed"
    assert c2_report["status"] == "Passed"

def test_unsupported_node_type():
    c1 = Constraint(name="c1", threshold=100.0, comparator=less_than_comparator, rationale="test")
    with pytest.raises(TypeError, match="Unsupported constraint node type"):
        CuraFrame(safety_constraints=[c1, "MALFORMED"]) # type: ignore
