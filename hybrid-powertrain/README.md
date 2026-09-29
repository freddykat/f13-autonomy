# F13 N63 PHEV / Hybrid Powertrain Research

Experimental engineering subproject for converting a BMW F13 650i xDrive with N63B44A into a plug-in hybrid while preserving the OEM BMW character and as much F-series integration as possible.

## Why this project exists

We are **petrolheads first**. We like the N63, the sound and character of a V8, and the idea of keeping a BMW 650i feeling like a real 650i. This project is not an attempt to remove the combustion engine from the car or turn it into a generic EV.

The objective is to get the **best of both worlds**:

- **Daily commute:** run electrically whenever practical, with low energy cost, quiet operation and regenerative braking.
- **Long trips:** retain the range, refuelling speed and flexibility of the N63.
- **Performance driving:** keep the V8 available and combine ICE + electric torque when desired.
- **Efficiency:** use the electric system to reduce unnecessary fuel use in traffic, short trips and low-load driving rather than carrying a large V8 through those conditions all the time.

A concrete benchmark for the project is that the normal daily commute should become **cheaper to run on energy than a small Citroën DS3 1.2 VTi**, while the same car can still deliver the performance, sound and character expected from a V8 650i when requested.

So the goal is not maximum horsepower at all times. The goal is a genuinely dual-personality car:

```text
weekday commute -> EV
traffic / city -> EV
normal mixed use -> automatic hybrid
long-distance cruise -> efficient hybrid / ICE as appropriate
Sport / special days -> N63 + electric assist
```

The engineering challenge is to achieve that without sacrificing OEM drivability, xDrive integration, chassis behavior or serviceability.

## Target

- Keep the N63B44A V8.
- Add true EV-only driving using a disconnect clutch (K0).
- Target about 100 km real EV commute range.
- Target about 40-45 kWh gross HV battery capacity, packaged entirely in the rear shell/sub-shell area.
- Keep xDrive and the original vehicle dynamics systems where practical.
- Use a BMW/ZF hybrid transmission architecture rather than a separate rear e-axle.
- Keep a 12 V lithium auxiliary battery in an OEM-like role.
- Long-term performance target: a limited high-output combined mode near 750-800 hp, with gearbox input torque managed rather than simply summing ICE and e-motor peaks.

This is a research project, not a finished conversion recipe. Safety-critical HV, transmission, braking, stability-control and structural work must be validated before road use.

## Current leading architecture

```text
N63B44A
   |
N63-compatible 8HP75 front/bellhousing geometry
   |
torsional damper
   |
K0 disconnect clutch
   |
BMW/ZF PHEV e-machine
   |
GA8P75HZ / 8P75XPH core
   |
AWD output
   |
F13 ATC35L if mechanically compatible
   |
F13 xDrive driveline
```

Electronic concept:

```text
F04 MSD85_HY strategy / N63 torque model
             |
      Hybrid supervisor
       /      |       \
     EGS     EME      BMS
      |       |        |
   8P75    e-machine  HV pack
```

The F04 ActiveHybrid 7 is useful because BMW already implemented hybrid torque coordination around an N63/MSD85-family DME. The later 8P70H/8P75H families are useful because they add a true K0 disconnect clutch and EV-only operation.

## Why not start with the 8HP100XPH?

The current BMW/ZF 8HP100 PHEV architecture is attractive for power capacity and a larger e-machine, but it creates significantly more G-series integration work. The 8P75 route appears more compatible with an F-series/N63 project and already exists in AWD/PHEV variants.

8HP100 remains a fallback/performance path if 8P75 torque, K0 thermal capacity or packaging becomes the limiting factor.

## Donor candidates under investigation

### N63 mechanical interface
- BMW GA8HP70X N63, original F13 transmission.
- BMW GA8HP75X N63 from later N63 applications.

### PHEV transmission core
Preferred:
- BMW G05 X5 xDrive45e GA8P75HZ / 8P75-family PHEV hardware because BMW reinforced the K0 and parts of the gearset for the six-cylinder PHEV application.

Also useful:
- F15 X5 xDrive40e GA8P75HZ.
- 740e/745e xDrive 8P75XPH family.
- F10 ActiveHybrid 5 GA8P70H as an earlier K0/e-machine reference.

### N63 hybrid logic
- F04 ActiveHybrid 7 MSD85_HY and related documentation/hardware as a reference for N63 hybrid torque coordination, eBoost, regen and start/stop logic.

## Battery target

- 40-45 kWh gross.
- Roughly 315-330 V nominal, subject to chosen EME/inverter voltage window.
- High-energy automotive cells.
- All traction cells in a custom rear shell/sub-shell enclosure.
- No central cabin battery.
- Auxiliary systems behind the rear quarter trims rather than cells.

## Open mechanical questions

1. Can N63 GA8HP75X front/bellhousing geometry be combined with a GA8P75HZ/8P75XPH hybrid case/core without machining the main case?
2. What is the exact crank flange to K0 depth for the N63 compared with B58/B48 PHEV donors?
3. Are the K0 input spline, pilot, bearing and damper interfaces sufficiently modular to build an N63-specific front stack?
4. Can the F13 ATC35L mate to the AWD output of the chosen 8P75XPH variant?
5. What combined input-torque envelope is realistic after K0 and clutch-pack thermal analysis?

## Existing public work worth studying

- Damien Maguire's 8HP-TCU, intended for the BMW ZF GA8P75HZ and EV conversions:
  https://github.com/damienmaguire/8HP-TCU
- OpenInverter GA8P75HZ gearbox hacking:
  https://openinverter.org/forum/viewtopic.php?t=750
- OpenInverter 330e hybrid swap:
  https://openinverter.org/forum/viewtopic.php?t=1919

## Collaboration wanted

We are actively looking for contributors with practical experience in:

- ZF 8HP/8P70/8P75 teardown and parts interchangeability;
- BMW N63 / MSD85 / MSD85_HY calibration;
- BMW F-series PT-CAN / PT-CAN2 / ICM / DSC / VTG;
- BMW PHEV EME / SME / EGS reverse engineering;
- OpenInverter, ZombieVerter, HTG GCU or custom VCU work;
- high-voltage battery design and functional safety;
- CAD measurement of transmission housings and driveline interfaces;
- F13 rear-body scanning, battery enclosure FEA and thermal design.

If you can provide real measurements, gearbox tags, teardown photos, CAN logs, DBC work or test hardware, please open an issue.

## Development principles

- Measure first, buy second.
- Preserve OEM fail-safe behavior where possible.
- Do not depend on AI-generated assumptions for safety-critical decisions.
- Validate first on a bench, then HIL, then controlled vehicle tests.
- Keep mechanical, electrical and software interfaces documented and reproducible.
