# Capture-pair manifest

`validation/capture_pair_manifest.py` binds two canonical CAN capture documents to one physical recording session before they may be compared as a reference pair.

The manifest replaces a free-standing `simultaneous=true` assertion with an auditable contract containing:

- pair and session identifiers;
- logical bus and physical tap description;
- reference and candidate capture IDs;
- SHA-256 of both complete canonical capture documents;
- same-physical-interval declaration;
- synchronization method and concrete evidence;
- `actuation_authority = NONE`.

Canonical hashes are calculated over deterministic sorted JSON. Any later change to payloads, timestamps, provenance, adapter metadata or capture-quality counters invalidates the pair.

## Synchronization quality

The supported methods are:

- `SHARED_CLOCK` — both recorders use the same declared clock domain;
- `HARDWARE_TRIGGER` — a hardware trigger binds the recording interval;
- `OBSERVED_MARKER` — both recordings contain a documented common event marker;
- `MANUAL_ASSERTION` — an operator states that the intervals are the same.

The first three produce `sync_quality = VERIFIED` when their structural requirements pass. `MANUAL_ASSERTION` remains `DECLARED_ONLY` and cannot produce an `EXACT` frame-fidelity result or promote capture quality.

This is evidence integrity, not cryptographic attestation of the capture hardware. A future signed acquisition manifest may strengthen the boundary further.

## CLI

```bash
python -m validation.capture_pair_manifest \
  vector-capture.json candidate-capture.json \
  --pair-id f13-pair-001 \
  --session-id f13-session-001 \
  --logical-bus vehicle-can \
  --physical-tap "gateway breakout, receive-only" \
  --same-physical-interval \
  --sync-method OBSERVED_MARKER \
  --sync-evidence "shared ignition transition at start" \
  --output pair.json
```

This module is offline-only and contains no CAN/FlexRay transmission or vehicle-control interface.
