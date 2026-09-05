# BMW Cross-Session Function Evidence

## Purpose

A single passive capture can produce convincing false positives. This stage
therefore aggregates exact raw-feature hypotheses across independent sessions
before any candidate is considered for decoder work.

It consumes JSON outputs produced by:

`tools/bmw_function_identifier.py`

and produces `BMWFunctionEvidence` records.

## Identity rule

Evidence is aggregated only when the exact raw interpretation matches across
sessions:

- function family;
- function kind;
- transport;
- transport source key;
- feature kind;
- start byte;
- width or bit;
- signedness;
- endian interpretation.

CAN and FlexRay candidates are never silently merged.

For FlexRay, the source key already preserves channel, slot, and either exact
cycle or known base-cycle/repetition schedule identity.

## Evidence score

The score prioritizes repeatability:

- session coverage: 35%;
- mean per-session hypothesis score: 25%;
- weakest observed session score: 15%;
- score stability: 10%;
- raw polarity consistency: 10%;
- mean direction score: 5%.

This intentionally makes a repeatable candidate more valuable than a one-off
high-scoring candidate.

## Confidence labels

Confidence is evidence confidence only.

`HIGH` requires at least three observed sessions, strong session coverage,
strong aggregate evidence, and consistent raw polarity.

`MEDIUM` requires at least two sessions and weaker thresholds.

Everything else remains `LOW`.

None of these labels mean `VEHICLE_VALIDATED`.

Every record remains:

`UNVALIDATED_CROSS_SESSION_EVIDENCE`

until later validation gates are satisfied.

## Running

Example:

```bash
python tools/bmw_cross_session_evidence.py \
  run001_function_hypotheses.json \
  run002_function_hypotheses.json \
  run003_function_hypotheses.json \
  --minimum-hypothesis-score 0.50 \
  --output cross_session_evidence.json
```

If an identifier output contains a `session_id`, it is used. Otherwise the
input filename stem becomes the session ID.

## Intended December workflow

```text
Capture 001 ─► Function Identifier ─┐
Capture 002 ─► Function Identifier ─┼─► Cross-Session Evidence
Capture 003 ─► Function Identifier ─┘
                                      │
                                      ▼
                              BMWFunctionEvidence
                                      │
                         read-only corroboration
                                      │
                                      ▼
                              decoder evidence gate
```

The next stage may compare high-confidence CAN and FlexRay evidence for the same
function family to classify likely network availability:

- CAN-only candidate;
- FlexRay-only candidate;
- candidate visible on both transports;
- possible ZGW-derived representation;
- unresolved.

That later correspondence stage must not assume two same-family candidates are
the same physical signal merely because their event signatures match.

## Safety boundary

This tool does not:

- create or modify a DBC;
- assign engineering scale, offset, or units;
- auto-promote a decoder;
- claim vehicle validation;
- write diagnostics;
- transmit CAN;
- transmit FlexRay;
- create `CarState` or `RadarData`;
- create a BMW `CarController`;
- grant actuation authority.

All processing is offline/read-only.
