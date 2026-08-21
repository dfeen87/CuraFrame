# Verdict ledger

An optional, off-by-default record of the verdicts `CuraFrame.evaluate()`
reaches. It is not part of the falsification engine and has no opinion on
pharmacology.

CuraFrame already produces governed decisions — `ACCEPTED` / `REJECTED` /
`INDETERMINATE`, violations carrying a severity, constraints carrying
`Provenance` with an epistemic confidence. What it does not do is keep them: an
`EvaluationResult` is returned, appended to an in-memory list, and that is the
end of it. Re-run the same candidate a month later against a changed constraint
set and there is no record of what it decided the first time, or on what basis.

---

## Using it

```bash
# off — the default. Nothing is imported, written, or slower.
python -m cura_frame.cli ...

# on
export CURAFRAME_LEDGER_ROOT="$PWD"
python -m cura_frame.cli ...
```

```python
from cura_frame import governance

governance.enabled()          # is anything being recorded?
governance.verify()           # check the chain; [] means clean
governance.status()           # root, enabled, and why not if not
list(governance.records(root))  # the verdicts, without the chain envelope
```

Every verdict is appended to `.curaframe/verdicts.jsonl`, carrying the
diagnostic the engine already produced:

- each `Violation` with its `constraint`, `observed`, `threshold`, `rationale`,
  `severity` and `confidence`
- the `gap_analysis`, when the engine computed one
- per-constraint `Provenance`: `source_type`, `confidence`, literature
  `references`, and whether it falls below the verification floor
- for `INDETERMINATE`, the property that was missing, by name

---

## The record shape is declared here, not in the code

`.curaframe/verdicts.schema.json` says what a verdict must contain, and
`append()` refuses to write anything that does not match it. Change the contract
and `verify()` will report the existing rows that no longer fit, rather than
passing because the hashes still line up.

That separation is deliberate. An earlier draft of the recorder wrote:

```json
{"candidate": "or_fail", "status": "rejected", "violations": 2}
```

Two six-field `Violation` objects, the gap analysis, and the literature
references — all discarded, because the recorder decided the shape. A reviewer
reading that row cannot tell which constraint failed, at what value, against
what threshold, which is the one thing this repository exists to produce.

---

## What the chain proves

`verify()` returning `[]` means:

- **no recorded row was modified** — every row's hash recomputes from its content
- **no row was removed from the middle** — each `prev_hash` matches its predecessor
- **no line is corrupted** — every line parses, and the line number is named if one does not
- **the final row is not half-written**

and every record still matches the declared contract.

## What it does not prove

**Continuous removal from the last row onward is not detectable.** Delete the
final *k* rows and rows 1..n−k remain a perfect chain: every hash recomputes,
every record matches. Nothing inside the file records that an n-th row ever
existed, so no amount of reading it reveals the loss.

That is a property of hash-chained append-only logs, not a defect. Closing it
needs state outside the file — normally a committed copy, so `git diff` shows a
removal the chain cannot.

**This arrangement has no such anchor, on purpose.** `.curaframe/verdicts.jsonl`
is gitignored and rebuilt by every run: the rows make one execution auditable,
they are not an archive. If you later keep a ledger across runs, the anchor
becomes yours to solve — a tracked file or an external attestation, not a
row-count sidecar, which can drift from the thing it counts.

The limit is asserted as a test (`test_removing_the_last_row_is_NOT_detectable`)
so that nothing later claims a detection it cannot perform.

---

## Three rules the recorder obeys

| | |
|---|---|
| **It never changes a verdict** | The same result is asserted with recording on and off. |
| **It never raises into evaluation** | Pointed at a root with no contract, evaluation still returns. Failures degrade to silence; `governance.last_error()` says why. |
| **It is off unless asked for** | No `CURAFRAME_LEDGER_ROOT` → no import, no write, no cost. |

The bare `except` in `core.py`'s `_commit_evaluation()` is what makes rule 2
true, and it has a cost worth naming: a silently broken recorder looks the same
as an idle one. That is why CI fails when the suite runs and the ledger is
empty, rather than trusting that rows appear.

---

## Cost

Measured on this repository — 86 tests across `test_core`, `test_sensitivity`,
`test_multi_bundle`, `test_simulations`:

Five runs of each, ranges rather than a figure, because a single number here
does not survive being measured again:

| | |
|---|---|
| recording off (the default) | 0.23 – 0.92 s |
| recording on, empty ledger | 0.37 – 1.41 s |
| recording on, over an existing 200-row ledger | 0.43 – 0.53 s |

Roughly 0.1 – 0.3 s to record 200 verdicts. The spread is the machine, not the
code: the `off` column varies four-fold while doing no recording at all.

**What the ranges do show is the property that matters — cost does not grow with
the ledger.** The 200-row column is no slower than the empty one, and is in fact
the steadier of the two.

That is the only claim wall clock can support here, so it is the only one made.
What the suite asserts instead is the byte count, because I/O is decided by the
algorithm while a stopwatch mostly measures the machine:
`test_appending_stays_cheap_as_the_ledger_grows` records one append at 20 rows
and again at 420 and requires the two to be identical.

---

## Files

| Path | |
|---|---|
| `cura_frame/governance/ledger.py` | the chain: append, read, validate |
| `cura_frame/governance/schema.py` | a small JSON Schema subset, so there is no new dependency |
| `cura_frame/governance/sink.py` | shapes an `EvaluationResult` into a record |
| `cura_frame/core.py` | `+26 / −4` — `_commit_evaluation()` and its three call sites |
| `tests/test_governance.py` | 24 controls: the three rules, the diagnostic, the chain, the contract, concurrency |
| `.curaframe/verdicts.schema.json` | the contract; tracked |
| `.curaframe/verdicts.jsonl` | the ledger; gitignored |

No third-party dependency. The package imports only the standard library.

---

## Removing it

**Turning it off needs no removal.** Unset `CURAFRAME_LEDGER_ROOT` — and drop it
from `ci.yml` — and the recorder imports nothing and writes nothing.

To take it out entirely:

```bash
git rm -r cura_frame/governance tests/test_governance.py .curaframe
git revert -m 1 <merge-commit>    # the core.py hook and the CI steps
```

The second line is not optional, and `git checkout -- <file>` will not do it:
`checkout` restores from the index, and after a merge the index holds the
modified version, so the command runs and changes nothing.

Doing the first line alone leaves the hook in `core.py`, where it cannot find
the package and the `except` swallows the `ImportError`. `pytest` returns to its
pre-adoption result and reports no skips, which looks like a clean removal and
is not one. Verify instead of assuming:

```bash
grep -c "_commit_evaluation" cura_frame/core.py    # 0 when actually removed
```

---

## Provenance

`ledger.py` and `schema.py` were adapted from an internal governance tool,
reduced to what this repository needs and rewritten around a single ledger. No
external dependency and no licence obligation — they are this repository's code
now, to change or delete as you see fit.

Five defects were found and fixed while the tool was being used here: a `read()`
that swallowed parse errors so a corrupted ledger validated clean, an append
that re-read the whole file, concurrent appends that forked the chain, a file
lock that gave up after ten seconds inside a worker thread, and performance
criteria that measured the machine rather than the code. Each is noted at the
code it applies to, and each has a test that fails without the fix.
