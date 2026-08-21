"""Optional, tamper-evident record of the verdicts CuraFrame reaches.

Off unless `CURAFRAME_LEDGER_ROOT` is set. When off, importing this package
costs one module load and nothing else runs.

    from cura_frame import governance

    governance.enabled()          # is anything being recorded?
    governance.verify()           # check the chain; returns findings, [] is clean
    governance.status()           # root, enabled, and why not if not

`cura_frame.core` calls `record()` from `_commit_evaluation()`. Nothing else in
the package should need to.

See `docs/governance.md` for what the chain proves, what it does not, and how to
remove the layer entirely.
"""

from __future__ import annotations

from .ledger import (
    LedgerError,
    contract,
    contract_path,
    declare,
    ledger_path,
    read,
    records,
    validate,
)
from .schema import SchemaError
from .sink import (
    ENV_ROOT,
    build_record,
    enabled,
    last_error,
    record,
    reset,
    status,
    verify,
)

__all__ = [
    "ENV_ROOT",
    "LedgerError",
    "SchemaError",
    "build_record",
    "contract",
    "contract_path",
    "declare",
    "enabled",
    "last_error",
    "ledger_path",
    "read",
    "record",
    "records",
    "reset",
    "status",
    "validate",
    "verify",
]
