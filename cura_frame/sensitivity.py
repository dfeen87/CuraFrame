# Licensed under the PolyForm Noncommercial License 1.0.0
"""
CuraFrame Sensitivity: Parameter Sweeping and Boundary Mapping.

This module provides tools for mapping the safety boundaries of hypothetical
designs by sweeping properties across specified ranges. This allows scientists
to identify precise falsification thresholds and inflection points under
varying patient population constraints.

It does NOT perform numerical optimization or structural generation. It operates
solely as an analytical tool to explore and visualize the limits of the safety
envelope.
"""

from __future__ import annotations

import copy
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from .core import Candidate, CuraFrame, EvaluationResult, EvaluationStatus

logger = logging.getLogger(__name__)


def run_1d_sweep(
    framework: CuraFrame,
    baseline_candidate: Candidate,
    property_name: str,
    min_val: float,
    max_val: float,
    steps: int = 20,
    population: Optional[str] = None,
    strict: bool = True
) -> List[Dict[str, Any]]:
    """
    Explore the safety envelope of a candidate along a single parameter dimension.

    Iteratively evaluates copies of the baseline candidate, sweeping the specified
    property from min_val to max_val. Generates a list of evaluation results
    to pinpoint exactly where the candidate's safety profile transitions.

    Args:
        framework: The CuraFrame framework containing safety constraints.
        baseline_candidate: The baseline Candidate design.
        property_name: Name of the property to sweep.
        min_val: Minimum sweep value.
        max_val: Maximum sweep value.
        steps: Number of evaluation steps (minimum 1).
        population: Optional population stratification key.
        strict: If True, missing properties -> INDETERMINATE.

    Returns:
        List of dictionaries detailing the sweep outcome at each step.
    """
    if steps < 1:
        raise ValueError("Steps must be at least 1")

    # Create temporary framework to keep evaluation history clean
    temp_framework = CuraFrame(
        safety_constraints=framework.safety_constraints,
        name=f"{framework.name}_temp_sweep"
    )
    for pop_name, pop_mods in framework.population_stratifier.populations.items():
        temp_framework.add_population(pop_name, pop_mods)

    results = []

    for i in range(steps):
        if steps == 1:
            val = min_val
        else:
            val = min_val + (max_val - min_val) * i / (steps - 1)

        # Copy and override the swept property
        properties = dict(baseline_candidate.properties)
        properties[property_name] = val

        cand = Candidate(
            name=f"{baseline_candidate.name}_sweep_{property_name}_{val:.4f}",
            properties=properties,
            provenance=baseline_candidate.provenance,
            uncertainty=baseline_candidate.uncertainty
        )

        eval_res = temp_framework.evaluate(cand, population=population, strict=strict)

        results.append({
            "value": val,
            "status": eval_res.status,
            "violations": [v.constraint for v in eval_res.violations],
            "violations_details": [
                {
                    "constraint": v.constraint,
                    "observed": v.observed,
                    "threshold": v.threshold,
                    "severity": v.severity,
                    "rationale": v.rationale
                }
                for v in eval_res.violations
            ],
            "warnings": eval_res.warnings,
            "notes": eval_res.notes
        })

    return results


def run_2d_sweep(
    framework: CuraFrame,
    baseline_candidate: Candidate,
    prop1: str,
    min1: float,
    max1: float,
    prop2: str,
    min2: float,
    max2: float,
    steps1: int = 10,
    steps2: int = 10,
    population: Optional[str] = None,
    strict: bool = True
) -> List[Dict[str, Any]]:
    """
    Explore the safety envelope of a candidate across a 2D parameter grid.

    Sweeps two properties simultaneously to generate a comprehensive 2D boundary
    map. This is valuable for evaluating synergistic or multi-dimensional
    vulnerabilities in a hypothetical design space.

    Args:
        framework: The CuraFrame framework containing safety constraints.
        baseline_candidate: The baseline Candidate design.
        prop1: Name of the first property.
        min1: Minimum sweep value for prop1.
        max1: Maximum sweep value for prop1.
        prop2: Name of the second property.
        min2: Minimum sweep value for prop2.
        max2: Maximum sweep value for prop2.
        steps1: Number of evaluation steps along prop1.
        steps2: Number of evaluation steps along prop2.
        population: Optional population stratification key.
        strict: If True, missing properties -> INDETERMINATE.

    Returns:
        List of dictionaries detailing the sweep outcome at each grid coordinate.
    """
    if steps1 < 1 or steps2 < 1:
        raise ValueError("Steps must be at least 1")

    temp_framework = CuraFrame(
        safety_constraints=framework.safety_constraints,
        name=f"{framework.name}_temp_sweep_2d"
    )
    for pop_name, pop_mods in framework.population_stratifier.populations.items():
        temp_framework.add_population(pop_name, pop_mods)

    results = []

    for i in range(steps1):
        if steps1 == 1:
            v1 = min1
        else:
            v1 = min1 + (max1 - min1) * i / (steps1 - 1)

        for j in range(steps2):
            if steps2 == 1:
                v2 = min2
            else:
                v2 = min2 + (max2 - min2) * j / (steps2 - 1)

            properties = dict(baseline_candidate.properties)
            properties[prop1] = v1
            properties[prop2] = v2

            cand = Candidate(
                name=f"{baseline_candidate.name}_sweep_{prop1}_{v1:.4f}_{prop2}_{v2:.4f}",
                properties=properties,
                provenance=baseline_candidate.provenance,
                uncertainty=baseline_candidate.uncertainty
            )

            eval_res = temp_framework.evaluate(cand, population=population, strict=strict)

            results.append({
                "value1": v1,
                "value2": v2,
                "status": eval_res.status,
                "violations": [v.constraint for v in eval_res.violations],
                "violations_details": [
                    {
                        "constraint": v.constraint,
                        "observed": v.observed,
                        "threshold": v.threshold,
                        "severity": v.severity,
                        "rationale": v.rationale
                    }
                    for v in eval_res.violations
                ],
                "warnings": eval_res.warnings,
                "notes": eval_res.notes
            })

    return results


def find_inflection_points(sweep_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Analyze 1D sweep results to identify transition points in the safety envelope.

    Identifies exact intervals where the candidate's status changes (e.g., from
    ACCEPTED to REJECTED), detailing the newly triggered or resolved violations.

    Args:
        sweep_results: Output of run_1d_sweep.

    Returns:
        List of dictionaries representing transition intervals.
    """
    if len(sweep_results) < 2:
        return []

    inflections = []
    for i in range(1, len(sweep_results)):
        prev = sweep_results[i - 1]
        curr = sweep_results[i]

        if prev["status"] != curr["status"]:
            inflections.append({
                "index_from": i - 1,
                "index_to": i,
                "value_from": prev["value"],
                "value_to": curr["value"],
                "status_from": prev["status"],
                "status_to": curr["status"],
                "violations_from": prev["violations"],
                "violations_to": curr["violations"]
            })

    return inflections
