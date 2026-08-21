"""Command line for the verdict ledger.

    python -m cura_frame.governance verify    check the chain; exits non-zero on a finding
    python -m cura_frame.governance show      print the recorded verdicts
    python -m cura_frame.governance demo      record, verify, tamper, show it caught

`verify` is what CI runs. Keeping it here rather than inline in the workflow
means the check is the same one you can run locally, and cannot drift from it.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import ledger


def _verify(root: Path, require_rows: bool) -> int:
    findings = ledger.validate(root)

    # `read()` is strict and raises on a file that is not a ledger, so the count
    # is taken defensively: losing the finding to a traceback would leave the
    # output saying nothing useful about a tampered ledger, which is the failure
    # this command exists to prevent.
    try:
        rows: int | str = len(ledger.read(root))
    except ledger.LedgerError:
        rows = "unreadable"

    print(f"verdict ledger: {rows} rows, chain {'ok' if not findings else 'BROKEN'}")
    for finding in findings:
        print(f"  {finding}")

    if require_rows and rows == 0:
        print("  no verdicts were recorded; the recorder did not run")
        return 1
    return 1 if findings else 0


def _show(root: Path, limit: int) -> int:
    try:
        rows = ledger.read(root)
    except ledger.LedgerError as exc:
        print(exc)
        return 1
    if not rows:
        print("no verdicts recorded")
        return 0
    for row in rows[-limit:] if limit else rows:
        record = row["record"]
        line = f"{row['ts_utc']}  {record['status']:<14} {record['candidate']}"
        if record.get("violations"):
            first = record["violations"][0]
            line += f"  [{first['constraint']} {first['observed']} vs {first['threshold']}]"
            extra = len(record["violations"]) - 1
            if extra:
                line += f" +{extra} more"
        print(line)
    print(f"\n{len(rows)} rows")
    return 0


def _demo(root: Path) -> int:
    """Record a verdict, verify it, tamper with it, watch the check catch it.

    Ten seconds, in a temporary directory, touching nothing. The point of the
    chain is not that it says `ok` -- it is that it stops saying `ok` the moment
    a recorded verdict is no longer what was recorded, and that is easier to
    believe after seeing it than after reading about it.
    """
    import operator
    import tempfile

    from ..core import Candidate, Constraint, CuraFrame, Provenance, Severity
    from . import reset, verify as sink_verify

    workspace = Path(tempfile.mkdtemp(prefix="curaframe-ledger-demo-"))
    contract = json.loads((root / ".curaframe" / "verdicts.schema.json").read_text("utf-8"))
    ledger.declare(workspace, contract)

    import os

    os.environ["CURAFRAME_LEDGER_ROOT"] = str(workspace)
    reset()

    frame = CuraFrame(
        name="demo",
        safety_constraints=[
            Constraint(
                name="hERG_IC50_uM",
                threshold=10.0,
                comparator=operator.ge,
                rationale="Cardiac safety margin",
                severity=Severity.CRITICAL,
                provenance=Provenance(
                    source_type="clinical_data",
                    confidence=0.92,
                    references=["doi:10.1093/cvr/cvg003"],
                ),
            )
        ],
    )

    print(f"workspace: {workspace}\n")

    print("1. evaluate two candidates")
    for name, value in (("safe-candidate", 40.0), ("cardiotoxic-candidate", 2.0)):
        result = frame.evaluate(Candidate(name=name, properties={"hERG_IC50_uM": value}))
        print(f"   {name:<24} {result.status.value}")

    print("\n2. what was recorded")
    row = ledger.read(workspace)[-1]
    print(json.dumps(row["record"], indent=2)[:520])

    print("\n3. verify")
    print(f"   findings: {sink_verify(workspace) or 'none — chain intact'}")

    print("\n4. edit a recorded verdict by hand (rejected -> accepted)")
    path = ledger.ledger_path(workspace)
    rows = [json.loads(line) for line in path.read_text("utf-8").splitlines() if line]
    rows[-1]["record"]["status"] = "accepted"
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")

    print("\n5. verify again")
    for finding in sink_verify(workspace):
        print(f"   {finding}")

    print("\nThe edit is detectable because the row's hash no longer matches its")
    print("content. Nothing was written outside the temporary directory above.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m cura_frame.governance",
        description="Inspect and verify the verdict ledger.",
    )
    parser.add_argument("--root", default=".", help="repository root (default: .)")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("verify", help="check the chain and the declared contract")
    check.add_argument(
        "--require-rows",
        action="store_true",
        help="also fail when the ledger is empty, which is how CI detects a recorder "
        "that ran but wrote nothing",
    )

    listing = sub.add_parser("show", help="print recorded verdicts")
    listing.add_argument("-n", type=int, default=20, help="last N rows; 0 for all")

    sub.add_parser("demo", help="record, verify, tamper, and watch the check catch it")

    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    if args.command == "verify":
        return _verify(root, args.require_rows)
    if args.command == "show":
        return _show(root, args.n)
    return _demo(root)


if __name__ == "__main__":
    sys.exit(main())
