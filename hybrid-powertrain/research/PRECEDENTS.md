# Research Precedents

## Open-source GA8P75HZ control
Damien Maguire's `8HP-TCU` is an open-source controller project for the ZF 8HP family and explicitly targets the BMW ZF GA8P75HZ for EV conversions.

https://github.com/damienmaguire/8HP-TCU

## OpenInverter GA8P75HZ work
Community work exists around GA8P75HZ gearbox hacking and a 330e hybrid swap.

https://openinverter.org/forum/viewtopic.php?t=750
https://openinverter.org/forum/viewtopic.php?t=1919

Reported challenges relevant here include:
- ICE torque-model exchange with the VCU/TCU;
- integrated e-machine control;
- K0 transitions;
- auxiliary transmission oil-pump control;
- CAN integration between inverter, gearbox and VCU.

## F04 ActiveHybrid 7
Use primarily as an N63 hybrid-controls reference:
- MSD85_HY;
- eBoost/regen semantics;
- DME/EME/EGS responsibility split;
- torque and start/stop messages.

The original F04 drivetrain is not the final target because its e-machine is permanently coupled to the N63.

## F10 ActiveHybrid 5 / 8P70H
Useful as an earlier P2 hybrid mechanical/hydraulic reference for:
- K0;
- integrated e-machine;
- auxiliary oil pump;
- compact hybrid front module.

## 8P75 family
Currently preferred because it retains P2/K0 while offering higher e-machine output and stronger applications.

Priority donor:
- G05 X5 45e family, due to documented reinforced K0/geartrain changes for the six-cylinder PHEV application.

## Evidence standard
Tag interchangeability claims as:
- CONFIRMED
- STRONG INDICATION
- HYPOTHESIS
- REJECTED

Do not upgrade a hypothesis to confirmed based only on catalog similarity.
