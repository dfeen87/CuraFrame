# CuraFrame 7.0.0 — BEDROCK engineering baseline

## Why this is a major release

CuraFrame's architecture remains sound: explicit constraints feed a deterministic
evaluation engine; applications consume its results; optional governance records
committed verdicts; and the C++ constraint/scoring universe remains a parallel,
buildable integration surface. The BEDROCK audit therefore did not redesign these
layers. It strengthened guarantees underneath them.

Version 7.0.0 is a major engineering-baseline release because malformed numeric
evidence that earlier versions could accept is now rejected or made indeterminate.
This is an intentional behavioral incompatibility at a safety boundary, not a
claim that normal finite-input APIs are incompatible.

## Invariant map and corrections

| Behavior | Required invariant | Earlier enforcement | 7.0.0 enforcement and proof |
| --- | --- | --- | --- |
| Constraint evaluation | Physical numeric evidence and thresholds are finite | NaN was partly rejected; positive infinity could satisfy minimum constraints | `Constraint.evaluate` checks scalar and range numbers before every built-in or custom comparator; regressions cover NaN and both infinities |
| Pipelayer authorization | Authorization requires complete, finite, supported evidence and satisfaction of configured policy minima | Clamping and floating-point comparisons could turn infinity into SAFE or let NaN evade threshold flags; configured trust/reliability minima were not authorization gates | A preflight gate returns SHUTDOWN for malformed scores/telemetry, impossible negative/percentage values, invalid unit intervals, and UNKNOWN operational context; policy minima now gate authorization |
| Stateful trust processing | Rejected malformed input cannot influence later decisions | Invalid values entered the pipeline history before a decision | Preflight runs before `pipeline.process`; regression tests assert history is unchanged |
| Governance persistence | Every row is standards-compliant JSON and contract-valid | Python's JSON extensions could emit and parse NaN/Infinity; NaN evaded numeric limits | Schema validation rejects non-finite values at any depth, serializers use `allow_nan=False`, and readers reject non-standard constants |
| Release metadata | Runtime, package, native build, citation, docs, and CLI identify one release | Metadata was consistent but CLI had no version output | All active declarations identify 7.0.0 and CI checks installed and runtime versions |
| CI enforcement | Supported Python and shipped C++ paths are exercised | One Python version ran; C++ was not built | Python 3.9/3.11 jobs run the suite and smoke checks; a Release CMake job builds the native library |

## Failure behavior and compatibility

- Non-finite therapeutic evidence now yields `INDETERMINATE` with an evaluation
  error. It cannot become accepted merely because infinity exceeds a minimum.
- Malformed pipelayer evidence yields a deterministic, audited
  `HALT_IMMEDIATELY`/`SHUTDOWN` result with zero validated trust and confidence.
  UNKNOWN operation, machine, or pipe classifications are unsupported for an
  authorization decision and fail closed.
- Finite scores below configured operation-trust or measurement-reliability
  minima are valid evidence of insufficient assurance, but can no longer receive
  restricted authorization through trust-pipeline grace.
- Invalid governance numbers are not persisted. The optional recorder retains
  its established isolation rule: recording failure never changes the scientific
  verdict, and `last_error()` remains the diagnostic surface.
- Valid finite candidate evaluations, bundle structure, application boundaries,
  hash chaining, population stratification, and C++ APIs are intentionally
  preserved.

## Risks investigated but not changed

- Non-strict therapeutic evaluation may accept after checking only the properties
  that are present. This is an explicit caller-selected exploratory mode and
  continues to emit missing-property warnings; strict mode remains the safety
  default.
- OR groups retain diagnostics for failed alternative branches even when another
  branch satisfies the group. This preserves useful falsification detail and does
  not change the overall logical verdict.
- The governance hash chain cannot detect deletion of a contiguous suffix without
  an external anchor. This is an inherent and already documented trust boundary.
- The optional external AILEE implementation was not available in this repository.
  The bundled fallback path is tested; compatibility with an independently evolving
  external package requires separate integration validation.

## CI and regression guarantees

CI now proves the Python suite at the declared lower supported version and a
current production version, verifies runtime and installed version metadata,
smoke-tests CLI help and version output, compiles Python bytecode, verifies an
enabled governance ledger, and compiles the C++ library in Release mode. These
checks establish software behavior only; they do not establish scientific or
physical validity.

## Validation outside this repository

CuraFrame remains a research reasoning and falsification framework, not a clinical
device or certification artifact. Constraint thresholds, provenance, population
models, and therapeutic interpretation require current literature review, domain
experts, experimental studies, and any applicable regulatory process.

The pipelayer module is likewise not authorization for real machinery. Deployment
requires independent review of machine-specific load charts, sensor calibration
and fault injection, simulation, hardware-in-the-loop and field validation,
operator procedures, site rules, applicable standards, and certification by the
responsible authorities. Software tests prove only the encoded failure semantics.
