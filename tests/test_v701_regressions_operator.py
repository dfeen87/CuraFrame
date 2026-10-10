import pytest
from cura_frame.core import CuraFrame, Constraint, EvaluationStatus, Candidate, ConstraintGroup, LogicOp, Severity
from cura_frame.comparators import less_than

def test_invalid_logic_operator():
    c1 = Constraint(name="c1", threshold=100.0, comparator=less_than, rationale="test")
    cg = ConstraintGroup(name="cg", op=LogicOp.AND, children=[c1])
    cg.op = "UNKNOWN_OP" # bypass type check

    cf = CuraFrame(safety_constraints=[cg])
    with pytest.raises(ValueError, match="Unsupported logical operator"):
        cf.evaluate(Candidate("t", {"c1": 50.0}), strict=False)
