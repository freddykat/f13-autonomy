# BMW F13 CAN / FlexRay / EPS Integration

## Purpose

Map and preserve the BMW F-series OEM dynamics architecture instead of bypassing it with crude external actuators.

Primary systems of interest:

- ICM
- DSC
- EPS / steering architecture
- DME
- ACC radar
- KAFAS
- wheel-speed and chassis sensors
- CAN / CAN-FD where applicable
- FlexRay

## Guiding principle

The autonomy computer should issue abstract vehicle requests. BMW-specific translation belongs in `bmwcontrold`, with an independent safety MCU between Linux/GPU compute and the vehicle networks.

```text
openpilot / planner
       ↓
VehicleCommand
       ↓
bmwcontrold
       ↓
Safety MCU
       ↓
CAN / FlexRay
       ↓
ICM / DSC / EPS / DME
```

## Initial state signals to map

- individual wheel speeds
- vehicle speed
- steering angle
- driver steering torque/input
- yaw rate
- longitudinal/lateral acceleration
- brake state
- accelerator state
- gear
- indicators
- DSC intervention state
- EPS availability/fault state
- ACC/radar tracks if accessible

## Lateral-control research

We need to identify the safest OEM-compatible request path for lateral control and understand which F-series steering variant best supports it.

Questions:

1. Which F13/F12/F10 configurations provide the most useful EPS/ADAS control path?
2. Which messages are CAN and which are FlexRay?
3. What counters, CRCs, startup/state machines and plausibility checks exist?
4. How does ICM arbitrate steering/dynamics requests?
5. How is driver override represented and enforced?

## Longitudinal-control research

The high-level planner should output target speed/acceleration, not raw brake/throttle actuator signals.

Research must determine how OEM ACC/DSC/DME coordinate longitudinal requests and which interfaces can be safely reused.

## Bench/HIL first

Before any moving-vehicle actuation, use donor modules where possible:

```text
bmwcontrold
    ↓
Safety MCU
    ↓
CAN/FlexRay bench
    ↓
EPS / ICM / DSC donor modules
```

The first objective is decoding and state observation; actuation comes only after replay, simulation and HIL validation.
