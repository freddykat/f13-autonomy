# Simultaneous CAN trace comparison

`validation/can_trace_compare.py` compares two canonical CAN schema-v2 captures of the same physical bus interval. The intended use is a candidate adapter such as Panda or pico hardware captured simultaneously with a qualified reference such as Vector/CANoe.

The comparator is offline and receive-only. It has no SocketCAN, Panda, diagnostic, EPS, DSC, steering, braking, torque or transmit interface, and it does not contain BMW signal IDs or decoding assumptions.

## Frame alignment

Only `Rx` frames participate. `Tx` rows are counted and ignored. Frames are partitioned by:

- explicit logical channel;
- arbitration ID;
- standard versus extended format;
- remote-frame flag;
- DLC.

Within each partition, payload sequences are aligned with an insertion/deletion-aware sequence matcher. A single missing frame therefore does not turn every subsequent frame of the same ID into a false payload mismatch.

Channel names are never guessed. If the tools call the same physical bus `can0` and `asc:1`, explicit channel-map JSON objects must map both names to the same logical channel.

## Frame-fidelity results

- `EXACT`: both captures contain the same non-empty receive-frame sequence and payloads, the run is declared simultaneous, and the reference independently evaluates as `FULL_RATE_CANDIDATE`;
- `MISMATCH`: missing, extra or byte-divergent frames exist against a qualified simultaneous reference;
- `UNQUALIFIED_REFERENCE`: the frames match, but completeness of the reference itself is not established;
- `NOT_SIMULTANEOUS`: the captures were not declared as the same physical interval;
- `INVALID`: the comparison cannot establish a usable non-empty stream.

The report includes missing, extra and payload-mismatch counts plus bounded examples. `actuation_authority` is always `NONE`.

## Closing the manual `EXACT` path

For CAN, `capture_quality_evaluator.py` now rejects a manually supplied `reference_frame_fidelity`. It accepts only a `CanTraceComparisonReport` whose `candidate_capture_id` matches the capture being evaluated.

Therefore an `EXACT` result cannot be introduced through the generic evidence JSON. It must be calculated from the two canonical captures, and it promotes the candidate only when the comparison is simultaneous and the reference has its own independent full-rate evidence.

## Timing remains separate

When both sides contain trusted per-frame timing provenance, the comparator removes the median constant clock offset and reports median and maximum absolute residuals. Host/capture-tool/batch timestamps remain `TIMING_UNVERIFIED` even when frame fidelity is exact.

No interpolation is performed and an exact payload stream does not imply accurate timing.

## CLI

```bash
python -m validation.can_trace_compare \
  reference.json candidate.json \
  --simultaneous \
  --reference-channel-map reference-channels.json \
  --candidate-channel-map candidate-channels.json \
  --output comparison.json
```

The optional `--reference-quality-evidence` document may supply independently audited sequence, cycle or expected-rate evidence for the reference. It cannot manually supply reference-frame fidelity.
