# Licensed under the PolyForm Noncommercial License 1.0.0
"""
CuraFrame Simulation Tests

Validates that the framework produces the expected accept/reject outcome
for each named simulation candidate JSON file under simulations/candidates/.

These tests serve as a reliability check: if the framework correctly
classifies every pre-labelled candidate, the constraint engine is working
as expected end-to-end, from JSON loading through constraint evaluation.
"""

from pathlib import Path
import pytest

from cura_frame.cli import evaluate_candidate, load_candidate_from_json
from cura_frame.core import EvaluationStatus

# Root of the simulations/candidates directory
_CANDIDATES_DIR = Path(__file__).parent.parent / "simulations" / "candidates"


def _load_and_evaluate(filename: str, bundle: str) -> EvaluationStatus:
    """Load a candidate JSON and evaluate it against the given bundle."""
    candidate = load_candidate_from_json(_CANDIDATES_DIR / filename)
    result = evaluate_candidate(
        candidate=candidate,
        bundle_name=bundle,
        population=None,
        strict=True,
    )
    return result.status


# ---------------------------------------------------------------------------
# core-safety bundle
# ---------------------------------------------------------------------------

class TestCoreSafetySimulation:
    def test_core_safety_accepted_candidate(self):
        """core_safety_accepted.json must be ACCEPTED by the core-safety bundle."""
        status = _load_and_evaluate("core_safety_accepted.json", "core-safety")
        assert status == EvaluationStatus.ACCEPTED

    def test_core_safety_rejected_candidate(self):
        """core_safety_rejected.json must be REJECTED by the core-safety bundle."""
        status = _load_and_evaluate("core_safety_rejected.json", "core-safety")
        assert status == EvaluationStatus.REJECTED


# ---------------------------------------------------------------------------
# lipinski bundle
# ---------------------------------------------------------------------------

class TestLipinskiSimulation:
    def test_lipinski_accepted_candidate(self):
        """lipinski_accepted.json must be ACCEPTED by the lipinski bundle."""
        status = _load_and_evaluate("lipinski_accepted.json", "lipinski")
        assert status == EvaluationStatus.ACCEPTED

    def test_lipinski_rejected_candidate(self):
        """lipinski_rejected.json must be REJECTED by the lipinski bundle."""
        status = _load_and_evaluate("lipinski_rejected.json", "lipinski")
        assert status == EvaluationStatus.REJECTED


# ---------------------------------------------------------------------------
# cns bundle
# ---------------------------------------------------------------------------

class TestCnsSimulation:
    def test_cns_accepted_candidate(self):
        """cns_accepted.json must be ACCEPTED by the cns bundle."""
        status = _load_and_evaluate("cns_accepted.json", "cns")
        assert status == EvaluationStatus.ACCEPTED

    def test_cns_rejected_candidate(self):
        """cns_rejected.json must be REJECTED by the cns bundle."""
        status = _load_and_evaluate("cns_rejected.json", "cns")
        assert status == EvaluationStatus.REJECTED


# ---------------------------------------------------------------------------
# cardiology bundle
# ---------------------------------------------------------------------------

class TestCardiologySimulation:
    def test_cardiology_accepted_candidate(self):
        """cardiology_accepted.json must be ACCEPTED by the cardiology bundle."""
        status = _load_and_evaluate("cardiology_accepted.json", "cardiology")
        assert status == EvaluationStatus.ACCEPTED

    def test_cardiology_rejected_candidate(self):
        """cardiology_rejected.json must be REJECTED by the cardiology bundle."""
        status = _load_and_evaluate("cardiology_rejected.json", "cardiology")
        assert status == EvaluationStatus.REJECTED


# ---------------------------------------------------------------------------
# cardianx bundle
# ---------------------------------------------------------------------------

class TestCardianxSimulation:
    def test_cardianx_accepted_candidate(self):
        """cardianx_accepted.json must be ACCEPTED by the cardianx bundle."""
        status = _load_and_evaluate("cardianx_accepted.json", "cardianx")
        assert status == EvaluationStatus.ACCEPTED

    def test_cardianx_rejected_candidate(self):
        """cardianx_rejected.json must be REJECTED by the cardianx bundle."""
        status = _load_and_evaluate("cardianx_rejected.json", "cardianx")
        assert status == EvaluationStatus.REJECTED


# ---------------------------------------------------------------------------
# oncology bundle
# ---------------------------------------------------------------------------

class TestOncologySimulation:
    def test_oncology_accepted_candidate(self):
        """oncology_accepted.json must be ACCEPTED by the oncology bundle."""
        status = _load_and_evaluate("oncology_accepted.json", "oncology")
        assert status == EvaluationStatus.ACCEPTED

    def test_oncology_rejected_candidate(self):
        """oncology_rejected.json must be REJECTED by the oncology bundle."""
        status = _load_and_evaluate("oncology_rejected.json", "oncology")
        assert status == EvaluationStatus.REJECTED


# ---------------------------------------------------------------------------
# anti-infective bundle
# ---------------------------------------------------------------------------

class TestAntiInfectiveSimulation:
    def test_anti_infective_accepted_candidate(self):
        """anti_infective_accepted.json must be ACCEPTED by the anti-infective bundle."""
        status = _load_and_evaluate("anti_infective_accepted.json", "anti-infective")
        assert status == EvaluationStatus.ACCEPTED

    def test_anti_infective_rejected_candidate(self):
        """anti_infective_rejected.json must be REJECTED by the anti-infective bundle."""
        status = _load_and_evaluate("anti_infective_rejected.json", "anti-infective")
        assert status == EvaluationStatus.REJECTED


# ---------------------------------------------------------------------------
# metabolic-disease bundle
# ---------------------------------------------------------------------------

class TestMetabolicDiseaseSimulation:
    def test_metabolic_disease_accepted_candidate(self):
        """metabolic_disease_accepted.json must be ACCEPTED by the metabolic-disease bundle."""
        status = _load_and_evaluate("metabolic_disease_accepted.json", "metabolic-disease")
        assert status == EvaluationStatus.ACCEPTED

    def test_metabolic_disease_rejected_candidate(self):
        """metabolic_disease_rejected.json must be REJECTED by the metabolic-disease bundle."""
        status = _load_and_evaluate("metabolic_disease_rejected.json", "metabolic-disease")
        assert status == EvaluationStatus.REJECTED
