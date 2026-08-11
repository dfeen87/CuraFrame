# Copyright (c) Don Michael Feeney Jr. Licensed under the MIT License.
"""
CuraFrame Gap Analysis Advisor

Analyzes failed constraints to determine exact numeric parameter gaps
and construct structured, logical diagnostic advisories.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from .core import Constraint, ConstraintGroup, LogicOp, Candidate, CandidateProtocol

logger = logging.getLogger(__name__)


def get_unit_by_name(name: str) -> str:
    """Map common parameter names to their scientific units."""
    name_lower = name.lower()
    if "herg" in name_lower or "cyp3a4" in name_lower:
        return "μM"
    elif "kd" in name_lower:
        return "nM"
    elif "weight" in name_lower or "mw" in name_lower:
        return "Da"
    elif "clearance" in name_lower:
        return "mL/min/kg"
    elif "half_life" in name_lower or "t_half" in name_lower:
        return "hours"
    elif "bioavailability" in name_lower:
        return "%"
    elif "solubility" in name_lower:
        return "μg/mL"
    elif "binding" in name_lower:
        return "%"
    elif "area" in name_lower or "psa" in name_lower:
        return "Å²"
    elif "selectivity" in name_lower:
        return "ratio units"
    return "units"


def get_comparator_type_and_direction(
    constraint_name: str,
    comparator_name: str,
    threshold: Any,
    observed: Any
) -> Tuple[Optional[str], Optional[float], Optional[str], Optional[str]]:
    """
    Analyzes the comparator and calculates:
      - comparator_type: 'less_than_or_equal', 'greater_than_or_equal', 'within_range', etc.
      - delta: exact gap value or None
      - direction: 'reduce' | 'increase' | None
      - message: Precise, scientific guidance advisory message
    """
    comp_lower = comparator_name.lower()
    unit = get_unit_by_name(constraint_name)

    # 1. less_than_or_equal / less_than / significantly_less_than
    if "less_than" in comp_lower or "less" in comp_lower:
        if isinstance(threshold, (int, float)) and isinstance(observed, (int, float)):
            if observed > threshold:
                delta = round(observed - threshold, 4)
                msg = f"{constraint_name} must be reduced by ≥ {delta} {unit}."
                return ("less_than_or_equal", delta, "reduce", msg)
            return ("less_than_or_equal", 0.0, None, None)

    # 2. greater_than_or_equal / greater_than / significantly_greater_than / ratio_greater_than
    elif "greater_than" in comp_lower or "greater" in comp_lower or "ratio_greater_than" in comp_lower:
        if isinstance(threshold, (int, float)) and isinstance(observed, (int, float)):
            if observed < threshold:
                delta = round(threshold - observed, 4)
                msg = f"{constraint_name} must be increased by ≥ {delta} {unit}."
                return ("greater_than_or_equal", delta, "increase", msg)
            return ("greater_than_or_equal", 0.0, None, None)

    # 3. within_range
    elif "within_range" in comp_lower:
        if isinstance(threshold, tuple) and len(threshold) == 2:
            lower, upper = threshold
            if isinstance(observed, (int, float)):
                if observed < lower:
                    delta = round(lower - observed, 4)
                    msg = f"{constraint_name} must be increased by ≥ {delta} {unit}."
                    return ("within_range", delta, "increase", msg)
                elif observed > upper:
                    delta = round(observed - upper, 4)
                    msg = f"{constraint_name} must be reduced by ≥ {delta} {unit}."
                    return ("within_range", delta, "reduce", msg)
                return ("within_range", 0.0, None, None)

    return (None, None, None, None)


def compute_gap_analysis(
    constraints: List[Union[Constraint, ConstraintGroup]],
    candidate: Union[Candidate, CandidateProtocol]
) -> Dict[str, Any]:
    """
    Constructs a structured, nested JSON-serializable report advising on exact parameter gaps.
    """
    def _analyze_recursive(item: Union[Constraint, ConstraintGroup]) -> Dict[str, Any]:
        if isinstance(item, Constraint):
            observed = candidate.get(item.name)
            if observed is None:
                return {
                    "id": item.name,
                    "name": item.name,
                    "status": "Indeterminate",
                    "reason": "Missing required property"
                }

            try:
                satisfied = item.evaluate(observed)
            except Exception:
                satisfied = False

            comp_name = item.comparator.__name__ if hasattr(item.comparator, "__name__") else str(item.comparator)
            comp_type, delta, direction, msg = get_comparator_type_and_direction(
                item.name, comp_name, item.threshold, observed
            )

            if satisfied:
                return {
                    "id": item.name,
                    "name": item.name,
                    "status": "Passed",
                    "comparator": comp_type or comp_name,
                    "threshold": item.threshold,
                    "observed": observed
                }
            else:
                return {
                    "id": item.name,
                    "name": item.name,
                    "status": "Failed",
                    "comparator": comp_type or comp_name,
                    "threshold": item.threshold,
                    "observed": observed,
                    "delta": delta,
                    "direction": direction,
                    "message": msg or f"{item.name} violates target constraints."
                }

        elif isinstance(item, ConstraintGroup):
            children_reports = [_analyze_recursive(child) for child in item.children]

            # Determine status of the group based on children statuses
            passed_count = sum(1 for c in children_reports if c.get("status") == "Passed")
            failed_count = sum(1 for c in children_reports if c.get("status") == "Failed")
            indeterminate_count = sum(1 for c in children_reports if c.get("status") == "Indeterminate")

            if item.op == LogicOp.AND:
                if passed_count == len(children_reports):
                    status = "Passed"
                elif indeterminate_count > 0:
                    status = "Indeterminate"
                else:
                    status = "Failed"
            else: # OR
                if passed_count > 0:
                    status = "Passed"
                elif failed_count == len(children_reports):
                    status = "Failed"
                else:
                    status = "Indeterminate"

            report = {
                "id": item.name,
                "name": item.name,
                "status": status,
                "logic": item.op.value,
                "children": children_reports
            }
            return report

    root_children = [_analyze_recursive(item) for item in constraints]
    # Root acts as an implicit AND bundle
    passed_count = sum(1 for c in root_children if c.get("status") == "Passed")
    failed_count = sum(1 for c in root_children if c.get("status") == "Failed")
    indeterminate_count = sum(1 for c in root_children if c.get("status") == "Indeterminate")

    if passed_count == len(root_children):
        status = "Passed"
    elif indeterminate_count > 0:
        status = "Indeterminate"
    else:
        status = "Failed"

    return {
        "status": status,
        "logic": "AND",
        "constraints": root_children
    }
