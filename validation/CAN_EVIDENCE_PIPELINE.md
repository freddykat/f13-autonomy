# Beta-0 CAN evidence pipeline

`validation/can_evidence_pipeline.py` turns the existing CAN evidence gates into one deterministic offline operation:

1. bind reference and candidate captures to a hash-checked session manifest;
2. compare logical channels, frame selectors and payload sequences;
3. evaluate candidate acquisition quality;
4. run the evidence-gated decoder manifest;
5. emit one audit report with a Beta-0 verdict.

The verdict is:

- `READY_FOR_REPLAY_REVIEW` when a verified pair has exact frame fidelity and the candidate evaluates as `FULL_RATE_CANDIDATE`;
- `REJECTED` when a qualified reference exposes missing, extra or divergent candidate frames, or other acquisition evidence makes the candidate `LOSSY`;
- `OBSERVATION_ONLY` when the data remain useful but completeness or pair synchronization is not established.

This verdict grants no vehicle-state or actuation authority. Every layer in the returned document declares `actuation_authority = NONE`.

## Reproducible smoke corpus

`validation/corpus/can_beta0/` contains a synthetic, explicitly non-BMW pair:

- `reference.json` — qualified synthetic reference capture;
- `candidate.json` — synthetic candidate with unknown local drop counters;
- `pair_spec.json` — session, tap, synchronization evidence and explicit channel maps;
- `expected_summary.json` — deterministic expected outcome.

The production BMW decoder manifest remains empty, so the golden run proves acquisition, comparison and safety plumbing while producing zero decoded BMW observations.

## One-command run

From the repository root:

```bash
python -m validation.can_evidence_pipeline \
  validation/corpus/can_beta0/reference.json \
  validation/corpus/can_beta0/candidate.json \
  validation/manifests/prototype_001_bmw_decoders.json \
  validation/corpus/can_beta0/pair_spec.json \
  --vehicle-profile prototype-001-f13-650i-xdrive-2012 \
  --output beta0-report.json
```

No CAN, FlexRay, ENET, EPS or DSC connection is opened. The runner reads JSON and writes JSON only.
