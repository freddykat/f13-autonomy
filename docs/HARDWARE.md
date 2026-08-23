# Hardware Plan

## Development philosophy

Start with the cheapest hardware that allows useful logging, replay, model execution and interface development. Scale GPU/camera hardware only when measurements justify it.

## Development compute

Initial target:

- affordable x86-64 platform
- 32–64 GB RAM
- 1–2 TB NVMe minimum
- NVIDIA GPU with enough VRAM for current openpilot/model experiments
- Ethernet/USB/PCIe expansion
- robust DC/DC power strategy for vehicle use later

A high-end RTX 5080 is not required for early development. The architecture should allow a later GPU upgrade without redesigning the software interfaces.

## Camera system

Prototype phase may begin with a small synchronized set, then expand toward:

- front tele
- front main
- front wide
- front-left/right
- side-left/right
- rear-left/right
- rear-centre

Final target should favour automotive HDR sensors, hardware synchronization and automotive transport such as GMSL-class links.

## Camera interface

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
