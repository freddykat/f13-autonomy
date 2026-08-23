# Smart Key, Phone Key and Supervised Summon

## Objective

Prototype 001 should modernise access and low-speed vehicle interaction as well as highway assistance.

The target is an OEM-like BMW experience combining the original secure vehicle access architecture with a modern smart-key layer, phone interaction and a tightly constrained **supervised low-speed summon/remote parking research mode**.

This document is a concept and safety requirements document, not an implementation of vehicle actuation.

## Smart-key philosophy

The project should not weaken or bypass the BMW immobiliser/CAS security model merely to add convenience features.

Preferred principle:

```text
phone / wearable / smart fob
          |
 authenticated convenience layer
          |
       BMW access
          |
 original immobiliser/start authorization
```

The convenience layer may request authorized actions, but starting/driving authorization should retain a proper cryptographic/security boundary rather than relying on an easily replayed radio or CAN message.

## Desired smart-key functions

Potential MY2026 functions:

- passive lock/unlock where securely implementable
- phone-as-key research
- owner proximity detection
- welcome lighting
- mirror/seat/profile preparation
- climate/preconditioning requests where supported
- boot/trunk release
- vehicle status in companion UI
- locate-car function
- temporary/digital guest-key concept with explicit expiry
- explicit remote-parking/summon authorization

## Authentication

Any custom remote-control path should use modern authenticated and encrypted communication, anti-replay counters/nonces, short-lived sessions and revocable credentials.

A lost phone must not become equivalent to an permanently cloned BMW key.

Biometric/PIN confirmation on the phone should be considered for high-impact actions such as remote movement.

## Supervised Summon concept

Summon is deliberately separated from normal road autonomy.

The initial useful target is not an unsupervised car driving through a public car park. It is **very low-speed, line-of-sight remote manoeuvring** for situations such as:

- moving out of a tight parking space
- moving into a narrow garage
- pulling forward/backward to allow door access
- short private-driveway manoeuvres

The operator remains responsible and must actively supervise the manoeuvre.

## Proposed operating envelope

Initial research constraints should be conservative:

- walking-speed maximum
- very short distance per authorization
- line-of-sight operator supervision
- private property / controlled testing first
- no public-road autonomous summon target in early milestones
- no high-speed steering
- no route following beyond the validated low-speed parking domain
- continuous obstacle monitoring

Exact speed/distance limits must be chosen from testing and applicable regulation rather than assumed here.

## Dead-man interaction

Remote movement should require continuous deliberate operator input rather than a single 'go' command.

Concept:

```text
AUTHENTICATE
    |
HOLD TO MOVE
    |
vehicle moves at constrained speed
    |
release / connection loss / obstacle / fault
    |
STOP
```

This is preferable for the first implementation to allowing the vehicle to continue after the operator stops interacting.

## Sensor requirements

Summon should require a healthy low-speed perception set before movement is permitted.

Candidate inputs:

- surround cameras
- front/rear/side camera coverage
- BMW PDC ultrasonic sensors
- Parking High data where available
- wheel speeds
- steering angle
- gear state
- brake state
- door/bonnet/boot state
- obstacle/free-space model

Radar may supplement the system where useful but should not substitute for near-field sensing.

## Independent safety boundary

The phone/app does not directly send steering/throttle/brake actuator commands.

Concept:

```text
PHONE / SMART KEY
       |
authenticated intent
       |
SUMMON SUPERVISOR
       |
low-speed planner
       |
SAFETY MCU / VEHICLE SAFETY GATE
       |
BMW control interfaces
```

The safety layer should enforce the low-speed operating envelope independently of the high-level computer.

## Mandatory stop conditions

The design should treat at least the following as immediate stop/cancel conditions:

- operator releases dead-man control
- communication/authentication session lost
- obstacle enters protected envelope
- perception confidence insufficient
- camera/PDC required sensor fault
- unexpected vehicle motion
- door/bonnet/boot opens
- driver brake/steering intervention
- EPS/DSC/control fault
- main compute watchdog failure
- safety MCU rejects command
- speed exceeds allowed envelope

## Occupant interaction

If a driver is seated in the vehicle and takes control, human input must dominate remote control.

Remote movement should never fight steering or braking input from an occupant.

## Companion UI concept

A future phone UI could expose:

```text
PROTOTYPE 001

Locked
Fuel / range
Vehicle location
Camera/security status

[ Unlock ]
[ Climate ]
[ Locate ]

REMOTE PARKING
[ Authenticate ]
```

After explicit authentication, the remote-parking view should show camera/perception status, obstacle warnings, connection health and a hold-to-move control.

## Relationship to sentry/security

The same secure companion layer can eventually support vehicle event notifications and access to stored security events, while keeping autonomy/control credentials separated from ordinary telemetry where practical.

## Development stages

### SK0 — Documentation and threat model

Define credentials, trust boundaries, attack surfaces, loss-of-phone handling and replay resistance. No vehicle control.

### SK1 — Read-only companion

Vehicle state, lock state, location and event/status viewing only.

### SK2 — Convenience actions

Authenticated non-driving functions such as lighting or other OEM-supported comfort requests, tested without weakening immobiliser security.

### SK3 — Summon simulator

Phone UI controls a simulated vehicle/world model. Test dead-man logic, latency, disconnects and stop conditions.

### SK4 — HIL remote parking

Safety gate and BMW control interfaces exercised on a bench/HIL environment.

### SK5 — Controlled low-speed vehicle test

Private controlled environment, walking speed, line of sight and an independent physical emergency stop.

### SK6 — Validated supervised remote parking

Only after defined test coverage, failure-injection testing and regulatory review.

## Non-goals

Early versions are not intended to provide:

- unattended public-car-park summon
- autonomous road driving initiated remotely
- immobiliser bypass
- remote high-speed operation
- hidden tracking/control of another person's vehicle

## MY2026 vision

Smart access and summon should feel like part of the same coherent vehicle modernisation as the digital cabin and autonomy stack: useful, restrained and OEM-like rather than a collection of aftermarket remote-control hacks.
