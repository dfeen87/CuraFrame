"""
CuraFrame Core: Constraint-driven therapeutic design reasoning.

This module provides primitives for expressing and evaluating
safety-critical constraints on hypothetical therapeutic candidates.
It is NOT a drug discovery tool, molecule generator, or optimizer.
"""

from dataclasses import dataclass, field
from typing import Callable, Any, Dict, List, Optional, Protocol, Union
from enum import Enum
import logging
from abc import ABC, abstractmethod


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


@dataclass
class Constraint:
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
    threshold: Any
    comparator: Callable[[Any, Any], bool]
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
            logger.error(f"Constraint {self.name} evaluation failed: {e}")
            raise TypeError(
                f"Cannot compare {type(value).__name__} to "
                f"{type(self.threshold).__name__} in constraint '{self.name}'"
            ) from e

    def copy(self) -> "Constraint":
        """Deep copy for population stratification."""
        return Constraint(
            name=self.name,
            threshold=self.threshold,
            comparator=self.comparator,
            rationale=self.rationale,
            severity=self.severity,
            provenance=self.provenance
        )

    def apply_modifier(self, modifier: Callable[["Constraint"], Any]) -> None:
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
    """
    status: EvaluationStatus
    violations: List[Violation] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    candidate_name: Optional[str] = None

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
            logger.warning(f"Overwriting existing population '{name}'")
        self.populations[name] = modifiers

    def get_populations(self) -> List[str]:
        """Return list of registered population names."""
        return list(self.populations.keys())

    def apply(
        self, 
        population: Optional[str], 
        constraints: List[Constraint]
    ) -> List[Constraint]:
        """
        Apply population-specific modifiers to constraints.
        
        Args:
            population: Population name (None = no modifications)
            constraints: Base constraints to modify
        
        Returns:
            New list of constraints with modifiers applied.
            Original constraints are unchanged (copies are modified).
        """
        if population is None:
            return constraints
        
        if population not in self.populations:
            logger.warning(
                f"Unknown population '{population}'. "
                f"Available: {self.get_populations()}"
            )
            return constraints

        adjusted = []
        modifiers = self.populations[population]

        for constraint in constraints:
            if constraint.name in modifiers:
                c = constraint.copy()
                c.apply_modifier(modifiers[constraint.name])
                adjusted.append(c)
                logger.debug(
                    f"Applied {population} modifier to {constraint.name}: "
                    f"{constraint.threshold} -> {c.threshold}"
                )
            else:
                adjusted.append(constraint)

        return adjusted


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
        safety_constraints: List[Constraint],
        name: Optional[str] = None
    ):
        """
        Initialize CuraFrame with safety constraints.
        
        Args:
            safety_constraints: List of non-negotiable safety limits
            name: Optional name for this framework instance (for logging)
        """
        self.name = name or "CuraFrame"
        self.safety_constraints = safety_constraints
        self.population_stratifier = PopulationStratification()
        self.evaluation_history: List[EvaluationResult] = []
        
        # Validate constraints at initialization
        self._validate_constraints()
    
    def _validate_constraints(self) -> None:
        """Ensure all constraints are properly configured."""
        seen_names = set()
        for constraint in self.safety_constraints:
            if constraint.name in seen_names:
                raise ValueError(f"Duplicate constraint name: {constraint.name}")
            seen_names.add(constraint.name)
            
            # Warn about low-confidence critical constraints
            if constraint.severity == Severity.CRITICAL:
                if constraint.provenance and constraint.provenance.requires_verification():
                    logger.warning(
                        f"CRITICAL constraint '{constraint.name}' has "
                        f"low confidence ({constraint.provenance.confidence:.2f}). "
                        "Consider additional validation."
                    )

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
        constraints = self.population_stratifier.apply(
            population,
            self.safety_constraints
        )

        violations: List[Violation] = []
        warnings: List[str] = []
        candidate_name = candidate.name if hasattr(candidate, 'name') else None

        # Evaluate each constraint
        for constraint in constraints:
            value = candidate.get(constraint.name)

            # Handle missing data
            if value is None:
                if strict:
                    result = EvaluationResult(
                        status=EvaluationStatus.INDETERMINATE,
                        notes=f"Missing required property: {constraint.name}",
                        candidate_name=candidate_name
                    )
                    self.evaluation_history.append(result)
                    return result
                else:
                    warnings.append(
                        f"Property '{constraint.name}' missing, constraint skipped"
                    )
                    continue

            # Evaluate constraint
            try:
                satisfied = constraint.evaluate(value)
            except TypeError as e:
                logger.error(f"Constraint evaluation failed: {e}")
                result = EvaluationResult(
                    status=EvaluationStatus.INDETERMINATE,
                    notes=f"Constraint evaluation error: {e}",
                    candidate_name=candidate_name
                )
                self.evaluation_history.append(result)
                return result

            # Record violation if constraint not satisfied
            if not satisfied:
                confidence = (
                    constraint.provenance.confidence 
                    if constraint.provenance 
                    else 1.0
                )
                
                violations.append(
                    Violation(
                        constraint=constraint.name,
                        observed=value,
                        threshold=constraint.threshold,
                        rationale=constraint.rationale,
                        severity=constraint.severity,
                        confidence=confidence
                    )
                )
                
                # Flag low-confidence violations
                if constraint.provenance and not constraint.provenance.is_well_established():
                    warnings.append(
                        f"Violation of '{constraint.name}' based on "
                        f"moderate-confidence constraint "
                        f"({constraint.provenance.confidence:.2f})"
                    )

        # Determine overall status
        if violations:
            status = EvaluationStatus.REJECTED
            notes = f"Failed {len(violations)} constraint(s)"
        else:
            status = EvaluationStatus.ACCEPTED
            notes = "All constraints satisfied"

        result = EvaluationResult(
            status=status,
            violations=violations,
            warnings=warnings,
            notes=notes,
            candidate_name=candidate_name
        )

        self.evaluation_history.append(result)
        return result

    def get_constraint(self, name: str) -> Optional[Constraint]:
        """Retrieve a constraint by name."""
        for c in self.safety_constraints:
            if c.name == name:
                return c
        return None

    def list_constraints(self) -> List[str]:
        """Return names of all registered constraints."""
        return [c.name for c in self.safety_constraints]

    def get_history(self, candidate_name: Optional[str] = None) -> List[EvaluationResult]:
        """
        Retrieve evaluation history.
        
        Args:
            candidate_name: Filter by candidate name (None = all results)
        
        Returns:
            List of EvaluationResults.
        """
        if candidate_name is None:
            return self.evaluation_history
        
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
