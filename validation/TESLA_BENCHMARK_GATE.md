# Tesla behavioural benchmark gate

## Purpose

Tesla HW4/FSD is a behavioural reference, not the BMW controller and not automatic ground truth. This gate decides whether Tesla observations and openpilot outputs have enough provenance to support offline comparison.

It does not contain Tesla CAN IDs, write functions, configuration spoofing or actuator translation.

## Best verification arrangement

The strongest useful dataset is collected on a genuine Tesla while:

- genuine HW4/FSD runs normally;
- a separate comma/openpilot instance runs in shadow/no-output mode;
- both observe the same physical episode;
- video/UI evidence and read-only Tesla state are timestamped;
- recorder loss counters and filter mode are retained.

That permits `Tesla behaviour vs openpilot proposal vs actual vehicle response vs human review` on the same event without connecting Tesla outputs to BMW actuators.

When the two systems did not observe the same physical event, the corpus must say `MATCHED_SCENARIO`. Similar roads or manoeuvres are useful research, but they cannot claim frame-level or temporal equivalence.

## Comparison modes

| Mode | Meaning | Maximum result |
|---|---|---|
| `SAME_EPISODE` | Tesla and openpilot observed the same event | `BEHAVIOURAL_COMPARISON_READY` |
| `REPLAY_SAME_INPUT` | Outputs are aligned to one frozen input timeline | `BEHAVIOURAL_COMPARISON_READY` |
| `MATCHED_SCENARIO` | Similar scenario, different physical episode | `SCENARIO_BENCHMARK_ONLY` |

`BEHAVIOURAL_COMPARISON_READY` authorizes only offline analysis and human review.

## Required provenance

Each episode binds:

- exact openpilot commit and model artifact;
- Tesla hardware generation, vehicle platform, firmware/FSD version;
- capture IDs, bus and physical tap;
- openpilot camera-drop and skipped-model-frame counters;
- Tesla decoder version;
- clock domain and timestamp origin for both systems;
- capture quality, hardware filter mode and drop/overflow counters;
- alignment method and measured maximum error;
- field-level evidence and explicit `UNKNOWN` values;
- `write_path_present = false` and `actuation_authority = NONE`.

An all-ID logger with silent queue overflow cannot qualify a benchmark even when its decoder appears correct. Unknown counters remain unknown; they are not treated as zero.

## Evidence levels for Tesla fields

| Status | Requirement |
|---|---|
| `UNKNOWN` | `value = null`, no invented default |
| `OBSERVED` | At least one recorded evidence type |
| `CROSS_SOURCE_VALIDATED` | At least two independent types, such as CAN observation plus UI video |

Firmware-dependent message layouts must use distinct decoder versions. A mapping seen on one HW4 car or release does not become a global Tesla mapping.

## Classifications

```text
REJECTED
OBSERVATION_ONLY
SCENARIO_BENCHMARK_ONLY
BEHAVIOURAL_COMPARISON_READY
```

The gate rejects any write path, non-null value labelled `UNKNOWN`, mismatched openpilot baseline or malformed provenance. It downgrades loss, unknown counters, USB batch timestamps and weak alignment to observation only.

## Initial episode suite

The first corpus should prioritize events whose outcome can be independently reviewed:

1. lead vehicle acquisition/loss and stopped lead;
2. cut-in and cut-out;
3. curve speed and lane centring;
4. driver-confirmed lane change;
5. blind-spot occupied/free transition;
6. merge and exit preparation;
7. forward-collision warning;
8. sensor blockage or degraded-system behaviour.

For each episode compare normalized intent and trajectory rather than copying raw Tesla steering or acceleration request values.

## Smoke fixture and command

`validation/corpus/tesla_benchmark_smoke.json` is synthetic and contains no real Tesla decoding.

```bash
python -m validation.tesla_benchmark_gate \
  validation/corpus/tesla_benchmark_smoke.json \
  --expected-openpilot-commit 044640668aa25d5c72f948ec072bfc259d1b269a
```

The output can feed `disagreementd`, the replay corpus and the future human-review UI only when it is not `REJECTED`.
