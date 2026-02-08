"""
CuraFrame CLI

Lightweight command-line evaluation for constraint bundles against a
JSON-described candidate. This CLI is intentionally conservative and
only evaluates explicit properties provided by the user.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .core import Candidate, CuraFrame, EvaluationResult
from .constraints_library import (
    cardiAnx_dual_domain_constraints,
    cardiology_oriented_constraints,
    cns_drug_constraints,
    core_safety_constraints,
    lipinski_rule_of_five,
)


BUNDLE_REGISTRY = {
    "core-safety": core_safety_constraints,
    "lipinski": lipinski_rule_of_five,
    "cns": cns_drug_constraints,
    "cardiology": cardiology_oriented_constraints,
    "cardianx": cardiAnx_dual_domain_constraints,
}


def available_bundles() -> List[str]:
    """Return a sorted list of available bundle keys."""
    return sorted(BUNDLE_REGISTRY.keys())


def resolve_bundle(bundle_name: str) -> List[Any]:
    """Resolve a bundle name into a list of constraints."""
    try:
        return BUNDLE_REGISTRY[bundle_name]()
    except KeyError as exc:
        options = ", ".join(available_bundles())
        raise ValueError(
            f"Unknown bundle '{bundle_name}'. Available: {options}"
        ) from exc


def load_candidate_from_json(
    path: Path,
    name: Optional[str] = None,
    provenance: Optional[str] = None,
) -> Candidate:
    """Load a Candidate from a JSON file."""
    payload = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(payload, dict):
        raise ValueError("Candidate JSON must be an object")

    if "properties" in payload:
        properties = payload.get("properties")
        candidate_name = payload.get("name") or name or "candidate"
        provenance = payload.get("provenance") or provenance
    else:
        properties = payload
        candidate_name = name or "candidate"

    if not isinstance(properties, dict):
        raise ValueError("Candidate properties must be an object")

    return Candidate(
        name=candidate_name,
        properties=properties,
        provenance=provenance,
    )


def serialize_result(result: EvaluationResult) -> Dict[str, Any]:
    """Convert an EvaluationResult into JSON-serializable data."""
    return {
        "status": result.status.value,
        "candidate": result.candidate_name,
        "notes": result.notes,
        "warnings": result.warnings,
        "violations": [
            {
                "constraint": violation.constraint,
                "observed": violation.observed,
                "threshold": violation.threshold,
                "severity": violation.severity.value,
                "rationale": violation.rationale,
                "confidence": violation.confidence,
            }
            for violation in result.violations
        ],
    }


def format_result_text(result: EvaluationResult) -> str:
    """Format evaluation output for terminal display."""
    return result.summary()


def evaluate_candidate(
    candidate: Candidate,
    bundle_name: str,
    population: Optional[str],
    strict: bool,
) -> EvaluationResult:
    """Evaluate a candidate using a named bundle."""
    framework = CuraFrame(resolve_bundle(bundle_name), name=bundle_name)
    return framework.evaluate(candidate, population=population, strict=strict)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate a candidate JSON against a CuraFrame constraint bundle."
        )
    )
    parser.add_argument(
        "candidate_json",
        type=Path,
        help="Path to candidate JSON file",
    )
    parser.add_argument(
        "--bundle",
        default="core-safety",
        help=(
            "Constraint bundle to use. "
            f"Options: {', '.join(available_bundles())}"
        ),
    )
    parser.add_argument(
        "--candidate-name",
        help="Override candidate name",
    )
    parser.add_argument(
        "--population",
        help="Population context to apply (must be registered by bundle)",
    )
    parser.add_argument(
        "--provenance",
        help="Attach provenance string to candidate",
    )
    parser.add_argument(
        "--no-strict",
        action="store_true",
        help="Skip missing properties instead of returning indeterminate",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format",
    )
    parser.add_argument(
        "--list-bundles",
        action="store_true",
        help="List available bundles and exit",
    )
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.list_bundles:
        print("Available bundles:")
        for bundle in available_bundles():
            print(f"- {bundle}")
        return 0

    candidate = load_candidate_from_json(
        args.candidate_json,
        name=args.candidate_name,
        provenance=args.provenance,
    )

    result = evaluate_candidate(
        candidate=candidate,
        bundle_name=args.bundle,
        population=args.population,
        strict=not args.no_strict,
    )

    if args.format == "json":
        print(json.dumps(serialize_result(result), indent=2))
    else:
        print(format_result_text(result))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
