# Camera System

## Objective

Use the comma road/wide/cabin cameras as the known openpilot input for the first Beta, while developing synchronized, low-latency 360-degree perception as a separate evidence/world-model layer.

## Initial concept

Potential views:

- front tele
- front main
- front wide
- front-left
- front-right
- side-left
- side-right
- rear-left
- rear-right
- rear-centre

The final camera count is deliberately open. Angular coverage, overlap, HDR, synchronization, calibration stability and latency matter more than raw count or resolution.

## Development stages

### Stage A — openpilot shadow baseline

Run the locked upstream model with the comma cameras. Log calibration, frame timing, dropped frames and model outputs without BMW actuation.

### Stage B — minimum useful sidecar

Start with a small synchronized side/rear subset that supports logging and lane-change/blind-spot comparison. Do not disguise these views as upstream road/wide streams.

### Stage C — highway surround coverage

Add rear/side overlap for blind spots, fast-approaching vehicles, merges and automatic lane changes.

### Stage D — full world perception

Expand toward 360-degree occupancy/world modelling if the measured value justifies the added bandwidth and compute.

## Transport

Prototype sidecar transport may use USB/development capture hardware. Final vehicle target should favour automotive links such as GMSL-class transport with a common clock and robust connectors/cabling. Extra cameras remain separate from the upstream model until their image geometry, timing and calibration have been validated.

## openpilot integration

Later custom-camera abstraction:

```text
camera sensors
     ↓
capture / ISP / synchronization
     ↓
our_camerad
     ↓
VisionIPC-compatible output
     ↓
modeld
```

A higher-spec camera is not automatically better if its FOV, distortion, timing, exposure or preprocessing differ significantly from what the driving model expects. Camera selection and preprocessing must therefore be validated against model performance, not only sensor specifications.

## Calibration

Every camera requires stable intrinsics and extrinsics in a common BMW ego coordinate system. Temporal calibration/synchronization is equally important at motorway speeds.

## Data path goal

Minimize unnecessary CPU memory copies and maintain reliable timestamps from sensor capture through inference and logging.
