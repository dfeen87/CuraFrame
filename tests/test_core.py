"""
CuraFrame Core Tests

Tests the constraint evaluation engine without involving:
- Molecular generation
- Chemical informatics
- Machine learning
- Clinical decision logic

Tests focus on:
- Constraint satisfaction semantics
- Population stratification
- Error handling
- Auditability
"""

import pytest
from typing import List

from cura_frame import (
    CuraFrame,
    Constraint,
    Candidate,
    EvaluationStatus,
    Severity,
    Provenance,
)
from cura_frame.comparators import (
    less_than_or_equal,
    greater_than_or_equal,
    ratio_greater_than,
    within_range,
)


# -----------------------------
# Fixtures
# -----------------------------

@pytest.fixture
def basic_constraints() -> List[Constraint]:
    """
    Minimal, safety-critical constraint set inspired by CardiAnx-1.
    
    Represents:
    - BBB penetration limit (logP)
    - Cardiac safety (hERG)
    - Receptor selectivity (β1/β2)
    """
    return [
        Constraint(
            name="logP",
            threshold=4.0,
            comparator=less_than_or_equal,
            rationale="Excessive lipophilicity increases safety risk",
            severity=Severity.CRITICAL,
            provenance=Provenance(
                source_type="empirical_guideline",
                confidence=0.9,
                references=["doi:10.x/logp-guideline"]
            )
        ),
        Constraint(
            name="hERG_IC50",
            threshold=10.0,
            comparator=greater_than_or_equal,
            rationale="Low hERG IC50 increases QT prolongation risk",
            severity=Severity.CRITICAL,
            provenance=Provenance(
                source_type="in_vitro_data",
                confidence=0.85,
                references=["doi:10.x/herg-study"]
            )
        ),
        Constraint(
            name="beta1_selectivity",
            threshold=100.0,
            comparator=ratio_greater_than,
            rationale="Insufficient β1/β2 selectivity increases bronchospasm risk",
            severity=Severity.SEVERE,
            provenance=Provenance(
                source_type="pharmacology_literature",
                confidence=0.8,
                references=["doi:10.x/selectivity"]
            )
        ),
    ]


@pytest.fixture
def framework(basic_constraints) -> CuraFrame:
    """Standard CuraFrame instance for testing."""
    return CuraFrame(basic_constraints, name="TestCuraFrame")


@pytest.fixture
def safe_candidate() -> Candidate:
    """A candidate that satisfies all base constraints."""
    return Candidate(
        name="safe_candidate",
        properties={
            "logP": 3.0,
            "hERG_IC50": 20.0,
            "beta1_selectivity": 150.0,
        },
        provenance="test_fixture"
    )


@pytest.fixture
def unsafe_candidate() -> Candidate:
    """A candidate with multiple violations."""
    return Candidate(
        name="unsafe_candidate",
        properties={
            "logP": 6.0,           # CRITICAL violation
            "hERG_IC50": 5.0,      # CRITICAL violation
            "beta1_selectivity": 20.0,  # SEVERE violation
        },
        provenance="test_fixture"
    )


# -----------------------------
# Core acceptance/rejection
# -----------------------------

class TestBasicEvaluation:
    """Tests for fundamental constraint evaluation logic."""
    
    def test_accepts_candidate_when_all_constraints_satisfied(
        self,
        framework: CuraFrame,
        safe_candidate: Candidate
    ):
        """ACCEPTED when all constraints pass."""
        result = framework.evaluate(safe_candidate)

        assert result.status == EvaluationStatus.ACCEPTED
        assert not result.violations
        assert not result.has_critical_violations()
        assert result.candidate_name == "safe_candidate"

    def test_rejects_candidate_on_single_critical_violation(self, framework: CuraFrame):
        """REJECTED when any CRITICAL constraint fails."""
        candidate = Candidate(
            name="high_logP",
            properties={
                "logP": 6.0,           # Violates CRITICAL constraint
                "hERG_IC50": 20.0,
                "beta1_selectivity": 200.0,
            }
        )

        result = framework.evaluate(candidate)

        assert result.status == EvaluationStatus.REJECTED
        assert result.has_critical_violations()
        assert len(result.violations) == 1
        
        violation = result.violations[0]
        assert violation.constraint == "logP"
        assert violation.observed == 6.0
        assert violation.threshold == 4.0
        assert violation.severity == Severity.CRITICAL

    def test_rejects_candidate_on_severe_violation(self, framework: CuraFrame):
        """REJECTED when SEVERE constraint fails (not just CRITICAL)."""
        candidate = Candidate(
            name="low_selectivity",
            properties={
                "logP": 3.0,
                "hERG_IC50": 20.0,
                "beta1_selectivity": 20.0,  # Only 20x selective
            }
        )

        result = framework.evaluate(candidate)

        assert result.status == EvaluationStatus.REJECTED
        assert not result.has_critical_violations()  # No CRITICAL violations
        assert len(result.violations) == 1
        assert result.violations[0].constraint == "beta1_selectivity"

    def test_rejects_candidate_with_multiple_violations(
        self,
        framework: CuraFrame,
        unsafe_candidate: Candidate
    ):
        """All violations are recorded when multiple constraints fail."""
        result = framework.evaluate(unsafe_candidate)

        assert result.status == EvaluationStatus.REJECTED
        assert len(result.violations) == 3
        
        violated_constraints = {v.constraint for v in result.violations}
        assert violated_constraints == {"logP", "hERG_IC50", "beta1_selectivity"}

    def test_violation_includes_full_context(self, framework: CuraFrame):
        """Violations contain all necessary debugging information."""
        candidate = Candidate(
            name="debuggable",
            properties={
                "logP": 5.5,
                "hERG_IC50": 20.0,
                "beta1_selectivity": 150.0,
            }
        )

        result = framework.evaluate(candidate)
        violation = result.violations[0]

        assert violation.constraint == "logP"
        assert violation.observed == 5.5
        assert violation.threshold == 4.0
        assert "safety risk" in violation.rationale.lower()
        assert violation.severity == Severity.CRITICAL
        assert 0.0 <= violation.confidence <= 1.0


# -----------------------------
# Missing data handling
# -----------------------------

class TestMissingData:
    """Tests for handling incomplete candidate data."""
    
    def test_indeterminate_when_required_property_missing_strict_mode(
        self,
        framework: CuraFrame
    ):
        """INDETERMINATE in strict mode when property is missing."""
        candidate = Candidate(
            name="incomplete",
            properties={
                "logP": 3.0,
                # Missing hERG_IC50
                "beta1_selectivity": 150.0,
            }
        )

        result = framework.evaluate(candidate, strict=True)

        assert result.status == EvaluationStatus.INDETERMINATE
        assert result.notes is not None
        assert "Missing required property: hERG_IC50" in result.notes
        assert not result.violations  # No violations, just incomplete

    def test_non_strict_mode_skips_missing_properties(self, framework: CuraFrame):
        """Non-strict mode evaluates available properties, warns on missing."""
        candidate = Candidate(
            name="partial",
            properties={
                "logP": 3.0,
                # Missing hERG_IC50
                "beta1_selectivity": 150.0,
            }
        )

        result = framework.evaluate(candidate, strict=False)

        # Should evaluate available properties
        assert result.status in (EvaluationStatus.ACCEPTED, EvaluationStatus.REJECTED)
        assert result.has_warnings()
        assert any("hERG_IC50" in w and "missing" in w.lower() for w in result.warnings)

    def test_non_strict_mode_still_rejects_on_present_violations(
        self,
        framework: CuraFrame
    ):
        """Non-strict mode still rejects when present properties violate."""
        candidate = Candidate(
            name="partial_unsafe",
            properties={
                "logP": 6.0,  # Violates constraint
                # Missing hERG_IC50 (skipped in non-strict)
                "beta1_selectivity": 150.0,
            }
        )

        result = framework.evaluate(candidate, strict=False)

        assert result.status == EvaluationStatus.REJECTED
        assert any(v.constraint == "logP" for v in result.violations)

    def test_all_properties_missing_non_strict(self, framework: CuraFrame):
        """Non-strict with all properties missing still can't be accepted."""
        candidate = Candidate(
            name="empty",
            properties={}
        )

        result = framework.evaluate(candidate, strict=False)

        # Can't be ACCEPTED if no properties were checked
        assert result.status != EvaluationStatus.ACCEPTED
        assert result.has_warnings()


# -----------------------------
# Population stratification
# -----------------------------

class TestPopulationStratification:
    """Tests for population-specific constraint adjustments."""
    
    def test_population_stratification_tightens_constraints(
        self,
        framework: CuraFrame
    ):
        """Elderly population requires stricter hERG threshold."""
        framework.add_population(
            "elderly",
            {
                "hERG_IC50": lambda c: c.threshold * 1.5  # 10 → 15 μM
            }
        )

        candidate = Candidate(
            name="borderline",
            properties={
                "logP": 3.0,
                "hERG_IC50": 12.0,      # Passes base (≥10), fails elderly (≥15)
                "beta1_selectivity": 150.0,
            }
        )

        general_result = framework.evaluate(candidate)
        elderly_result = framework.evaluate(candidate, population="elderly")

        assert general_result.status == EvaluationStatus.ACCEPTED
        assert elderly_result.status == EvaluationStatus.REJECTED
        assert any(v.constraint == "hERG_IC50" for v in elderly_result.violations)

    def test_multiple_population_modifiers(self, framework: CuraFrame):
        """Population can adjust multiple constraints simultaneously."""
        framework.add_population(
            "asthmatic_elderly",
            {
                "hERG_IC50": lambda c: c.threshold * 1.5,
                "beta1_selectivity": lambda c: c.threshold * 2.0,  # Need 200x
            }
        )

        candidate = Candidate(
            name="dual_borderline",
            properties={
                "logP": 3.0,
                "hERG_IC50": 12.0,
                "beta1_selectivity": 150.0,  # Passes base, fails 200x requirement
            }
        )

        result = framework.evaluate(candidate, population="asthmatic_elderly")

        assert result.status == EvaluationStatus.REJECTED
        assert len(result.violations) == 2
        violated = {v.constraint for v in result.violations}
        assert violated == {"hERG_IC50", "beta1_selectivity"}

    def test_unknown_population_fallback_to_base(self, framework: CuraFrame):
        """Unknown population name falls back to base constraints."""
        candidate = Candidate(
            name="test",
            properties={
                "logP": 3.0,
                "hERG_IC50": 12.0,
                "beta1_selectivity": 150.0,
            }
        )

        result = framework.evaluate(candidate, population="nonexistent")

        # Should use base constraints (no modifier applied)
        assert result.status == EvaluationStatus.ACCEPTED

    def test_population_list_retrieval(self, framework: CuraFrame):
        """Can query registered population names."""
        framework.add_population("elderly", {})
        framework.add_population("pediatric", {})

        populations = framework.population_stratifier.get_populations()

        assert "elderly" in populations
        assert "pediatric" in populations
        assert len(populations) == 2


# -----------------------------
# Provenance and confidence
# -----------------------------

class TestProvenanceTracking:
    """Tests for constraint source tracking and confidence."""
    
    def test_violation_includes_confidence(self, framework: CuraFrame):
        """Violations carry epistemic confidence from constraint provenance."""
        candidate = Candidate(
            name="test",
            properties={
                "logP": 5.0,
                "hERG_IC50": 20.0,
                "beta1_selectivity": 150.0,
            }
        )

        result = framework.evaluate(candidate)
        violation = result.violations[0]

        assert violation.confidence == 0.9  # From logP provenance

    def test_low_confidence_constraint_generates_warning(
        self,
        basic_constraints: List[Constraint]
    ):
        """Low-confidence CRITICAL constraints generate warnings."""
        low_confidence = Constraint(
            name="speculative_property",
            threshold=100.0,
            comparator=less_than_or_equal,
            rationale="Based on preliminary model",
            severity=Severity.CRITICAL,
            provenance=Provenance(
                source_type="QSPR_model",
                confidence=0.5,  # Low confidence
                references=[]
            )
        )
        
        constraints = basic_constraints + [low_confidence]
        framework = CuraFrame(constraints)

        candidate = Candidate(
            name="test",
            properties={
                "logP": 3.0,
                "hERG_IC50": 20.0,
                "beta1_selectivity": 150.0,
                "speculative_property": 150.0,  # Violates low-confidence constraint
            }
        )

        result = framework.evaluate(candidate)

        assert result.has_warnings()
        assert any(
            "moderate-confidence" in w.lower() or "speculative_property" in w
            for w in result.warnings
        )

    def test_constraint_export_includes_provenance(
        self,
        framework: CuraFrame
    ):
        """Exported constraints include full provenance metadata."""
        exported = framework.export_constraints()

        assert "constraints" in exported
        assert len(exported["constraints"]) == 3
        
        logP_constraint = next(
            c for c in exported["constraints"] if c["name"] == "logP"
        )
        
        assert logP_constraint["provenance"]["source"] == "empirical_guideline"
        assert logP_constraint["provenance"]["confidence"] == 0.9
        assert "doi:10.x/logp-guideline" in logP_constraint["provenance"]["references"]


# -----------------------------
# Auditability and history
# -----------------------------

class TestAuditability:
    """Tests for evaluation history and reproducibility."""
    
    def test_evaluation_history_is_recorded(
        self,
        framework: CuraFrame,
        safe_candidate: Candidate
    ):
        """Each evaluation is logged to history."""
        framework.evaluate(safe_candidate)
        framework.evaluate(safe_candidate)

        history = framework.get_history(candidate_name="safe_candidate")

        assert len(history) == 2
        assert all(r.candidate_name == "safe_candidate" for r in history)

    def test_history_contains_full_results(
        self,
        framework: CuraFrame,
        unsafe_candidate: Candidate
    ):
        """History preserves full evaluation results including violations."""
        framework.evaluate(unsafe_candidate)

        history = framework.get_history(candidate_name="unsafe_candidate")
        result = history[0]

        assert result.status == EvaluationStatus.REJECTED
        assert len(result.violations) > 0

    def test_history_filters_by_candidate_name(self, framework: CuraFrame):
        """Can retrieve history for specific candidate."""
        candidate_a = Candidate("A", {"logP": 3.0, "hERG_IC50": 20.0, "beta1_selectivity": 150.0})
        candidate_b = Candidate("B", {"logP": 5.0, "hERG_IC50": 20.0, "beta1_selectivity": 150.0})

        framework.evaluate(candidate_a)
        framework.evaluate(candidate_b)
        framework.evaluate(candidate_a)

        history_a = framework.get_history(candidate_name="A")
        history_b = framework.get_history(candidate_name="B")

        assert len(history_a) == 2
        assert len(history_b) == 1

    def test_history_retrieves_all_when_no_filter(self, framework: CuraFrame):
        """get_history() with no args returns all evaluations."""
        candidate_a = Candidate("A", {"logP": 3.0, "hERG_IC50": 20.0, "beta1_selectivity": 150.0})
        candidate_b = Candidate("B", {"logP": 3.0, "hERG_IC50": 20.0, "beta1_selectivity": 150.0})

        framework.evaluate(candidate_a)
        framework.evaluate(candidate_b)

        all_history = framework.get_history()

        assert len(all_history) == 2


# -----------------------------
# Result summary and display
# -----------------------------

class TestResultSummary:
    """Tests for human-readable result formatting."""
    
    def test_summary_includes_violations(self, framework: CuraFrame):
        """Summary method produces readable violation report."""
        candidate = Candidate(
            name="summary_test",
            properties={
                "logP": 6.0,
                "hERG_IC50": 20.0,
                "beta1_selectivity": 150.0,
            }
        )

        result = framework.evaluate(candidate)
        summary = result.summary()

        assert "REJECTED" in summary
        assert "logP" in summary
        assert "6.0" in summary  # observed value
        assert "4.0" in summary  # threshold

    def test_summary_for_accepted_candidate(
        self,
        framework: CuraFrame,
        safe_candidate: Candidate
    ):
        """Summary for accepted candidate shows success."""
        result = framework.evaluate(safe_candidate)
        summary = result.summary()

        assert "ACCEPTED" in summary
        assert "safe_candidate" in summary

    def test_summary_includes_warnings(self, framework: CuraFrame):
        """Summary displays warnings if present."""
        candidate = Candidate(
            name="partial",
            properties={
                "logP": 3.0,
                "beta1_selectivity": 150.0,
            }
        )

        result = framework.evaluate(candidate, strict=False)
        summary = result.summary()

        assert "Warnings" in summary or "warnings" in summary


# -----------------------------
# Edge cases and error handling
# -----------------------------

class TestEdgeCases:
    """Tests for unusual inputs and error conditions."""
    
    def test_duplicate_constraint_names_raise_error(self, basic_constraints):
        """Cannot initialize with duplicate constraint names."""
        duplicate = Constraint(
            name="logP",  # Duplicate
            threshold=5.0,
            comparator=less_than_or_equal,
            rationale="Duplicate constraint",
            severity=Severity.CRITICAL
        )
        
        with pytest.raises(ValueError, match="Duplicate constraint name"):
            CuraFrame(basic_constraints + [duplicate])

    def test_type_error_during_comparison_returns_indeterminate(
        self,
        framework: CuraFrame
    ):
        """Type mismatch in comparator returns INDETERMINATE."""
        candidate = Candidate(
            name="type_error",
            properties={
                "logP": "not_a_number",  # String instead of float
                "hERG_IC50": 20.0,
                "beta1_selectivity": 150.0,
            }
        )

        result = framework.evaluate(candidate)

        assert result.status == EvaluationStatus.INDETERMINATE
        assert "error" in result.notes.lower()

    def test_constraint_with_no_provenance(self):
        """Constraints work without provenance (defaults to confidence=1.0)."""
        constraint = Constraint(
            name="simple",
            threshold=10.0,
            comparator=greater_than_or_equal,
            rationale="No provenance provided",
            severity=Severity.CRITICAL
            # No provenance
        )
        
        framework = CuraFrame([constraint])
        candidate = Candidate("test", {"simple": 5.0})
        
        result = framework.evaluate(candidate)
        
        assert result.status == EvaluationStatus.REJECTED
        assert result.violations[0].confidence == 1.0  # Default

    def test_empty_candidate_properties(self, framework: CuraFrame):
        """Candidate with no properties handled gracefully."""
        candidate = Candidate(name="empty", properties={})

        result = framework.evaluate(candidate, strict=True)

        assert result.status == EvaluationStatus.INDETERMINATE

    def test_framework_repr(self, framework: CuraFrame):
        """Framework has readable repr."""
        repr_str = repr(framework)

        assert "CuraFrame" in repr_str
        assert "TestCuraFrame" in repr_str
        assert "3" in repr_str  # 3 constraints

    def test_candidate_str(self, safe_candidate: Candidate):
        """Candidate has readable str."""
        str_repr = str(safe_candidate)

        assert "safe_candidate" in str_repr
        assert "logP" in str_repr


# -----------------------------
# Constraint introspection
# -----------------------------

class TestConstraintIntrospection:
    """Tests for querying framework configuration."""
    
    def test_get_constraint_by_name(self, framework: CuraFrame):
        """Can retrieve constraint by name."""
        constraint = framework.get_constraint("logP")

        assert constraint is not None
        assert constraint.name == "logP"
        assert constraint.threshold == 4.0

    def test_get_nonexistent_constraint_returns_none(self, framework: CuraFrame):
        """Requesting unknown constraint returns None."""
        constraint = framework.get_constraint("nonexistent")

        assert constraint is None

    def test_list_all_constraints(self, framework: CuraFrame):
        """Can list all registered constraint names."""
        names = framework.list_constraints()

        assert set(names) == {"logP", "hERG_IC50", "beta1_selectivity"}

    def test_export_constraints_structure(self, framework: CuraFrame):
        """Exported constraints have expected structure."""
        exported = framework.export_constraints()

        assert "framework_name" in exported
        assert "constraints" in exported
        assert "populations" in exported
        assert exported["framework_name"] == "TestCuraFrame"
