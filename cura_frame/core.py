# Copyright (c) Don Michael Feeney Jr. Licensed under the MIT License.
"""
CuraFrame Core: Constraint-driven therapeutic design reasoning.

This module provides primitives for expressing and evaluating
safety-critical constraints on hypothetical therapeutic candidates.
It is NOT a drug discovery tool, molecule generator, or optimizer.
"""

from __future__ import annotations

import copy
import logging
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Any, Dict, Generic, List, Optional, Protocol, TypeVar, Union


logger = logging.getLogger(__name__)


# -----------------------------
# Evaluation outcomes
# -----------------------------

class EvaluationStatus(Enum):
    """
    Outcome of constraint evaluation.

    ACCEPTED: All constraints satisfied.
    REJECTED: One or more critical constraints violated.
    INDETERMINATE: Insufficient data to evaluate.
    """
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    INDETERMINATE = "indeterminate"


class Severity(Enum):
    """
    Violation severity levels.

    CRITICAL: Immediate rejection, non-negotiable.
    SEVERE: Likely rejection unless exceptional justification.
    WARNING: Caution advised, not grounds for rejection.
    """
    CRITICAL = "critical"
    SEVERE = "severe"
    WARNING = "warning"


# -----------------------------
# Constraint primitives
# -----------------------------

class LogicOp(Enum):
    """Logical operators for grouping constraints."""
    AND = "AND"
    OR = "OR"


@dataclass
class ConstraintGroup:
    """
    Groups constraints with a logical operator (AND / OR).
    Allows nesting of constraints and alternative evaluation pathways.
    """
    name: str
    op: LogicOp
    children: List[Union[Constraint, ConstraintGroup]]
    rationale: Optional[str] = None
    severity: Severity = Severity.CRITICAL

    def copy(self) -> ConstraintGroup:
        """Recursively copy the constraint group and all its children."""
        return ConstraintGroup(
            name=self.name,
            op=self.op,
            children=[child.copy() for child in self.children],
            rationale=self.rationale,
            severity=self.severity
        )


@dataclass
class Provenance:
    """
    Tracks the source and reliability of a constraint.

    Attributes:
        source_type: Origin of constraint (e.g., 'clinical_data', 'QSPR_model')
        confidence: Epistemic confidence [0.0, 1.0]
        references: Citations, DOIs, or data sources
        last_validated: When this constraint was last verified (optional)
    """
    source_type: str
    confidence: float
    references: List[str] = field(default_factory=list)
    last_validated: Optional[str] = None

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be in [0,1], got {self.confidence}")

    def is_well_established(self, threshold: float = 0.8) -> bool:
        """Conservative: high confidence AND multiple references."""
        return self.confidence >= threshold and len(self.references) >= 3

    def requires_verification(self, threshold: float = 0.6) -> bool:
        """Flag constraints with moderate or low confidence."""
        return self.confidence < threshold


T = TypeVar("T")


@dataclass
class Constraint(Generic[T]):
    """
    Represents a single evaluative boundary.

    Constraints are non-negotiable safety limits unless explicitly
    modified by population stratification. Each constraint carries
    provenance metadata for transparency.

    Attributes:
        name: Unique identifier for this constraint
        threshold: The limiting value (type depends on constraint)
        comparator: Function that evaluates (value, threshold) -> bool
        rationale: Human-readable explanation of why this limit exists
        severity: How serious a violation would be
        provenance: Source and confidence metadata (optional)
    """
    name: str
    threshold: T
    comparator: Callable[[Any, T], bool]
    rationale: str
    severity: Severity = Severity.CRITICAL
    provenance: Optional[Provenance] = None

    def evaluate(self, value: Any) -> bool:
        """
        Returns True if value satisfies constraint, False otherwise.

        Raises:
            TypeError: If value and threshold types are incompatible
        """
        try:
            return self.comparator(value, self.threshold)
        except (TypeError, ValueError) as e:
            logger.error("Constraint %s evaluation failed: %s", self.name, e)
            raise TypeError(
                f"Cannot compare {type(value).__name__} to "
                f"{type(self.threshold).__name__} in constraint '{self.name}'"
            ) from e

    def copy(self) -> "Constraint[T]":
        """Deep copy for population stratification."""
        return Constraint(
            name=self.name,
            threshold=self.threshold,
            comparator=self.comparator,
            rationale=self.rationale,
            severity=self.severity,
            provenance=copy.deepcopy(self.provenance)
        )

    def apply_modifier(self, modifier: Callable[["Constraint[T]"], T]) -> None:
        """
        Apply population-specific adjustment to threshold.

        Example:
            >>> elderly_modifier = lambda c: c.threshold * 1.5  # More conservative
            >>> constraint.apply_modifier(elderly_modifier)
        """
        self.threshold = modifier(self)


# -----------------------------
# Violation representation
# -----------------------------

@dataclass
class Violation:
    """
    Records a constraint violation with full context.

    Attributes:
        constraint: Name of violated constraint
        observed: Actual value from candidate
        threshold: Required threshold
        rationale: Why this constraint exists
        severity: How serious this violation is
        confidence: Epistemic confidence in the constraint itself
    """
    constraint: str
    observed: Any
    threshold: Any
    rationale: str
    severity: Severity
    confidence: float

    def __str__(self) -> str:
        return (
            f"[{self.severity.value.upper()}] {self.constraint}: "
            f"observed {self.observed}, required {self.threshold}\n"
            f"  Rationale: {self.rationale}\n"
            f"  Confidence: {self.confidence:.2f}"
        )


# -----------------------------
# Evaluation result
# -----------------------------

@dataclass
class EvaluationResult:
    """
    Complete outcome of constraint evaluation.

    Attributes:
        status: Overall outcome (ACCEPTED/REJECTED/INDETERMINATE)
        violations: List of constraint violations (if any)
        warnings: Non-critical issues flagged during evaluation
        notes: Additional context or explanations
        candidate_name: Name of evaluated candidate (for logging)
        gap_analysis: Structured logical diagnostic advising on exact gaps (optional)
    """
    status: EvaluationStatus
    violations: List[Violation] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    candidate_name: Optional[str] = None
    gap_analysis: Optional[Dict[str, Any]] = None

    def is_accepted(self) -> bool:
        return self.status == EvaluationStatus.ACCEPTED

    def is_rejected(self) -> bool:
        return self.status == EvaluationStatus.REJECTED

    def is_indeterminate(self) -> bool:
        return self.status == EvaluationStatus.INDETERMINATE

    def has_critical_violations(self) -> bool:
        return any(v.severity == Severity.CRITICAL for v in self.violations)

    def has_warnings(self) -> bool:
        return len(self.warnings) > 0 or any(
            v.severity == Severity.WARNING for v in self.violations
        )

    def summary(self) -> str:
        """Human-readable summary of evaluation."""
        lines = [f"Evaluation: {self.status.value.upper()}"]

        if self.candidate_name:
            lines.append(f"Candidate: {self.candidate_name}")

        if self.violations:
            lines.append(f"\nViolations ({len(self.violations)}):")
            for v in self.violations:
                lines.append(f"  • {v}")

        if self.warnings:
            lines.append(f"\nWarnings ({len(self.warnings)}):")
            for w in self.warnings:
                lines.append(f"  • {w}")

        if self.notes:
            lines.append(f"\nNotes: {self.notes}")

        # Add Logical Failure Diagnostic / Gap Analysis if rejected or failed
        if self.status == EvaluationStatus.REJECTED and self.gap_analysis:
            lines.append("\n==================================================")
            lines.append("Logical Failure Diagnostic & Gap Analysis")
            lines.append("==================================================")
            lines.append("Under current simulation parameters, target constraint boundaries are violated.")
            lines.append("The following scientific parameter adjustments are advised:\n")

            def _format_gap_text_recursive(node: Dict[str, Any], depth: int = 0) -> List[str]:
                output_lines = []
                indent = "  " * depth
                if "logic" in node:
                    # Logical group
                    children = node.get("children", [])
                    failed_children = [c for c in children if c.get("status") == "Failed"]
                    if failed_children:
                        op_str = f" {node['logic']} "
                        child_msgs = []
                        for child in failed_children:
                            for l in _format_gap_text_recursive(child, depth + 1):
                                child_msgs.append(l)

                        # Format list with logical operations
                        for idx, l in enumerate(child_msgs):
                            if idx > 0:
                                output_lines.append(f"{indent}• {node['logic']} {l.strip()}")
                            else:
                                output_lines.append(f"{indent}• {l.strip()}")
                else:
                    # Flat leaf constraint
                    if node.get("status") == "Failed":
                        msg = node.get("message")
                        if msg:
                            output_lines.append(f"{msg}")
                return output_lines

            diagnostic_lines = []
            for item in self.gap_analysis.get("constraints", []):
                diagnostic_lines.extend(_format_gap_text_recursive(item))

            if diagnostic_lines:
                lines.extend(diagnostic_lines)
            else:
                lines.append("• No numeric parameter gaps detected.")
            lines.append("==================================================")

        return "\n".join(lines)


# -----------------------------
# Candidate abstraction
# -----------------------------

class CandidateProtocol(Protocol):
    """Protocol for candidate objects to ensure compatibility."""
    def get(self, property_name: str) -> Any:
        ...


@dataclass
class Candidate:
    """
    Represents a hypothetical design concept.

    All property values are assumed to be predicted, estimated,
    or otherwise uncertain. CuraFrame evaluates whether these
    values satisfy constraints—it does NOT generate or optimize them.

    Attributes:
        name: Human-readable identifier
        properties: Dictionary of property_name -> value
        provenance: How these properties were obtained (optional)
        uncertainty: Property-specific uncertainty bounds (optional)
    """
    name: str
    properties: Dict[str, Any]
    provenance: Optional[str] = None
    uncertainty: Optional[Dict[str, tuple]] = None  # property -> (lower, upper)

    def get(self, property_name: str, default: Any = None) -> Any:
        """
        Retrieve a property value.

        Returns None if property is missing (caller must handle).
        Optionally returns a default value if provided.
        """
        return self.properties.get(property_name, default)

    def has(self, property_name: str) -> bool:
        """Check if property exists."""
        return property_name in self.properties

    def get_with_uncertainty(self, property_name: str) -> tuple:
        """
        Returns (nominal_value, lower_bound, upper_bound).
        If no uncertainty data, returns (value, value, value).
        """
        value = self.get(property_name)
        if value is None:
            raise KeyError(f"Property '{property_name}' not found")

        if self.uncertainty and property_name in self.uncertainty:
            lower, upper = self.uncertainty[property_name]
            return (value, lower, upper)

        return (value, value, value)

    def __str__(self) -> str:
        props = ", ".join(f"{k}={v}" for k, v in self.properties.items())
        return f"Candidate({self.name}: {props})"


# -----------------------------
# Population stratification
# -----------------------------

class PopulationStratification:
    """
    Applies conservative constraint modifiers for patient subgroups.

    Different populations (elderly, pediatric, comorbid conditions)
    may require tighter safety margins. This class manages those
    adjustments in a transparent, traceable way.

    Example:
        >>> strat = PopulationStratification()
        >>> strat.add_population("elderly", {
        ...     "hERG_IC50": lambda c: c.threshold * 1.5,  # More conservative
        ... })
        >>> adjusted = strat.apply("elderly", base_constraints)
    """

    def __init__(self):
        self.populations: Dict[str, Dict[str, Callable[[Constraint], Any]]] = {}

    def add_population(
        self,
        name: str,
        modifiers: Dict[str, Callable[[Constraint], Any]]
    ) -> None:
        """
        Register a population with constraint modifiers.

        Args:
            name: Population identifier (e.g., "elderly", "asthmatic")
            modifiers: Map of constraint_name -> modifier_function
        """
        if name in self.populations:
            logger.warning("Overwriting existing population '%s'", name)
        self.populations[name] = modifiers

    def get_populations(self) -> List[str]:
        """Return list of registered population names."""
        return list(self.populations.keys())

    def apply(
        self,
        population: Optional[str],
        constraints: List[Union[Constraint, ConstraintGroup]]
    ) -> List[Union[Constraint, ConstraintGroup]]:
        """
        Apply population-specific modifiers to constraints or constraint groups.

        Args:
            population: Population name (None = no modifications)
            constraints: Base constraints/groups to modify

        Returns:
            New list of constraints with modifiers applied.
            Original constraints are unchanged (copies are modified).
        """
        if population is None:
            return constraints

        if population not in self.populations:
            logger.warning(
                "Unknown population '%s'. Available: %s",
                population, self.get_populations()
            )
            return constraints

        modifiers = self.populations[population]

        def _apply_recursive(item: Union[Constraint, ConstraintGroup]) -> Union[Constraint, ConstraintGroup]:
            if isinstance(item, Constraint):
                c = item.copy()
                if item.name in modifiers:
                    c.apply_modifier(modifiers[item.name])
                    logger.debug(
                        "Applied %s modifier to %s: %s -> %s",
                        population, item.name, item.threshold, c.threshold
                    )
                return c
            elif isinstance(item, ConstraintGroup):
                g = item.copy()
                g.children = [_apply_recursive(child) for child in g.children]
                return g
            return item

        return [_apply_recursive(item) for item in constraints]


# -----------------------------
# CuraFrame core
# -----------------------------

class CuraFrame:
    """
    Core constraint-reasoning engine for therapeutic design.

    CuraFrame evaluates whether hypothetical candidates satisfy
    safety and design constraints. It does NOT:
    - Generate molecules
    - Optimize properties
    - Make clinical decisions
    - Predict outcomes

    It DOES:
    - Evaluate constraint satisfaction
    - Track provenance and uncertainty
    - Apply population-specific safety margins
    - Reject designs that violate safety limits

    Philosophy:
        Safety constraints precede creativity.
        "This cannot be done safely" is a valid and important answer.
    """

    def __init__(
        self,
        safety_constraints: List[Union[Constraint, ConstraintGroup]],
        name: Optional[str] = None,
        max_history: int = 1000,
    ):
        """
        Initialize CuraFrame with safety constraints.

        Args:
            safety_constraints: List of non-negotiable safety limits or constraint groups
            name: Optional name for this framework instance (for logging)
            max_history: Maximum number of evaluation results to retain in
                history (default: 1000). Older entries are discarded.
        """
        self.name = name or "CuraFrame"
        self.safety_constraints = safety_constraints
        self.population_stratifier = PopulationStratification()
        self.evaluation_history: deque = deque(maxlen=max_history)
        self._constraints_by_name: Dict[str, Constraint] = {}
        self._population_constraints_cache: Dict[Optional[str], List[Union[Constraint, ConstraintGroup]]] = {}

        # Validate constraints at initialization
        self._validate_constraints()

    def _validate_constraints(self) -> None:
        """Ensure all constraints are properly configured."""
        seen_names = set()
        constraints_by_name: Dict[str, Constraint] = {}

        def _validate_recursive(item: Union[Constraint, ConstraintGroup]) -> None:
            if isinstance(item, Constraint):
                if item.name in seen_names:
                    raise ValueError(f"Duplicate constraint name: {item.name}")
                seen_names.add(item.name)
                constraints_by_name[item.name] = item

                # Warn about low-confidence critical constraints
                if item.severity == Severity.CRITICAL:
                    if item.provenance and item.provenance.requires_verification():
                        logger.warning(
                            "CRITICAL constraint '%s' has low confidence (%.2f). "
                            "Consider additional validation.",
                            item.name, item.provenance.confidence
                        )
            elif isinstance(item, ConstraintGroup):
                for child in item.children:
                    _validate_recursive(child)

        for item in self.safety_constraints:
            _validate_recursive(item)

        self._constraints_by_name = constraints_by_name
        self._population_constraints_cache.clear()

    def add_population(
        self,
        name: str,
        modifiers: Dict[str, Callable[[Constraint], Any]]
    ) -> None:
        """
        Register a patient population with constraint modifiers.

        Args:
            name: Population identifier
            modifiers: Constraint adjustments for this population
        """
        self.population_stratifier.add_population(name, modifiers)
        self._population_constraints_cache.clear()

    def _get_constraints_for_population(
        self,
        population: Optional[str]
    ) -> List[Union[Constraint, ConstraintGroup]]:
        if population in self._population_constraints_cache:
            return self._population_constraints_cache[population]

        constraints = self.population_stratifier.apply(
            population,
            self.safety_constraints
        )
        self._population_constraints_cache[population] = constraints
        return constraints

    def evaluate(
        self,
        candidate: Union[Candidate, CandidateProtocol],
        population: Optional[str] = None,
        strict: bool = True
    ) -> EvaluationResult:
        """
        Evaluate a candidate against all applicable constraints.

        Args:
            candidate: Hypothetical design to evaluate
            population: Patient population context (None = general)
            strict: If True, missing properties -> INDETERMINATE.
                   If False, missing properties are skipped with warning.

        Returns:
            EvaluationResult with status and any violations.

        Philosophy:
            - All safety constraints must be satisfied for ACCEPTED.
            - Any critical violation results in REJECTED.
            - Missing data results in INDETERMINATE (unless strict=False).
        """

        # Apply population-specific constraint adjustments
        constraints = self._get_constraints_for_population(population)

        violations: List[Violation] = []
        warnings: List[str] = []
        evaluated_constraints = 0
        missing_constraints = 0
        candidate_name = candidate.name if hasattr(candidate, 'name') else None

        # Recursively evaluate constraints & constraint groups
        def _eval_recursive(item: Union[Constraint, ConstraintGroup]) -> bool:
            nonlocal evaluated_constraints, missing_constraints
            if isinstance(item, Constraint):
                value = candidate.get(item.name)

                # Handle missing data
                if value is None:
                    if strict:
                        raise KeyError(item.name)
                    else:
                        warnings.append(
                            f"Property '{item.name}' missing, constraint skipped"
                        )
                        missing_constraints += 1
                        return True  # Skipped, count as satisfied/passed for this run

                # Evaluate constraint
                try:
                    satisfied = item.evaluate(value)
                except TypeError as e:
                    logger.error("Constraint evaluation failed: %s", e)
                    raise TypeError(f"Constraint evaluation error: {e}") from e
                evaluated_constraints += 1

                # Record violation if constraint not satisfied
                if not satisfied:
                    confidence = (
                        item.provenance.confidence
                        if item.provenance
                        else 1.0
                    )

                    violations.append(
                        Violation(
                            constraint=item.name,
                            observed=value,
                            threshold=item.threshold,
                            rationale=item.rationale,
                            severity=item.severity,
                            confidence=confidence
                        )
                    )

                    # Flag low-confidence violations
                    if item.provenance and not item.provenance.is_well_established():
                        warnings.append(
                            f"Violation of '{item.name}' based on "
                            f"moderate-confidence constraint "
                            f"({item.provenance.confidence:.2f})"
                        )
                return satisfied

            elif isinstance(item, ConstraintGroup):
                if not item.children:
                    return True
                child_results = []
                for child in item.children:
                    child_results.append(_eval_recursive(child))
                if item.op == LogicOp.AND:
                    return all(child_results)
                elif item.op == LogicOp.OR:
                    return any(child_results)
            return True

        try:
            passed = True
            for constraint in constraints:
                if not _eval_recursive(constraint):
                    passed = False
        except KeyError as e:
            missing_prop_name = str(e.args[0])
            result = EvaluationResult(
                status=EvaluationStatus.INDETERMINATE,
                notes=f"Missing required property: {missing_prop_name}",
                candidate_name=candidate_name
            )
            self.evaluation_history.append(result)
            return result
        except TypeError as e:
            result = EvaluationResult(
                status=EvaluationStatus.INDETERMINATE,
                notes=f"Constraint evaluation error: {e}",
                candidate_name=candidate_name
            )
            self.evaluation_history.append(result)
            return result

        # Determine overall status
        if violations:
            # If the top level constraint has groups, passing/failing is governed by the recursive logic structure.
            # However, standard flat constraints are strictly evaluated and failures result in rejection.
            # To be absolutely sure, if we have logic groups, some children violations could be present but the group as a whole might be SATISFIED (via OR).
            # Let's perform a second logic-only pass to check if the top-level constraints/groups are genuinely satisfied.
            def _is_satisfied_recursive(item: Union[Constraint, ConstraintGroup]) -> bool:
                if isinstance(item, Constraint):
                    value = candidate.get(item.name)
                    if value is None:
                        return True # skip/indeterminate handled above
                    try:
                        return item.evaluate(value)
                    except Exception:
                        return False
                elif isinstance(item, ConstraintGroup):
                    if not item.children:
                        return True
                    child_results = [_is_satisfied_recursive(child) for child in item.children]
                    if item.op == LogicOp.AND:
                        return all(child_results)
                    elif item.op == LogicOp.OR:
                        return any(child_results)
                return True

            is_overall_satisfied = all(_is_satisfied_recursive(c) for c in constraints)
            if not is_overall_satisfied:
                status = EvaluationStatus.REJECTED
                notes = f"Failed {len(violations)} constraint(s)"
            else:
                status = EvaluationStatus.ACCEPTED
                notes = "All constraints satisfied (some non-critical/alternative violations ignored via OR logic)"
        elif evaluated_constraints == 0:
            status = EvaluationStatus.INDETERMINATE
            if missing_constraints > 0:
                notes = (
                    f"Skipped {missing_constraints} constraint(s) due to "
                    "missing data"
                )
            else:
                notes = "Insufficient data to evaluate any constraints"
        else:
            status = EvaluationStatus.ACCEPTED
            if missing_constraints > 0:
                notes = (
                    f"Evaluated {evaluated_constraints} constraint(s); "
                    f"skipped {missing_constraints} due to missing data"
                )
            else:
                notes = "All constraints satisfied"

        # Compute structured gap analysis advisor report
        from .advisor import compute_gap_analysis
        gap_report = compute_gap_analysis(constraints, candidate)

        result = EvaluationResult(
            status=status,
            violations=violations,
            warnings=warnings,
            notes=notes,
            candidate_name=candidate_name,
            gap_analysis=gap_report
        )

        self.evaluation_history.append(result)
        return result

    def get_constraint(self, name: str) -> Optional[Constraint]:
        """Retrieve a constraint by name."""
        return self._constraints_by_name.get(name)

    def list_constraints(self) -> List[str]:
        """Return names of all registered constraints."""
        return list(self._constraints_by_name.keys())

    def get_history(self, candidate_name: Optional[str] = None) -> List[EvaluationResult]:
        """
        Retrieve evaluation history.

        Args:
            candidate_name: Filter by candidate name (None = all results)

        Returns:
            List of EvaluationResults.
        """
        if candidate_name is None:
            return list(self.evaluation_history)

        return [
            r for r in self.evaluation_history
            if r.candidate_name == candidate_name
        ]

    def export_constraints(self) -> Dict[str, Any]:
        """
        Export constraints as machine-readable dictionary.

        Useful for documentation, version control, and reproducibility.
        """
        return {
            "framework_name": self.name,
            "constraints": [
                {
                    "name": c.name,
                    "threshold": str(c.threshold),
                    "rationale": c.rationale,
                    "severity": c.severity.value,
                    "provenance": {
                        "source": c.provenance.source_type,
                        "confidence": c.provenance.confidence,
                        "references": c.provenance.references
                    } if c.provenance else None
                }
                for c in self.safety_constraints
            ],
            "populations": self.population_stratifier.get_populations()
        }

    def __repr__(self) -> str:
        return (
            f"CuraFrame(name='{self.name}', "
            f"constraints={len(self.safety_constraints)}, "
            f"populations={len(self.population_stratifier.get_populations())})"
        )
