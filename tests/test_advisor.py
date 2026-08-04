# Licensed under the PolyForm Noncommercial License 1.0.0
"""
CuraFrame Gap Analysis Advisor & Nested Logical Primitives Tests.
"""

import pytest
from typing import List

from cura_frame import (
    CuraFrame,
    Constraint,
    ConstraintGroup,
    LogicOp,
    Candidate,
    EvaluationStatus,
    Severity,
    Provenance,
)
from cura_frame.comparators import (
    less_than_or_equal,
    greater_than_or_equal,
    within_range,
    ratio_greater_than,
)
from cura_frame.advisor import (
    get_unit_by_name,
    get_comparator_type_and_direction,
    compute_gap_analysis,
)


def test_unit_mapping():
    assert get_unit_by_name("hERG_IC50") == "μM"
    assert get_unit_by_name("molecular_weight") == "Da"
    assert get_unit_by_name("Kd_5HT1A") == "nM"
    assert get_unit_by_name("unknown_parameter") == "units"


def test_comparator_type_and_direction():
    # less_than_or_equal
    comp_type, delta, direction, msg = get_comparator_type_and_direction(
        "logP", "less_than_or_equal", 4.0, 5.2
    )
    assert comp_type == "less_than_or_equal"
    assert delta == 1.2
    assert direction == "reduce"
    assert "logP must be reduced by ≥ 1.2 units" in msg

    # greater_than_or_equal
    comp_type, delta, direction, msg = get_comparator_type_and_direction(
        "hERG_IC50", "greater_than_or_equal", 10.0, 5.0
    )
    assert comp_type == "greater_than_or_equal"
    assert delta == 5.0
    assert direction == "increase"
    assert "hERG_IC50 must be increased by ≥ 5.0 μM" in msg

    # within_range (lower bound violation)
    comp_type, delta, direction, msg = get_comparator_type_and_direction(
        "logP", "within_range", (1.0, 4.0), 0.5
    )
    assert comp_type == "within_range"
    assert delta == 0.5
    assert direction == "increase"
    assert "logP must be increased by ≥ 0.5 units" in msg

    # within_range (upper bound violation)
    comp_type, delta, direction, msg = get_comparator_type_and_direction(
        "logP", "within_range", (1.0, 4.0), 5.2
    )
    assert comp_type == "within_range"
    assert delta == 1.2
    assert direction == "reduce"
    assert "logP must be reduced by ≥ 1.2 units" in msg

    # ratio_greater_than
    comp_type, delta, direction, msg = get_comparator_type_and_direction(
        "beta1_selectivity", "ratio_greater_than", 100.0, 80.0
    )
    assert comp_type == "greater_than_or_equal" or comp_type == "ratio_greater_than"
    assert delta == 20.0
    assert direction == "increase"
    assert "beta1_selectivity must be increased by ≥ 20.0 ratio units" in msg


def test_flat_and_logical_groups_gap_analysis():
    # Nested AND/OR scenario
    # Either logP is <= 4.0 OR hERG_IC50 is >= 10.0
    c1 = Constraint(
        name="logP",
        threshold=4.0,
        comparator=less_than_or_equal,
        rationale="Lipophilicity cap"
    )
    c2 = Constraint(
        name="hERG_IC50",
        threshold=10.0,
        comparator=greater_than_or_equal,
        rationale="Cardiac safety"
    )
    group = ConstraintGroup(
        name="Mitigated Risk",
        op=LogicOp.OR,
        children=[c1, c2],
        rationale="OR alternative path"
    )

    # Let's evaluate a candidate that fails BOTH
    cand = Candidate("bad_candidate", {"logP": 5.2, "hERG_IC50": 5.0})
    report = compute_gap_analysis([group], cand)

    assert report["status"] == "Failed"
    constraints = report["constraints"]
    assert len(constraints) == 1

    grp_report = constraints[0]
    assert grp_report["name"] == "Mitigated Risk"
    assert grp_report["status"] == "Failed"
    assert grp_report["logic"] == "OR"

    children = grp_report["children"]
    assert len(children) == 2
    assert children[0]["name"] == "logP"
    assert children[0]["status"] == "Failed"
    assert children[0]["delta"] == 1.2

    assert children[1]["name"] == "hERG_IC50"
    assert children[1]["status"] == "Failed"
    assert children[1]["delta"] == 5.0


def test_cura_frame_integration():
    c1 = Constraint(
        name="logP",
        threshold=4.0,
        comparator=less_than_or_equal,
        rationale="Lipophilicity cap"
    )
    c2 = Constraint(
        name="hERG_IC50",
        threshold=10.0,
        comparator=greater_than_or_equal,
        rationale="Cardiac safety"
    )
    group = ConstraintGroup(
        name="Mitigated Risk",
        op=LogicOp.OR,
        children=[c1, c2],
        rationale="OR alternative path"
    )

    framework = CuraFrame([group], name="MitigationFramework")

    # 1. Candidate satisfying logP <= 4.0 but NOT hERG (Should pass via OR)
    cand_or_pass = Candidate("or_pass", {"logP": 3.0, "hERG_IC50": 5.0})
    res_pass = framework.evaluate(cand_or_pass)
    assert res_pass.status == EvaluationStatus.ACCEPTED

    # 2. Candidate failing BOTH (Should fail)
    cand_fail = Candidate("or_fail", {"logP": 5.2, "hERG_IC50": 5.0})
    res_fail = framework.evaluate(cand_fail)
    assert res_fail.status == EvaluationStatus.REJECTED
    assert res_fail.gap_analysis is not None

    summary_text = res_fail.summary()
    assert "Logical Failure Diagnostic & Gap Analysis" in summary_text
    assert "logP must be reduced by ≥ 1.2 units." in summary_text
    assert "hERG_IC50 must be increased by ≥ 5.0 μM." in summary_text
