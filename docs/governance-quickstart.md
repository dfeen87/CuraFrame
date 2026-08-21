# Verdict ledger — quickstart

One page. [`governance.md`](governance.md) is the long version.

## What it is

- An **optional record** of the verdicts `CuraFrame.evaluate()` reaches — accepted, rejected, indeterminate.
- Each verdict is written with the **full diagnostic the engine already produced**: every `Violation` field, the `gap_analysis`, and the per-constraint provenance with its references.
- Rows are **hash-chained**, so editing a recorded verdict or removing one from the middle is detectable.
- The **record shape is declared in this repo** — `.curaframe/verdicts.schema.json` — not decided by the code.

## What it is not

- **Not on by default.** Without `CURAFRAME_LEDGER_ROOT` set, nothing is imported, written, or slower.
- **Not a dependency.** Standard library only.
- **Not an opinion on pharmacology.** It records what the engine decided; it cannot change a verdict.
- **Not able to break an evaluation.** Any recording fault degrades to silence.

## See it work — 10 seconds

```bash
python -m cura_frame.governance demo
```

Records two verdicts in a temporary directory, verifies the chain, edits a recorded verdict by hand, and shows the check catching it. Writes nothing outside that temporary directory.

## Turn it on

```bash
export CURAFRAME_LEDGER_ROOT="$PWD"
python -m cura_frame.cli ...
```

Verdicts land in `.curaframe/verdicts.jsonl`, which is gitignored — it makes one run auditable, it is not an archive.

## Check it

```bash
python -m cura_frame.governance verify   # exits non-zero on any finding
python -m cura_frame.governance show     # the last 20 verdicts, one line each
```

`verify` is the same command CI runs, so it cannot drift from what you can reproduce locally.

## Turn it off

Unset `CURAFRAME_LEDGER_ROOT`, and delete the line that sets it in `.github/workflows/ci.yml`. Nothing needs removing.

## Remove it entirely

```bash
git rm -r cura_frame/governance tests/test_governance.py .curaframe
git revert -m 1 <merge-commit>     # the core.py hook and the CI steps
```

The second command is not optional. `git checkout -- <file>` restores from the index, which after a merge holds the modified version — so it runs, reports nothing, and changes nothing.

Doing only the first leaves the hook in `core.py`, where it cannot find the package and the `except` swallows the `ImportError`. `pytest` then returns to its pre-adoption result with no skips, which looks like a clean removal and is not one:

```bash
grep -c "_commit_evaluation" cura_frame/core.py   # 0 when actually removed
```

## What the chain does not prove

It **cannot detect rows removed from the end**. Rows 1..n−k stay a perfect chain, because nothing inside the file records that an n-th row ever existed. That is inherent to append-only logs; closing it needs an anchor outside the file, and this arrangement deliberately has none — the ledger is rebuilt every run.

The limit is asserted as a test (`test_removing_the_last_row_is_NOT_detectable`) so nothing later claims a detection it cannot perform.

## Scope

The **Python evaluation path only**. `constraint_core/`, `constraints/` and `scoring/` produce no verdict that reaches the ledger — nothing links the static library, there is no Python bridge, there are no C++ tests, and both `render.yaml` services are `env: python`. If that changes, this layer will not follow automatically.

## Files

| Path | |
|---|---|
| `cura_frame/governance/ledger.py` | the chain — append, read, validate |
| `cura_frame/governance/sink.py` | `EvaluationResult` → record |
| `cura_frame/governance/schema.py` | a JSON Schema subset, so no dependency is added |
| `cura_frame/governance/__main__.py` | `verify` / `show` / `demo` |
| `cura_frame/core.py` | `+26 / −4` — the hook and its three call sites |
| `.curaframe/verdicts.schema.json` | the contract, tracked |
| `.curaframe/verdicts.jsonl` | the ledger, gitignored |
