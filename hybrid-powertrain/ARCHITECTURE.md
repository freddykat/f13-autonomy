# Architecture Notes

## EV
```text
N63 = stopped
K0 = open
HV battery -> EME -> e-machine -> 8P75 -> xDrive -> wheels
```

## Hybrid
```text
N63 -> K0 closed -> e-machine/8P75 -> xDrive
                 ^
                 |
           electric assist
```

## Regeneration
```text
wheels -> xDrive -> 8P75 -> e-machine generator -> EME -> HV battery
```

## ICE charge / battery hold
The e-machine, not the 12 V alternator, should be the HV generator.

```text
N63 -> K0 -> e-machine generator -> HV battery
```

## Controls split

### DME / MSD85_HY
- combustion, boost, ignition and knock protection;
- ICE torque model;
- ICE start/stop state.

### EGS
- gear selection and clutch control;
- K0 coordination where implemented by the transmission;
- torque-intervention requests;
- transmission protection.

### EME
- e-machine inverter control;
- motor/generator torque;
- thermal protection.

### BMS / SME-equivalent
- SOC/SOH;
- cell voltage and temperature;
- contactors / precharge;
- charge/discharge power limits;
- isolation / HVIL state.

### Hybrid supervisor
- operating-mode arbitration;
- F-series <-> PHEV message translation;
- EV permission;
- ICE start request;
- torque blending;
- safety-state supervision.

The supervisor should not replace inner control loops already handled by the DME, EGS or EME.
