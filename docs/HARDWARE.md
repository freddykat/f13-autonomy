# Hardware Plan

## Development philosophy

Start the physical Beta from a supported upstream hardware/runtime combination: comma four, Panda and the locked openpilot release. Scale sidecar GPU/camera hardware only when measurements justify it.

## Development compute

Initial in-car target:

- comma four for upstream cameras, driver monitoring, openpilot runtime and route logging
- Panda-compatible read-only CAN connection
- independent deterministic BMW/FlexRay logger where Panda cannot see the required bus
- optional sidecar computer for 360-camera capture and offline/world-model experiments

An x86-64/NVIDIA workstation remains useful for replay and later perception research, but it is not required in the car for the first Beta. A high-end RTX 5080 is not an early dependency.

## Camera system

The comma camera set is the first model input. A separate synchronized surround set may then expand toward:

- front tele
- front main
- front wide
- front-left/right
- side-left/right
- rear-left/right
- rear-centre

Final target should favour automotive HDR sensors, hardware synchronization and automotive transport such as GMSL-class links.

## Sidecar camera interface

Desired capabilities:

- multi-channel deserialization
- common clock / trigger
- timestamp integrity
- camera power distribution
- low-copy path toward GPU memory
- temperature/health monitoring

## Safety / vehicle interface board

Candidate MCU class: STM32H7-family / panda-compatible approach.

Interfaces to investigate:

- multiple CAN
- CAN-FD
- FlexRay transceiver/controller path
- watchdog
- ignition/wake
- hardware autonomy kill
- USB/Ethernet host link

## BMW donor/HIL hardware

Useful donor components may include:

- EPS/steering hardware
- ICM
- DSC
- relevant harness/connectors
- ACC radar
- KAFAS/Parking modules as needed

## Tesla benchmark hardware

Prefer a same-donor electronic set where possible rather than a random isolated HW4. Research priority is a genuine HW4/FSD environment that can provide read-only benchmark behaviour.

No expensive HW4 purchase should be made until the minimum viable bench requirements are better understood.
