"""An append-only, hash-chained record of the verdicts CuraFrame reached.

Each row wraps one verdict in an envelope:

    ts_utc  record  prev_hash  entry_hash
            ^^^^^^
            the verdict, in whatever shape verdicts.schema.json declares

`prev_hash` links a row to the one before it and `entry_hash` covers the whole
canonical row, so editing a recorded verdict, removing one from the middle, or
corrupting a line all break the chain and are reported by `validate()`.

The record shape is **not** fixed here. It lives in
`.curaframe/verdicts.schema.json`, and `append()` refuses to write a record that
does not match it. That separation is the point: the envelope belongs to this
module, the contents belong to whoever declares the contract, and a ledger with
an open payload and no declaration is a dumping ground.

What the chain proves
---------------------

`validate()` reporting clean means no row was modified, none removed from the
middle, no line corrupted, and the last row is not half-written.

**It does not detect continuous removal from the last row onward.** Delete the
final k rows and rows 1..n-k remain a perfect chain -- every hash recomputes,
every record matches the contract, and nothing inside the file records that an
n-th row ever existed. That is a property of hash-chained append-only logs, not
a gap in this implementation, and closing it needs state outside the file. Here
the ledger is rebuilt each run and is not tracked, so there is nothing to anchor
against and nothing that needs anchoring.

Provenance
----------

Adapted from an internal governance tool, reduced to what this repository needs
and rewritten around a single ledger. No external dependency, no licence
obligation. Five defects were found and fixed while it was being used against
this repository, and each is noted at the code it applies to.
"""

from __future__ import annotations

import hashlib
import json
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from .schema import SchemaError, validate as validate_schema

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl

LEDGER_DIR = ".curaframe"
LEDGER_FILE = "verdicts.jsonl"
CONTRACT_FILE = "verdicts.schema.json"

CHAIN_GENESIS = "genesis"
HASH_LENGTH = 16

#: Keys the envelope owns. A record may not use them.
RESERVED_KEYS = ("ts_utc", "record", "prev_hash", "entry_hash")

#: One row is all `append()` needs to read. 4 KB covers every verdict this
#: repository produces; a larger row doubles the window until it fits.
_TAIL_WINDOW = 4096

#: Windows only. `msvcrt.locking` is mandatory rather than advisory, so a lock
#: on byte 0 would deny every other open of the file -- including this module's
#: own tail read. A byte past any plausible ledger serialises writers without
#: covering data a reader needs.
_LOCK_OFFSET = 0x7FFFFFFE

#: How long a writer waits for the lock before giving up. Generous on purpose:
#: losing a verdict is worse than waiting, and a wait this long means something
#: is wrong rather than busy.
_LOCK_TIMEOUT = 60.0

#: path -> (file size after this process last wrote, that row's hash).
#:
#: Opening a just-written file for *reading* is far more expensive than opening
#: it for appending -- measured at 43 ms against 0.5 ms on one machine, scaling
#: with file size, because real-time antivirus rescans on the read-open. This
#: hint removes that read in the common case.
#:
#: It is a hint, never an authority: every use is gated on the file still being
#: exactly the size this process's last write left it, measured inside the lock.
#: A write from anywhere else changes the size and the hint is discarded, so it
#: can be stale but cannot be silently wrong.
_TAIL_HINT: dict[str, tuple[int, str]] = {}
_HINT_LOCK = threading.Lock()


class LedgerError(ValueError):
    """Raised when the ledger has no contract, or a record breaks it, or the
    file on disk is not something this module wrote."""


# ── locations ────────────────────────────────────────────────────────────────


def ledger_path(root: Path | str) -> Path:
    return Path(root) / LEDGER_DIR / LEDGER_FILE


def contract_path(root: Path | str) -> Path:
    return Path(root) / LEDGER_DIR / CONTRACT_FILE


# ── the envelope ─────────────────────────────────────────────────────────────


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical(row: dict[str, Any]) -> str:
    payload = {key: value for key, value in row.items() if key != "entry_hash"}
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_hash(row: dict[str, Any]) -> str:
    """Digest the whole canonical row, so a field added later is covered at once."""
    return hashlib.sha256(_canonical(row).encode("utf-8")).hexdigest()[:HASH_LENGTH]


def read(root: Path | str) -> list[dict[str, Any]]:
    """Every row, or `LedgerError` naming the first line that is not one.

    Strict on purpose. A lenient version of this function returned the rows it
    had managed to parse and stopped at the first `JSONDecodeError` without
    saying so -- and because `validate()` reads through here, every row after a
    corrupted line left the universe. A ledger truncated to a third of itself
    validated clean, and so did a file replaced entirely with junk.

    Raising is what makes corruption reachable by every caller at once, rather
    than each having to remember to look.
    """
    path = ledger_path(root)
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError as exc:
            raise LedgerError(
                f"verdict ledger line {number} is not valid JSON ({exc.msg}); "
                f"the file has been edited or truncated after it was written"
            ) from exc
        if not isinstance(parsed, dict):
            raise LedgerError(
                f"verdict ledger line {number} is not a JSON object; "
                f"the file has been edited or corrupted"
            )
        rows.append(parsed)
    return rows


def records(root: Path | str) -> Iterator[dict[str, Any]]:
    """The verdicts alone, for a reader that wants them without the chain."""
    for row in read(root):
        yield row.get("record", {})


# ── the contract ─────────────────────────────────────────────────────────────


def declare(root: Path | str, record_schema: dict[str, Any]) -> Path:
    """Declare what a verdict record must look like. Required before writing."""
    path = contract_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record_schema, indent=2) + "\n", encoding="utf-8")
    return path


def contract(root: Path | str) -> dict[str, Any]:
    path = contract_path(root)
    if not path.is_file():
        raise LedgerError(
            f"no verdict contract at {path}; declare one before recording verdicts"
        )
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise LedgerError(f"the verdict contract is not valid JSON: {exc}") from exc


# ── locking ──────────────────────────────────────────────────────────────────


def _lock(handle) -> None:
    """Take an exclusive lock on the ledger file itself.

    Locking the file rather than a sidecar means the thing protected is the
    thing written, so a crash cannot strand a lock for a file that no longer
    exists.
    """
    if sys.platform == "win32":
        handle.seek(_LOCK_OFFSET)
        # `LK_LOCK` retries internally for ten seconds and then raises, and ten
        # seconds is reachable under real contention. The raise would land in
        # whichever thread was writing, killing it and losing its remaining
        # rows, so the wait is ours to control rather than the C runtime's.
        deadline = time.monotonic() + _LOCK_TIMEOUT
        delay = 0.001
        while True:
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                return
            except OSError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(delay)
                delay = min(delay * 2, 0.05)
    else:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)


def _unlock(handle) -> None:
    if sys.platform == "win32":
        try:
            handle.seek(_LOCK_OFFSET)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
    else:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


# ── writing ──────────────────────────────────────────────────────────────────


def _tail_line(path: Path) -> str | None:
    """The last non-empty line, read by seeking backward from EOF.

    `append()` needs the previous row's hash, not the file. Reading the whole
    thing per write is O(n) per append and O(n^2) over a run: at a thousand
    rows that was 145 KB read per write.
    """
    if not path.is_file():
        return None
    size = path.stat().st_size
    if size == 0:
        return None
    window = _TAIL_WINDOW
    with path.open("rb") as handle:
        while True:
            offset = max(0, size - window)
            handle.seek(offset)
            chunk = handle.read().rstrip(b"\r\n")
            if not chunk:
                return None
            index = chunk.rfind(b"\n")
            if index != -1:
                return chunk[index + 1 :].decode("utf-8")
            if offset == 0:
                return chunk.decode("utf-8")
            window *= 2


def _ends_with_newline(path: Path) -> bool:
    """True if the file ends with a newline byte, or False if missing."""
    if not path.is_file() or path.stat().st_size == 0:
        return True
    with path.open("rb") as handle:
        handle.seek(-1, 2)
        return handle.read(1) in (b"\n", b"\r")


def _prev_hash(path: Path, size: int) -> str:
    """The hash the next row should carry, from the hint or from the tail."""
    with _HINT_LOCK:
        hint = _TAIL_HINT.get(str(path))
    if hint is not None and hint[0] == size:
        return hint[1]

    tail = _tail_line(path)
    if tail is None:
        return CHAIN_GENESIS
    try:
        row = json.loads(tail)
    except json.JSONDecodeError as exc:
        raise LedgerError(
            f"the last line of the verdict ledger is not valid JSON ({exc.msg}); "
            f"refusing to append to a file that has been edited or truncated"
        ) from exc
    if not isinstance(row, dict):
        raise LedgerError(
            "the last line of the verdict ledger is not a JSON object; "
            "refusing to append to a file that has been edited or corrupted"
        )
    last = row.get("entry_hash")
    if not isinstance(last, str) or not last:
        raise LedgerError("the last row of the verdict ledger carries no hash")
    return last


def append(root: Path | str, record: dict[str, Any]) -> dict[str, Any]:
    """Append one chained row. Raises if the record breaks the declared contract.

    Constant cost in the number of rows already present: at most one 4 KB read,
    one file open, one write. An exclusive lock spans the read-then-write, so
    two concurrent writers cannot read the same tail, compute the same
    `prev_hash`, and fork the chain -- which in an append-only file is not
    recoverable.
    """
    if not isinstance(record, dict):
        raise LedgerError("a verdict record must be an object")
    overlap = sorted(set(record) & set(RESERVED_KEYS))
    if overlap:
        raise LedgerError(f"a verdict record may not use envelope keys {overlap}")

    declared = contract(root)
    try:
        validate_schema(record, declared, "verdict")
    except SchemaError as exc:
        raise LedgerError(f"verdict breaks the declared contract ({exc})") from exc

    path = ledger_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Append-only mode, deliberately: on Windows a read-write open with a seek
    # costs ~33 ms against 0.5 ms here, and scales with file size.
    with path.open("ab") as handle:
        _lock(handle)
        try:
            size_before = path.stat().st_size
            row: dict[str, Any] = {
                "ts_utc": _now_utc(),
                "record": record,
                "prev_hash": _prev_hash(path, size_before),
            }
            row["entry_hash"] = compute_hash(row)
            payload = json.dumps(row, ensure_ascii=True).encode("utf-8") + b"\n"
            if size_before > 0 and not _ends_with_newline(path):
                payload = b"\n" + payload
            handle.write(payload)
            handle.flush()
            with _HINT_LOCK:
                _TAIL_HINT[str(path)] = (size_before + len(payload), row["entry_hash"])
        finally:
            _unlock(handle)
    return row


# ── verifying ────────────────────────────────────────────────────────────────


def validate(root: Path | str) -> list[str]:
    """Check the chain and re-check every record against the current contract.

    Returns findings rather than raising: this is what a gate calls, and a file
    that will not parse is a finding rather than an exception for somebody else
    to handle.

    Re-checking the records matters because a contract can be tightened after
    rows exist, and a ledger whose contract no longer describes its own contents
    should say so rather than pass because the hashes still line up.

    An empty result means the rows that are present are sound. It does not mean
    none are missing from the end -- see the module docstring.
    """
    try:
        rows = read(root)
    except LedgerError as exc:
        return [str(exc)]

    path = ledger_path(root)
    if not rows:
        if path.is_file() and path.stat().st_size > 0:
            return ["the verdict ledger has content but no readable rows; it has been overwritten"]
        return []

    try:
        declared = contract(root)
    except LedgerError as exc:
        return [str(exc)]

    findings: list[str] = []
    expected = CHAIN_GENESIS
    for index, row in enumerate(rows, start=1):
        if row.get("prev_hash") != expected:
            findings.append(
                f"row {index}: broken chain, expected prev_hash "
                f"`{expected}` but found `{row.get('prev_hash')}`"
            )
            return findings
        recomputed = compute_hash(row)
        if row.get("entry_hash") != recomputed:
            findings.append(
                f"row {index}: content does not match its hash "
                f"(recomputed `{recomputed}`, row claims `{row.get('entry_hash')}`)"
            )
            return findings
        try:
            validate_schema(row.get("record", {}), declared, f"row {index}")
        except SchemaError as exc:
            findings.append(f"row {index}: record breaks the declared contract ({exc})")
        expected = row["entry_hash"]
    return findings
