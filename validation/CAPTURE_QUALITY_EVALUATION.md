# Offline capture-quality evaluation

`validation/capture_quality_evaluator.py` derives an auditable acquisition-quality result from recorder provenance, counters and observable trace statistics.

It evaluates already-recorded data only. It contains no SocketCAN, Panda, Vector, FlexRay, diagnostic, EPS, DSC, steering, braking or torque transmission path.

## Why this gate exists

A valid parser and a correct signal decoder cannot repair frames that the acquisition hardware silently discarded. Conversely, an unknown drop counter must not be silently interpreted as zero.

The evaluator keeps three questions separate:

1. are the records structurally usable;
2. is there evidence that the frame stream is complete;
3. do the timestamps have meaningful per-frame provenance?

Frame-rate qualification never upgrades timestamp fidelity.

## Outputs

The primary result is one of:

- `LOSSY` — direct evidence of loss or corruption exists;
- `OBSERVATION_ONLY` — useful for exploration, but completeness is not established;
- `FULL_RATE_CANDIDATE` — available evidence is consistent with a complete capture, still subject to independent validation.

Each report also contains:

- declared quality versus evaluated quality;
- timing quality;
- positive, negative and unknown evidence lists;
- all counters and statistics used in the decision;
- `actuation_authority = NONE`.

## Evidence that forces `LOSSY`

Examples include:

- non-zero adapter drop or overflow counters;
- structural record errors or timestamp regressions;
- trusted capture-sequence gaps, duplicates or regressions;
- anomalies from validated bus-cycle/schedule statistics;
- a failed explicit frame-rate check;
- mismatch or invalidity against a simultaneous reference capture;
- an explicit source declaration that the capture is lossy.

Negative evidence takes precedence over every positive claim.

## Requirements for `FULL_RATE_CANDIDATE`

The trace must be non-empty, structurally valid and explicitly listen-only. In addition, at least one of these evidence paths must be present:

- exact frame fidelity calculated by the simultaneous CAN comparator (or the existing FlexRay comparison path);
- independently confirmed expected message/frame rate;
- continuous adapter-side monotonic sequence;
- schedule-validated cycle statistics without anomalies;
- known-zero drop/overflow counters combined with hardware acceptance filtering.

A self-declared `FULL_RATE_CANDIDATE` is not sufficient. Unknown counters remain unknown. An explicit `OBSERVATION_ONLY` declaration acts as a conservative ceiling unless an exact simultaneous reference comparison is supplied.

## Sequence and cycle provenance

Sequence statistics only establish completeness when their origin is explicit:

- `ADAPTER_MONOTONIC` can support a full-rate claim;
- `ROW_ORDINAL` records file order only and cannot prove that the adapter received every frame;
- `UNKNOWN` provides no continuity evidence.

FlexRay cycle values are similarly separated from schedule validation. Merely possessing a cycle field is not proof that all expected slots/cycles were captured.

## Timing result

Timing is reported separately:

- `PER_FRAME_CANDIDATE` — all timestamps claim supported per-frame provenance and do not regress;
- `TIMING_UNVERIFIED` — timestamps are host, batch, mixed or otherwise not characterized per frame;
- `INVALID` — timestamps regress;
- `UNKNOWN` — no records exist.

`PER_FRAME_CANDIDATE` remains a candidate classification; the existing golden-trace comparator is still required to quantify jitter and clock drift against a reference.

## Adapter-neutral use

The same decision model is usable for:

- canonical CAN captures imported from `candump` or Vector ASC;
- Panda captures when health/drop counters are retained;
- Vector/CANoe exports with an exact simultaneous comparison result;
- canonical FlexRay records;
- pico-flexray captures, where row ordinals and USB-batch timestamps remain explicitly insufficient for a full-rate/timing claim.

## Offline decoder integration

`validation/offline_can_decoder.py` now runs this evaluator before emitting observations. It preserves both the source-declared and evaluated qualities, but observation confidence uses the evaluated result.

Therefore a capture labelled `FULL_RATE_CANDIDATE` with unknown drop/overflow evidence is automatically downgraded to `OBSERVATION_ONLY` before decoding.

## CLI

```bash
python -m validation.capture_quality_evaluator capture.json
```

Optional supplemental evidence can be supplied with `--evidence evidence.json`. The supplemental object may contain sequence/cycle provenance and statistics or expected-rate validation. For CAN, reference-frame fidelity is never accepted as a manual field; it must come from `validation/can_trace_compare.py`, be bound to both capture-document hashes by `validation/capture_pair_manifest.py`, and be passed as a typed comparison report by the offline pipeline.
