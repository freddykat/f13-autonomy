# Reproducible openpilot base

## Decision

Prototype 001 now treats a real upstream openpilot build as its executable base. The project services are integrations around that base, not a replacement driving stack and not a deep copy of openpilot source.

The first Beta profile is:

```text
comma four + Panda
        |
openpilot 0.11.2 (locked)
        |
BMW read-only CarState/RadarInterface overlay
        |
project sidecars and offline validation
```

Custom compute and custom camera hosting remain later options. They are no longer prerequisites for the first shadow Beta.

## Locked baseline

| Component | Ref | Locked commit |
|---|---|---|
| openpilot | release `0.11.2`, branch `zeroeleventwo` | `044640668aa25d5c72f948ec072bfc259d1b269a` |
| opendbc | submodule selected by that openpilot commit | `b4ef5e1cf406ff143fa67bdbfb154739d43279c9` |
| panda | submodule selected by that openpilot commit | `dd8a5b3df77706337a11555377e7180c5adc8726` |

The machine-readable source is `upstream/openpilot.lock.json`. `master` is recorded only as an update snapshot. A moving branch is not used directly for a vehicle build.

## Why openpilot is not copied into this repository

Keeping an external, detached checkout provides three useful properties:

1. upstream history and submodules remain intact;
2. the exact executable base can be recreated and audited;
3. BMW changes stay small enough to rebase or reject independently.

The project must never silently apply patches after an upstream branch moves.

## Prepare a workspace

Validate the lock and shadow-only overlay without downloading anything:

```bash
python tools/openpilot_workspace.py validate
```

Create the complete external checkout:

```bash
python tools/openpilot_workspace.py prepare \
  .openpilot-workspace/openpilot-0.11.2 \
  --with-submodules
```

Verify an existing checkout:

```bash
python tools/openpilot_workspace.py verify \
  .openpilot-workspace/openpilot-0.11.2
```

The prepare command refuses a non-empty target. It also aborts if the named upstream ref no longer resolves to the reviewed commit.

## Correct extension points in openpilot 0.11.2

Vehicle integrations live in openpilot's `opendbc_repo` submodule. The eventual BMW package belongs below:

```text
opendbc_repo/opendbc/car/bmw/
├── values.py
├── interface.py
├── carstate.py
└── radar_interface.py
```

There is deliberately no `carcontroller.py` in the shadow phase.

The current upstream `openpilot/selfdrive/car/card.py` loads the selected `CarInterface` and `RadarInterface`, publishes `carState` and publishes radar points as `radarTracks`. This lets the F13 integration use standard openpilot contracts without modifying `modeld`.

## BMW sensor mapping

| F13 source | First openpilot boundary | Beta use |
|---|---|---|
| Wheel speed, steering, pedals, indicators, cruise state | `CarState` | Ego state and driver input |
| Front `ACC-SEN` radar | `RadarInterface` / `radarTracks` | Lead distance, lateral position and relative speed if present at the ZGM/OBD capture point |
| Left/right `SWW` radar | `CarState.leftBlindspot` / `rightBlindspot` | Blind-spot state |
| KAFAS | Project observation sidecar first | Cross-check lanes, signs and warnings without pretending it is an openpilot camera |
| comma road/wide/cabin cameras | Upstream camera and VisionIPC path | Unmodified driving and driver-monitoring model input |
| Additional 360 cameras | Separate synchronized logger / `worldmodeld` | Surround perception experiments; not forced into the upstream model input |

The F13 sensor inventory must not invent modern surround radars. The vehicle has the front ACC radar and, when equipped, the two SWW blind-spot radars; parking coverage is principally cameras and ultrasonics.

## First BMW port state

`integration/openpilot/overlay_manifest.json` is the review boundary. For the first implementation it requires:

- `SHADOW_ONLY`;
- `actuation_authority = NONE`;
- `dashcamOnly`/Panda `noOutput` behaviour;
- no `sendcan` use;
- no BMW `CarController`;
- no Panda safety patch;
- no FlexRay transmission;
- no Tesla-to-BMW command translation.

The BMW package should initially consume only signals already accepted by the decoder evidence pipeline. Unknown IDs, scaling and validity values remain outside the executable port.

## Upgrade procedure

An openpilot update is a deliberate review, not a version-string edit:

1. resolve the candidate upstream commit and all critical submodule gitlinks;
2. run upstream replay/model and car-interface tests;
3. run this repository's CAN/FlexRay, state, Tesla benchmark and safety-boundary tests;
4. compare model outputs on the frozen BMW replay corpus;
5. record regressions and only then update the lock and overlay target together.

No update may promote the system from shadow mode to vehicle control.
