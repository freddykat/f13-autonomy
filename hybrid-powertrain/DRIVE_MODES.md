# Propulsion and Drive-Mode Strategy

The project will use a **parallel P2 hybrid** architecture with a disconnect clutch (K0).

We are deliberately **not** pursuing a dedicated series-hybrid / range-extender mode.

When the N63 is off:
- K0 open;
- e-machine propels the vehicle through the 8P75 and xDrive;
- true EV operation.

When the N63 is on:
- K0 closed;
- the N63 can propel the wheels directly;
- the e-machine can assist, regenerate, or generate electrical power from surplus ICE torque.

The objective is to make propulsion behavior feel native to BMW drive modes rather than expose the driver to engineering states.

## Core operating states

### EV
```text
N63 = OFF
K0 = OPEN
battery -> EME -> e-machine -> 8P75 -> xDrive
```

### Hybrid propulsion
```text
N63 -> K0 CLOSED -> 8P75 -> xDrive
                     ^
                     |
               e-machine assist
```

### ICE propulsion + battery charging
```text
N63 -> K0 CLOSED -> 8P75 -> xDrive
                     |
                     +-> e-machine generating -> HV battery
```

Charging from the engine is not a permanent behavior. The supervisor should only request generator torque when:
- battery SOC is below the mode reserve target;
- the N63 is operating in a favorable efficiency region;
- there is enough torque margin to propel the car without poor drivability;
- thermal limits permit it.

Avoid inefficient behavior where the engine continuously burns fuel only to cycle energy through the battery.

## Drive modes

These are initial calibration targets, not final fixed values.

### ECO PRO

Primary objective:
**minimum energy cost for daily commuting.**

Default:
- EV-first;
- N63 off;
- K0 open;
- soft accelerator map;
- maximum sensible regenerative recovery;
- reduced HVAC/auxiliary load where acceptable.

ICE start conditions can include:
- SOC below lower reserve;
- requested power above safe EV capability;
- sustained speed/load outside efficient EV operation;
- battery/inverter thermal limits;
- drivetrain protection requirements.

When the N63 starts:
- K0 closes after synchronization;
- engine provides direct wheel propulsion;
- supervisor targets a favorable BSFC/load region;
- moderate generator torque can be added to rebuild a small SOC reserve.

Suggested initial SOC strategy:
- normal EV use down toward ~20–25%;
- once ICE is required, rebuild toward ~30–35% when efficient;
- avoid charging toward high SOC using fuel.

This mode should be optimized to make the daily commute cheaper in energy cost than the reference DS3 1.2 VTi.

### NORMAL / COMFORT

Primary objective:
**smooth automatic hybrid operation.**

Default:
- EV at low/medium load and urban speeds;
- earlier ICE engagement than ECO;
- seamless K0 synchronization;
- moderate electric torque fill;
- regenerative braking prioritized before friction braking where stability and pedal feel allow.

ICE charging:
- maintain a useful hybrid buffer rather than maximize SOC;
- target roughly ~30–40% reserve;
- charge mainly when the engine is already operating efficiently.

The driver should not normally notice whether propulsion is EV, ICE or blended.

### SPORT

Primary objective:
**response and sustained performance.**

Default:
- N63 normally running;
- K0 closed;
- e-machine used for torque fill and transient boost;
- faster shift strategy;
- sharper accelerator calibration;
- maintain enough SOC for repeated electric assist.

Battery behavior:
- target a larger performance reserve, approximately ~35–45%;
- opportunistic charging during efficient cruise / low-demand phases;
- regen remains active but calibrated for predictable sporty pedal/lift-off behavior.

No unnecessary fuel-driven charging while the driver is requesting performance.

### SPORT+

Primary objective:
**maximum road-performance response with reduced intervention.**

Default:
- N63 continuously available;
- K0 closed;
- aggressive e-boost;
- faster gearbox response;
- more permissive DSC calibration subject to OEM safety architecture;
- battery reserved primarily for propulsion rather than deliberate charging.

Battery behavior:
- no significant ICE charging unless SOC falls below a minimum performance reserve;
- stronger thermal monitoring;
- preserve enough SOC for repeated boost.

Suggested activation reserve:
- ~30% minimum preferred;
- warn/reduce e-boost below the calibrated threshold.

### M MODE 1

Custom **fast-road / GT performance** profile.

Suggested baseline:
- N63 always available;
- K0 normally closed;
- strong but progressive e-boost;
- performance shift program;
- MDM / intermediate stability setting if the final DSC integration supports it;
- active battery reserve management.

Suggested SOC target:
- ~40–50%.

M1 should be repeatable and usable for sustained spirited driving without exhausting the battery immediately.

### M MODE 2

Custom **maximum attack** profile.

Primary objective:
maximum combined performance within validated mechanical and thermal limits.

Behavior:
- N63 permanently active;
- K0 closed;
- maximum allowed e-machine assist;
- most aggressive shift logic;
- minimum permitted stability intervention according to final validated DSC configuration;
- battery thermal preconditioning where hardware permits;
- no intentional fuel-driven charging during an acceleration event.

Before activation, the system should preferably have:
- sufficient battery SOC;
- battery within performance temperature window;
- transmission oil within temperature limits;
- N63 oil/coolant temperatures ready;
- no HV, EGS, EME or DSC faults.

Suggested preferred SOC before repeated full-power use:
- ~50–60%.

M2 should automatically derate electric assist as SOC or temperature limits are approached rather than violate hardware limits.

### LAUNCH MODE

Launch is a temporary propulsion state, not a normal drive mode.

Preconditions:
- N63 at operating temperature;
- HV battery SOC above calibrated minimum;
- HV battery and inverter temperatures valid;
- transmission temperature valid;
- K0 fully synchronized/closed;
- xDrive / DSC / wheel-speed plausibility valid.

Launch control concept:
1. establish required ICE rpm/load;
2. prepare turbo boost within safe limits;
3. preload drivetrain according to validated EGS/DSC logic;
4. use e-machine torque to fill transient response;
5. cap total gearbox input torque by gear;
6. ramp torque rather than simply add maximum N63 + maximum e-motor torque;
7. reduce e-assist if traction, K0, transmission or thermal limits are reached.

The goal is the quickest repeatable launch the drivetrain can survive, not the largest instantaneous torque number.

## Torque management principle

The transmission should never receive the arithmetic sum of maximum engine and motor torque if that exceeds a validated limit.

The Hybrid Supervisor should use a torque envelope:

```text
allowed_total_torque =
min(
  gearbox_limit,
  K0_limit,
  transfer_case_limit,
  axle_limit,
  traction_limit,
  thermal_limit
)
```

Then split that torque between:
- N63;
- e-machine.

At low speed / low gear:
- cap total torque aggressively.

At higher rpm / higher gears:
- allow greater combined power while keeping torque inside the validated envelope.

This is how the project can pursue ~750–800 hp combined without requiring ~1000+ Nm at the transmission input at low rpm.

## Independent EV override

A dedicated iDrive propulsion control should also be considered independently of the chassis mode:

- **EV MAX** – request EV-only until a protection limit requires ICE.
- **AUTO HYBRID** – mode-dependent strategy described above.
- **BATTERY HOLD** – maintain a chosen SOC for a later low-emission / urban segment.

This allows the driver to select SPORT chassis settings while still requesting EV operation in limited situations, or to preserve charge before entering a city.

Final combinations must be constrained so contradictory requests cannot create unsafe or mechanically invalid states.
