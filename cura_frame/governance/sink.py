"""Records each evaluation verdict as tamper-evident evidence. Off by default.

CuraFrame already reaches governed decisions -- `EvaluationStatus` is ACCEPTED,
REJECTED or INDETERMINATE, violations carry a severity, and every constraint
carries `Provenance` with an epistemic confidence. What it does not do is keep
them: an `EvaluationResult` is returned, appended to an in-memory list, and that
is the end of it.

This writes each one to a hash-chained ledger, and it carries the diagnostic
rather than a summary of it. The README promises that *every rejection includes
full diagnostic information*, and an earlier draft of this file recorded
`violations: 2` -- dropping the six-field `Violation` objects, the gap analysis
the engine had already computed, and the literature references behind every
constraint. A rejection record without the rejection criteria erases the thing
this repository exists to produce.

Three rules constrain it:

1. **It never changes an evaluation outcome.** This layer is about whether
   evidence exists and holds together. It has no opinion on whether a
   pharmacological constraint is correct, and must not be able to turn a
   REJECTED into an ACCEPTED or the reverse.

2. **It never raises into the evaluation path.** A recorder that breaks the
   science is worse than no recorder. Every failure degrades to silence, and
   `last_error()` says why.

3. **It is off unless asked for.** Without `CURAFRAME_LEDGER_ROOT` in the
   environment nothing is imported, nothing is written, and nothing is slower.

Enable it by pointing the variable at a repository that has declared a contract:

    export CURAFRAME_LEDGER_ROOT="$PWD"
    python -m cura_frame.cli ...
"""

from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any, Iterable, Optional

ENV_ROOT = "CURAFRAME_LEDGER_ROOT"

#: Used only when a `Provenance` object cannot answer `requires_verification()`
#: itself, so a malformed provenance degrades to a flag rather than an exception
#: (rule 2). `cura_frame.core` owns the real default.
_VERIFICATION_FLOOR = 0.6

_lock = threading.Lock()
_state: dict[str, Any] = {"resolved": False, "root": None, "last_error": None}


def _root() -> Optional[Path]:
    """The ledger root, or None when recording is switched off. Never raises."""
    with _lock:
        if _state["resolved"]:
            return _state["root"]
        _state["resolved"] = True

        raw = os.environ.get(ENV_ROOT, "").strip()
        if not raw:
            return None

        root = Path(raw).expanduser()
        from . import ledger

        if not ledger.contract_path(root).is_file():
            _state["last_error"] = (
                f"no verdict contract at {ledger.contract_path(root)}; "
                f"nothing will be recorded"
            )
            return None

        _state["root"] = root
        return root


def enabled() -> bool:
    return _root() is not None


def last_error() -> Optional[str]:
    """Why nothing is being recorded, when nothing is being recorded."""
    _root()
    return _state["last_error"]


def status() -> dict[str, Any]:
    """For diagnostics and for the test suite."""
    root = _root()
    return {
        "enabled": root is not None,
        "root": str(root) if root else None,
        "last_error": _state["last_error"],
    }


def reset() -> None:
    """Drop the cached resolution. Used by tests that change the environment."""
    with _lock:
        _state.update({"resolved": False, "root": None, "last_error": None})


# ── shaping the record ───────────────────────────────────────────────────────


def _plain(value: Any) -> Any:
    """JSON-safe without losing the value a reviewer needs to read."""
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _leaves(item: Any) -> Iterable[Any]:
    """Yield leaf constraints, descending through logic groups."""
    children = getattr(item, "constraints", None) or getattr(item, "children", None)
    if children:
        for child in children:
            yield from _leaves(child)
    else:
        yield item


def violations(result: Any) -> list[dict[str, Any]]:
    """Every field a `Violation` defines -- where and why a design failed."""
    rows = []
    for violation in getattr(result, "violations", ()) or ():
        rows.append(
            {
                "constraint": str(getattr(violation, "constraint", "")),
                "observed": _plain(getattr(violation, "observed", None)),
                "threshold": _plain(getattr(violation, "threshold", None)),
                "rationale": str(getattr(violation, "rationale", "")),
                "severity": getattr(getattr(violation, "severity", None), "name", ""),
                "confidence": float(getattr(violation, "confidence", 0.0) or 0.0),
            }
        )
    return rows


def provenance(constraints: Iterable[Any]) -> list[dict[str, Any]]:
    """Source, confidence and references, per constraint.

    Constraints are first-class scientific objects here, and the references are
    a constraint's standing in the literature. A record that drops them records
    a verdict with no basis.
    """
    rows = []
    for constraint in constraints or ():
        for item in _leaves(constraint):
            source = getattr(item, "provenance", None)
            if source is None:
                continue
            try:
                needs_check = bool(source.requires_verification())
            except Exception:  # noqa: BLE001 - rule 2
                needs_check = float(getattr(source, "confidence", 1.0)) < _VERIFICATION_FLOOR
            rows.append(
                {
                    "constraint": str(getattr(item, "name", "")),
                    "source_type": str(getattr(source, "source_type", "")),
                    "confidence": float(getattr(source, "confidence", 0.0) or 0.0),
                    "references": [str(r) for r in getattr(source, "references", []) or []],
                    "requires_verification": needs_check,
                }
            )
    return rows


def build_record(result: Any, constraints: Iterable[Any] = ()) -> dict[str, Any]:
    """The verdict as it will be recorded. Separated so tests can read it."""
    status_value = getattr(getattr(result, "status", None), "value", None) or str(
        getattr(result, "status", "unknown")
    )
    record: dict[str, Any] = {
        "candidate": getattr(result, "candidate_name", None) or "unnamed",
        "status": status_value,
        "violations": violations(result),
        "provenance": provenance(constraints),
    }
    # An INDETERMINATE result names the property that was missing. Recording
    # only the status would hide the epistemic gap it exists to report.
    notes = getattr(result, "notes", None)
    if notes:
        record["notes"] = str(notes)
    gap = getattr(result, "gap_analysis", None)
    if isinstance(gap, dict):
        record["gap_analysis"] = gap
    return record


# ── recording ────────────────────────────────────────────────────────────────


def record(result: Any, constraints: Iterable[Any] = ()) -> Optional[dict[str, Any]]:
    """Append one chained row carrying the full diagnostic. Never raises."""
    root = _root()
    if root is None:
        return None
    try:
        from . import ledger

        return ledger.append(root, build_record(result, constraints))
    except Exception as exc:  # noqa: BLE001 - rule 2
        _state["last_error"] = f"{type(exc).__name__}: {exc}"
        return None


def verify(root: Optional[Path] = None) -> list[str]:
    """Check the chain and re-check every record against the declared contract."""
    target = Path(root) if root else _root()
    if target is None:
        return []
    try:
        from . import ledger

        return ledger.validate(target)
    except Exception as exc:  # noqa: BLE001 - rule 2
        _state["last_error"] = f"{type(exc).__name__}: {exc}"
        return [f"{type(exc).__name__}: {exc}"]
