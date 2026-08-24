# Upstream research snapshot — 2026-08-24

Purpose: keep Prototype 001 aligned with active public work while preserving the project's non-actuating M1 boundary.

## 1. openpilot / comma

### 0.11.2 direction
The public 0.11.2 milestone explicitly lists support for big models via external GPU/eGPU. The 0.11.2 release notes also describe an 880M-parameter model and external-GPU support.

Implication for f13-autonomy:
- do not build a deep custom fork solely to make big-model inference run off-device;
- keep the M1 logger/capture node lightweight and deterministic;
- isolate the perception compute behind standard openpilot/cereal/VisionIPC-compatible contracts where practical;
- track upstream camera and PC/researcher-experience changes before inventing equivalents.

Relevant upstream activity also includes ongoing camerad configuration work, logger changes, PC/replay tooling and researcher-experience issues. These are directly relevant to our shadow/replay architecture.

References:
- https://github.com/commaai/openpilot/milestone/42
- https://github.com/commaai/openpilot/blob/master/RELEASES.md
- https://github.com/commaai/openpilot/pulls
- https://blog.comma.ai/

## 2. BMW FlexRay / open-source tooling

### dynm/pico-flexray
`dynm/pico-flexray` is active public FlexRay tooling using RP2040-class hardware. It has recent activity and public discussion around passive capture and MITM behaviour.

A particularly relevant fork is:
- `gericho/pico-flexray-can`
- public description: "Czok Pico PANDA Firmware for BMW i3-specific FlexRay/CAN work"

There is also a BMW-oriented `gericho/opendbc` fork with default branch `bmw_i3_dev`.

Implication for f13-autonomy:
- evaluate pico-flexray first as a low-cost *passive bench/capture* research tool;
- compare its timestamp quality and captured frame fidelity against a known commercial interface before trusting it for motion validation;
- treat any MITM/transmission capability as out of M1 scope;
- inspect BMW i3 work for reusable framing, synchronization, controller configuration and logging ideas, not for blindly copying actuation assumptions onto F13.

References:
- https://github.com/dynm/pico-flexray
- https://github.com/gericho/pico-flexray-can
- https://github.com/gericho/opendbc

## 3. Tesla HW4 public CAN research

Public repositories now document observable HW4-era CAN messages such as `DAS_status`, `UI_driverAssistControl` and `UI_autopilotControl`, with signal naming linked to public Tesla CAN exploration work.

This is useful evidence that some HW4/FSD state is externally observable, but these projects often include message modification. That write path is **not** required for our teacher/benchmark goal.

For `teslaoracled`, only read-only observation should be considered:
- timestamped DAS/FSD state;
- speed-profile/follow-distance context;
- lane-change/driver-assist state where publicly decoded and legally obtained;
- version/build provenance;
- explicit UNKNOWN for undocumented fields.

No Tesla entitlement bypass, firmware extraction, or message injection is part of M1.

References:
- https://github.com/sahilcc7/tesla_can
- https://github.com/jvanakker/tesla-fsd-can-mod

## 4. Safe integration decision

### M1 architecture remains

```text
BMW buses / GNSS / IMU / cameras
          |
          v
 deterministic logger
          |
          +--> replay store
          |
          +--> openpilot observer / big model on external GPU
          |
          +--> BMW state + world model + shadow planner
```

The logger remains independent from heavy inference. A perception crash or eGPU disconnect must not corrupt source capture.

## 5. New validation task

Before purchasing a commercial FlexRay interface, build a *passive-only FlexRay evaluation bench* with one of the public RP2040 FlexRay implementations and compare it to a trusted capture source when available.

Acceptance criteria:
1. receive-only mode is physically/configurationally enforced;
2. raw frames retain channel, slot/frame identity and local monotonic timestamp;
3. frame-error/drop counters are recorded;
4. capture continues through source loss/recovery without fabricated frames;
5. no transmission/MITM code is enabled in the Prototype 001 M1 configuration;
6. captured traces can be replayed into a parser without vehicle hardware;
7. any decoded BMW signal stays UNKNOWN until cross-validated against an independent observation or authoritative diagram/log.

## 6. Collaboration targets

High-signal public projects/developers discovered in this pass:
- `dynm/pico-flexray` — active FlexRay implementation/tooling;
- `gericho/pico-flexray-can` / `gericho/opendbc` — BMW i3-specific FlexRay/CAN work;
- comma/openpilot contributors working on PC, replay, camera configuration and external-GPU support.

Outreach should be narrow: ask for passive-capture/timestamping lessons and BMW-specific framing/tooling experience. Do not ask external maintainers to validate or enable safety-critical actuation.
