# BMWVehicleState

`BMWVehicleState` is the unified read-only vehicle telemetry contract for Prototype 001.

The design principle is simple:

> If the BMW knows it, and the signal is useful, timestampable and trustworthy, the autonomy stack should be able to observe it.

Observation does **not** imply actuation authority.

## Top-level structure

```text
BMWVehicleState
├── chassis
├── powertrain
├── adas
├── parking
├── body
├── driver
├── environment
├── energy
└── health
```

Every signal should carry or inherit:

- source
- timestamp
- validity
- stale state
- unit
- confidence where appropriate

Missing or stale data must not silently become zero.

## chassis

Candidate fields:

- vehicleSpeed
- wheelSpeedFL
- wheelSpeedFR
- wheelSpeedRL
- wheelSpeedRR
- steeringWheelAngle
- frontSteerAngle
- rearSteerAngle
- rearSteerAvailable
- rearSteerActive
- yawRate
- lateralAcceleration
- longitudinalAcceleration
- epsState
- icmState
- dscState
- dscIntervention
- tractionLimited
- suspensionMode
- brakePressure where available

`BMWChassisState` remains the more detailed chassis-specific sub-contract.

## powertrain

Candidate fields:

- engineRpm
- acceleratorPosition
- gear
- transmissionMode
- driveMode
- requested/actual torque where safely observable
- coolantTemperature
- oilTemperature
- transmissionTemperature
- boost/charge state where useful and available
- xDrive/torque-distribution state where trustworthy
- shiftInProgress
- kickdownState
- powertrainLimited

These states feed `bmwdynamicsd` for longitudinal capability prediction.

## adas

Candidate fields:

- ACC state
- radar object/tracks
- KAFAS state
- lane/road-sign detections where exposed
- FCW state
- blind-spot state
- cruise target speed
- OEM speed-limit state
- driver-assistance availability/faults

ADAS sensor outputs should not be treated as ground truth; they are additional observations for fusion.

## parking

Candidate fields:

- PDC distance/sector data
- Parking High state
- surround-camera state
- parking-camera availability
- park-assist state
- near-field obstacle state
- park-brake state

This group supports parking, low-speed world modelling and future supervised Summon.

## body

Candidate fields:

- door states
- bonnet state
- boot/trunk state
- lock state
- mirror state
- window state
- exterior lighting state
- brake-lamp state
- indicator state
- hazard state
- wiper state

## driver

Candidate fields:

- brakePedalPressed
- acceleratorPosition
- steeringTorque / steeringOverride where available
- turnSignalCommand
- gearSelector state
- seatbelt state
- driverDoor state
- driverMonitoring state from custom system

Driver inputs always have priority over remote or autonomous requests.

## environment

Candidate fields:

- outsideTemperature
- rainSensor state
- ambientLight state
- OEM GNSS position/heading where useful
- road-grade estimate from fused sources

## energy

Candidate fields:

- fuelLevel
- estimatedRange
- 12V system voltage
- alternator/charging state
- brake-energy-regeneration/overrun charging state where observable
- battery state relevant to compute wake/sleep management

The BMW's Brake Energy Regeneration system should be treated as an energy-management state, not as EV-style regenerative braking unless measured deceleration proves otherwise.

## health

Candidate fields:

- busHealthCAN
- busHealthFlexRay
- epsHealthy
- icmHealthy
- dscHealthy
- iasHealthy
- radarHealthy
- kafasHealthy
- parkingHealthy
- powertrainHealthy
- requiredSensorsHealthy
- diagnosticSummary
- degradedMode

## Consumer mapping

```text
BMWVehicleState
   |
   +--> motionvalidatord
   |      chassis / motion
   |
   +--> bmwdynamicsd
   |      powertrain / longitudinal capability
   |
   +--> worldmodeld
   |      radar / KAFAS / parking / environment
   |
   +--> trafficlawd / HMI
   |      indicators / speed / mode / navigation context
   |
   +--> sentry / black-box
          body / security / event state
```

## Raw vs normalized data

The stack should preserve access to raw bus logs for reverse engineering and replay, while `BMWVehicleState` only contains normalized, versioned, semantically understood signals.

```text
CAN / FlexRay / LIN / diagnostics
          |
          v
      raw logger
          |
          v
       bmwstated
          |
          v
   BMWVehicleState
```

Unknown IDs or partially understood signals remain outside the trusted normalized interface until validated.

## Versioning

Signals must be versioned by vehicle configuration and source where needed. Prototype 001 may differ from other F13/F12/F10 variants, so the interface should not assume all cars expose identical states.

## Safety boundary

`BMWVehicleState` is observational. It must not contain hidden side effects, write functions or actuator command paths.
