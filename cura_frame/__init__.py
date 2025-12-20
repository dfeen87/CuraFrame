"""
CuraFrame

A constraint-driven reasoning framework for safe, systems-level
therapeutic design exploration.

CuraFrame is NOT a drug discovery engine, optimizer, or clinical tool.
It exists to help scientists reason within explicit safety and ethical
boundaries.

See docs/PHILOSOPHY.md and docs/ETHICAL_USE.md for guiding principles.
"""

from .core import (
    CuraFrame,
    Constraint,
    Provenance,
    Candidate,
    EvaluationResult,
    EvaluationStatus,
    Severity,
    Violation,
)

__all__ = [
    "CuraFrame",
    "Constraint",
    "Provenance",
    "Candidate",
    "EvaluationResult",
    "EvaluationStatus",
    "Severity",
    "Violation",
]
