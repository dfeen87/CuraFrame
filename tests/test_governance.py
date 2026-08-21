"""The recorder must never change what an evaluation decided, and the ledger
must not report a clean chain over a file that has been tampered with.

Three rules make the recorder safe to leave in place: it is off by default, it
cannot alter a result, and it cannot raise into the evaluation path. Each is a
test here rather than a claim in a docstring.

The integrity tests exist because the lenient version of `read()` returned the
rows it had managed to parse and said nothing, so `validate()` answered "clean"
for a ledger truncated to a third of itself. Detecting exactly that is the only
reason the chain is worth having.
"""

from __future__ import annotations

import json
import operator
import threading
from pathlib import Path

import pytest

from cura_frame import governance
from cura_frame.core import (
    Candidate,
    Constraint,
    CuraFrame,
    EvaluationStatus,
    Provenance,
    Severity,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads(
    (REPO_ROOT / ".curaframe" / "verdicts.schema.json").read_text(encoding="utf-8")
)

WELL_SOURCED = 0.92
BELOW_FLOOR = 0.45  # Provenance.requires_verification() default floor is 0.6


@pytest.fixture(autouse=True)
def _reset():
    governance.reset()
    yield
    governance.reset()


@pytest.fixture()
def ledger_root(tmp_path: Path, monkeypatch) -> Path:
    """A repository that has declared a contract and switched recording on."""
    governance.declare(tmp_path, CONTRACT)
    monkeypatch.setenv(governance.ENV_ROOT, str(tmp_path))
    governance.reset()
    return tmp_path


def _rows(root: Path) -> list[dict]:
    return governance.read(root)


def _frame() -> CuraFrame:
    solid = Constraint(
        name="hERG_IC50_uM",
        threshold=10.0,
        comparator=operator.ge,
        rationale="Cardiac safety margin",
        severity=Severity.CRITICAL,
        provenance=Provenance(
            source_type="clinical_data",
            confidence=WELL_SOURCED,
            references=["doi:1", "doi:2", "doi:3"],
        ),
    )
    weak = Constraint(
        name="CYP3A4_inhibition_pct",
        threshold=50.0,
        comparator=operator.le,
        rationale="DDI risk",
        severity=Severity.WARNING,
        provenance=Provenance(
            source_type="QSPR_model", confidence=BELOW_FLOOR, references=["doi:4"]
        ),
    )
    return CuraFrame(safety_constraints=[solid, weak], name="test-frame")


def _passing() -> Candidate:
    return Candidate(
        name="CAND-PASS",
        properties={"hERG_IC50_uM": 40.0, "CYP3A4_inhibition_pct": 10.0},
    )


def _failing() -> Candidate:
    return Candidate(
        name="CAND-FAIL",
        properties={"hERG_IC50_uM": 2.0, "CYP3A4_inhibition_pct": 90.0},
    )


# ── the three rules ──────────────────────────────────────────────────────────


def test_recording_is_off_without_the_environment_variable(monkeypatch):
    monkeypatch.delenv(governance.ENV_ROOT, raising=False)
    assert governance.enabled() is False
    assert governance.record(object()) is None


def test_a_verdict_is_the_same_whether_recording_is_on_or_off(monkeypatch, ledger_root):
    """Rule 1: this layer governs evidence, not pharmacology."""
    monkeypatch.delenv(governance.ENV_ROOT, raising=False)
    governance.reset()
    off_pass = _frame().evaluate(_passing())
    off_fail = _frame().evaluate(_failing())

    monkeypatch.setenv(governance.ENV_ROOT, str(ledger_root))
    governance.reset()
    on_pass = _frame().evaluate(_passing())
    on_fail = _frame().evaluate(_failing())

    assert on_pass.status == off_pass.status == EvaluationStatus.ACCEPTED
    assert on_fail.status == off_fail.status == EvaluationStatus.REJECTED
    assert len(on_fail.violations) == len(off_fail.violations)


def test_a_broken_recorder_does_not_break_evaluation(monkeypatch, tmp_path):
    """Rule 2: a recorder that breaks the science is worse than none."""
    monkeypatch.setenv(governance.ENV_ROOT, str(tmp_path / "nowhere"))
    governance.reset()

    result = _frame().evaluate(_failing())

    assert result.status == EvaluationStatus.REJECTED
    assert governance.enabled() is False
    assert "no verdict contract" in (governance.last_error() or "")


def test_history_is_still_kept_when_recording_is_off(monkeypatch):
    monkeypatch.delenv(governance.ENV_ROOT, raising=False)
    governance.reset()
    frame = _frame()
    frame.evaluate(_passing())
    frame.evaluate(_failing())
    assert len(frame.evaluation_history) == 2


# ── the record carries the diagnostic ────────────────────────────────────────


def test_a_rejection_records_why_it_was_rejected(ledger_root):
    """The README promises full diagnostic information; the record must carry it.

    An earlier draft wrote `violations: 2` -- a count, from which no reviewer
    can tell which constraint failed, at what value, against what threshold.
    """
    _frame().evaluate(_failing())

    record = _rows(ledger_root)[0]["record"]
    assert record["candidate"] == "CAND-FAIL"
    assert record["status"] == "rejected"

    failed = {v["constraint"]: v for v in record["violations"]}
    assert set(failed) == {"hERG_IC50_uM", "CYP3A4_inhibition_pct"}
    assert failed["hERG_IC50_uM"]["observed"] == 2.0
    assert failed["hERG_IC50_uM"]["threshold"] == 10.0
    assert failed["hERG_IC50_uM"]["rationale"] == "Cardiac safety margin"
    assert failed["hERG_IC50_uM"]["severity"] == "CRITICAL"
    assert failed["hERG_IC50_uM"]["confidence"] == pytest.approx(WELL_SOURCED)


def test_the_record_carries_what_each_constraint_rests_on(ledger_root):
    """Constraints are scientific objects: references and confidence, per constraint."""
    _frame().evaluate(_passing())

    sourced = {p["constraint"]: p for p in _rows(ledger_root)[0]["record"]["provenance"]}
    assert sourced["hERG_IC50_uM"]["source_type"] == "clinical_data"
    assert sourced["hERG_IC50_uM"]["references"] == ["doi:1", "doi:2", "doi:3"]
    assert sourced["hERG_IC50_uM"]["requires_verification"] is False

    # An accepted verdict resting on weak provenance still stands, and the
    # record still says what it rests on.
    assert sourced["CYP3A4_inhibition_pct"]["confidence"] == pytest.approx(BELOW_FLOOR)
    assert sourced["CYP3A4_inhibition_pct"]["requires_verification"] is True


def test_an_indeterminate_verdict_names_the_missing_property(ledger_root):
    _frame().evaluate(Candidate(name="CAND-PARTIAL", properties={"hERG_IC50_uM": 40.0}))

    record = _rows(ledger_root)[0]["record"]
    assert record["status"] == "indeterminate"
    assert "CYP3A4_inhibition_pct" in record["notes"]


def test_nothing_is_written_without_a_declared_contract(monkeypatch, tmp_path):
    """An open payload with no declaration is a dumping ground, so it is refused."""
    monkeypatch.setenv(governance.ENV_ROOT, str(tmp_path))
    governance.reset()

    result = _frame().evaluate(_failing())

    assert result.status == EvaluationStatus.REJECTED  # rule 2
    assert not governance.ledger_path(tmp_path).exists()
    assert "no verdict contract" in (governance.last_error() or "")


def test_a_record_breaking_the_contract_is_refused(ledger_root):
    from cura_frame.governance import ledger

    with pytest.raises(governance.LedgerError) as excinfo:
        ledger.append(ledger_root, {"candidate": "X", "status": "maybe", "violations": []})
    assert "breaks the declared contract" in str(excinfo.value)


# ── the chain ────────────────────────────────────────────────────────────────


def test_rows_are_chained_and_editing_a_verdict_is_detected(ledger_root):
    frame = _frame()
    frame.evaluate(_passing())
    frame.evaluate(_failing())

    rows = _rows(ledger_root)
    assert len(rows) == 2
    assert rows[0]["prev_hash"] == "genesis"
    assert rows[1]["prev_hash"] == rows[0]["entry_hash"]
    assert governance.verify() == []

    path = governance.ledger_path(ledger_root)
    rows[0]["record"]["status"] = "rejected"  # flip a verdict
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")

    findings = governance.verify()
    assert findings and "does not match its hash" in findings[0]


def test_removing_a_row_from_the_middle_is_detected(ledger_root):
    frame = _frame()
    for _ in range(3):
        frame.evaluate(_passing())

    rows = _rows(ledger_root)
    del rows[1]
    governance.ledger_path(ledger_root).write_text(
        "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8"
    )
    assert any("broken chain" in f for f in governance.verify())


@pytest.mark.parametrize(
    "corrupt,expected",
    [
        ("line", "line 2"),
        ("whole", "line 1"),
    ],
)
def test_a_corrupted_ledger_does_not_validate_clean(ledger_root, corrupt, expected):
    """A tamper-evidence tool that cannot see tampering is worse than none."""
    frame = _frame()
    for _ in range(3):
        frame.evaluate(_passing())

    path = governance.ledger_path(ledger_root)
    if corrupt == "line":
        lines = path.read_text(encoding="utf-8").splitlines()
        lines[1] = "CORRUPTED NOT JSON"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    else:
        path.write_text("not a ledger at all\n", encoding="utf-8")

    findings = governance.verify()
    assert findings, "a corrupted ledger must not validate clean"
    assert expected in findings[0]
    assert "not valid JSON" in findings[0]


def test_non_object_json_row_is_detected(ledger_root):
    frame = _frame()
    frame.evaluate(_passing())

    path = governance.ledger_path(ledger_root)
    # Write valid JSON that is a list instead of an object envelope
    path.write_text("[]\n", encoding="utf-8")

    findings = governance.verify()
    assert findings, "a ledger with non-object JSON must not validate clean"
    assert "not a JSON object" in findings[0]


def test_append_handles_missing_trailing_newline(ledger_root):
    frame = _frame()
    frame.evaluate(_passing())

    path = governance.ledger_path(ledger_root)
    content = path.read_text(encoding="utf-8")
    assert content.endswith("\n")
    # Strip the trailing newline
    path.write_text(content.rstrip("\r\n"), encoding="utf-8")

    # Append a second record
    frame.evaluate(_failing())

    rows = _rows(ledger_root)
    assert len(rows) == 2
    assert governance.verify() == []


def test_a_half_written_final_row_is_detected(ledger_root):
    frame = _frame()
    for _ in range(3):
        frame.evaluate(_passing())

    path = governance.ledger_path(ledger_root)
    path.write_bytes(path.read_bytes()[:-20])
    assert any("not valid JSON" in f for f in governance.verify())


def test_read_refuses_rather_than_silently_dropping_rows(ledger_root):
    """The defect this strictness removes: a truncated view with no signal."""
    frame = _frame()
    for _ in range(3):
        frame.evaluate(_passing())

    path = governance.ledger_path(ledger_root)
    lines = path.read_text(encoding="utf-8").splitlines()
    lines[1] = "CORRUPTED"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(governance.LedgerError):
        governance.read(ledger_root)
    with pytest.raises(governance.LedgerError):
        list(governance.records(ledger_root))


def test_removing_the_last_row_is_NOT_detectable(ledger_root):
    """The documented limit, asserted so nothing later claims otherwise.

    Rows 1..n-1 remain a perfect chain and nothing inside the file records that
    an n-th row existed. If this test ever starts failing, check that the new
    detection is real before updating the documentation.
    """
    frame = _frame()
    for _ in range(3):
        frame.evaluate(_passing())

    path = governance.ledger_path(ledger_root)
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")

    assert len(_rows(ledger_root)) == 2
    assert governance.verify() == []


# ── concurrency ──────────────────────────────────────────────────────────────


def test_concurrent_evaluations_do_not_fork_the_chain(ledger_root):
    """Two writers reading the same tail would compute the same prev_hash.

    In an append-only file that is not recoverable, and the console evaluates
    from more than one place.
    """
    raised: list[str] = []

    def worker(index: int) -> None:
        frame = _frame()
        for row in range(10):
            try:
                frame.evaluate(
                    Candidate(
                        name=f"T{index}-R{row}",
                        properties={"hERG_IC50_uM": 40.0, "CYP3A4_inhibition_pct": 10.0},
                    )
                )
            except Exception as exc:  # noqa: BLE001 - the diagnostic is the point
                raised.append(f"thread {index} row {row}: {type(exc).__name__}: {exc}")
                return

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert raised == [], raised
    assert len(_rows(ledger_root)) == 80
    assert governance.verify() == []


def _bytes_read_by_one_append(root: Path, frame: CuraFrame) -> int:
    """Total bytes read while performing exactly one append, cold."""
    from cura_frame.governance import ledger

    with ledger._HINT_LOCK:
        ledger._TAIL_HINT.clear()  # force the path a fresh process would take

    read_bytes = 0
    real_open = Path.open

    class _Counted:
        def __init__(self, handle):
            self._handle = handle

        def read(self, *args, **kwargs):
            nonlocal read_bytes
            data = self._handle.read(*args, **kwargs)
            read_bytes += len(data)
            return data

        def __getattr__(self, name):
            return getattr(self._handle, name)

        def __enter__(self):
            self._handle.__enter__()
            return self

        def __exit__(self, *exc):
            return self._handle.__exit__(*exc)

    def counted_open(self, mode="r", *args, **kwargs):
        handle = real_open(self, mode, *args, **kwargs)
        return _Counted(handle) if "r" in mode else handle

    Path.open = counted_open
    try:
        frame.evaluate(_passing())
    finally:
        Path.open = real_open
    return read_bytes


def test_appending_stays_cheap_as_the_ledger_grows(ledger_root):
    """One append reads the same amount whether the ledger is small or large.

    Measured in bytes rather than seconds: I/O is decided by the algorithm,
    while a stopwatch here mostly measures the machine. The absolute figure is
    the tail window plus the contract, both fixed; what matters is that neither
    moves when the ledger does.

    Without this property every append re-reads the whole file, which is O(n)
    per write and O(n^2) over a run -- and a ledger that has grown makes the
    next run slower than the last.
    """
    frame = _frame()

    for _ in range(20):
        frame.evaluate(_passing())
    small_size = governance.ledger_path(ledger_root).stat().st_size
    small_read = _bytes_read_by_one_append(ledger_root, frame)

    for _ in range(400):
        frame.evaluate(_passing())
    large_size = governance.ledger_path(ledger_root).stat().st_size
    large_read = _bytes_read_by_one_append(ledger_root, frame)

    assert large_size > small_size * 5, "the ledger did not grow enough to test anything"
    assert large_read == small_read, (
        f"bytes read per append moved with ledger size: "
        f"{small_read} at {small_size} bytes, {large_read} at {large_size} bytes"
    )
    assert large_read < large_size, (
        f"one append read {large_read} bytes of a {large_size}-byte ledger"
    )


def test_a_contract_violation_is_caught_even_when_the_chain_is_perfect(ledger_root):
    """Re-signing the whole file does not launder a record that breaks the contract.

    The chain answers "was this edited after it was written". It does not answer
    "is this a verdict at all" -- anyone who can edit the file can also
    recompute every hash in it, and the result is a chain that verifies. So
    `validate()` re-checks each record against the declared contract rather than
    stopping once the hashes line up.
    """
    from cura_frame.governance import ledger

    frame = _frame()
    for _ in range(4):
        frame.evaluate(_passing())

    path = governance.ledger_path(ledger_root)
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]

    rows[1]["record"]["status"] = "totally-made-up"
    for index in range(1, len(rows)):
        if index:
            rows[index]["prev_hash"] = rows[index - 1]["entry_hash"]
        rows[index].pop("entry_hash", None)
        rows[index]["entry_hash"] = ledger.compute_hash(rows[index])
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")

    findings = governance.verify()
    assert findings, "a re-signed chain must not launder a contract violation"
    assert "breaks the declared contract" in findings[0]
    assert "totally-made-up" in findings[0]


def test_tightening_the_contract_reports_rows_that_no_longer_fit(ledger_root):
    """A contract can change after rows exist; the old rows must be re-judged."""
    frame = _frame()
    frame.evaluate(_passing())
    assert governance.verify() == []

    # A field the recorder does not produce, so the existing row cannot satisfy
    # it. `gap_analysis` would not work here -- the engine emits one.
    tightened = json.loads(json.dumps(CONTRACT))
    tightened["required"] = sorted(set(tightened["required"]) | {"reviewed_by"})
    tightened["properties"]["reviewed_by"] = {"type": "string"}
    governance.declare(ledger_root, tightened)

    findings = governance.verify()
    assert any("reviewed_by" in f for f in findings), findings
    assert "breaks the declared contract" in findings[0]


# ── the command line ─────────────────────────────────────────────────────────


def test_verify_command_exits_zero_on_a_clean_ledger(ledger_root, capsys):
    from cura_frame.governance.__main__ import main

    _frame().evaluate(_passing())
    assert main(["--root", str(ledger_root), "verify"]) == 0
    assert "chain ok" in capsys.readouterr().out


def test_verify_command_reports_a_tampered_ledger_without_crashing(ledger_root, capsys):
    """A gate reports findings. Losing one to a traceback is the failure mode."""
    from cura_frame.governance.__main__ import main

    _frame().evaluate(_passing())
    path = governance.ledger_path(ledger_root)
    path.write_text("CORRUPTED NOT JSON\n", encoding="utf-8")

    assert main(["--root", str(ledger_root), "verify"]) == 1
    output = capsys.readouterr().out
    assert "unreadable" in output
    assert "not valid JSON" in output


def test_require_rows_is_what_catches_a_recorder_that_did_not_run(ledger_root, capsys):
    """The recorder degrades to silence, so an empty ledger is indistinguishable
    from a broken one unless something says an empty ledger is a failure."""
    from cura_frame.governance.__main__ import main

    assert main(["--root", str(ledger_root), "verify"]) == 0
    assert main(["--root", str(ledger_root), "verify", "--require-rows"]) == 1
    assert "the recorder did not run" in capsys.readouterr().out


def test_show_command_lists_recorded_verdicts(ledger_root, capsys):
    from cura_frame.governance.__main__ import main

    _frame().evaluate(_failing())
    assert main(["--root", str(ledger_root), "show"]) == 0
    output = capsys.readouterr().out
    assert "CAND-FAIL" in output
    assert "rejected" in output
    assert "hERG_IC50_uM" in output  # the first violation is summarised inline
