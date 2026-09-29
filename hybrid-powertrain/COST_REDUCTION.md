# Cost-Minimisation Strategy

The project should minimise **total engineering cost**, not simply buy the cheapest components.

The preferred order is:

1. reuse OEM BMW/ZF hardware;
2. use damaged/scrap donor parts for measurement before buying good parts;
3. reuse open-source control/BMS projects where safe and appropriate;
4. use student/research collaborations for bounded engineering work packages;
5. pay specialists only for tasks that require proprietary tooling, precision machining, safety validation or final assembly;
6. buy new components only where used parts create unacceptable safety or reliability risk.

## Transmission strategy

### Research core first

Before buying a good GA8P75HZ/8P75XPH:
- source a damaged/noisy core;
- scan and measure bellhousing, K0, e-machine housing and AWD output;
- compare with F13 GA8HP70X and N63 GA8HP75X geometry.

Current market evidence shows:
- used 330e/530e GA8P75HZ boxes can appear around €1,000–€2,000;
- faulty X5 45e GA8P75HZ cores can appear far below that;
- a good X5/F15 hybrid gearbox can cost €3,000+.

Target research-core budget:
**€250–€750**.

Only buy the final good donor after the interface study proves which exact variant we need.

### Professional transmission work

Use a ZF specialist for:
- final inspection;
- clutch/K0 condition;
- bearing/endplay verification;
- final assembly;
- any required machining review.

Do not pay workshop rates for early exploratory teardown if a scrap core can be used.

## EME / inverter strategy

Preferred:
- buy used OEM BMW PHEV EME;
- reset/virginize/bench-check through a specialist;
- avoid new BMW electronics.

Current Dutch specialists already support EME reset for 330e/530e/740e/745e/X5 40e/45e families.

Open questions:
- which EME generation best matches the chosen GA8P75HZ;
- minimum immobilizer/ISN dependencies;
- minimum bench network;
- whether one reset unit can be operated under a custom hybrid supervisor.

## Hybrid supervisor / VCU

Do not start from a blank PCB/software stack.

Reference/open-source foundations:
- ZombieVerter / OpenInverter STM32 VCU;
- Damien Maguire STM32 VCU;
- 8HP-TCU hardware;
- BMW-specific CAN work from the existing F13 autonomy project.

Strategy:
- use an open-source VCU as an engineering baseline;
- keep BMW-specific state translation in a separate layer;
- preserve DME/EGS/EME inner control loops wherever possible;
- only develop custom safety hardware where OEM/open-source hardware cannot satisfy requirements.

## BMS

Candidate R&D platform:
**foxBMS 2 (Fraunhofer IISB)**.

Reasons:
- open hardware/software;
- CAN architecture;
- scalable to large HV packs;
- cell voltage/temperature monitoring;
- precharge/contactors;
- current sensing;
- fault-state handling;
- documented and actively maintained.

Important:
foxBMS is an R&D platform, not a drop-in road-certified BMS. Application-specific engineering and validation remain required.

Cost strategy:
- use foxBMS for prototype / HIL development if appropriate;
- compare final cost against an automotive integrator's certified BMS;
- do not reinvent cell monitoring, precharge and diagnostic logic from scratch.

## Battery pack engineering

The most expensive mistake would be committing to cells before the real package volume is known.

Order:
1. strip/scan rear body;
2. build parametric CAD volume;
3. shortlist cells;
4. simulate S/P topologies;
5. thermal model;
6. structural pack concept;
7. supplier review;
8. buy cells.

Possible partner categories:
- cell supplier;
- pack integrator;
- academic structural/thermal project;
- BMS specialist.

Do not force one company to supply every layer if that increases cost.

## Academic / student collaboration

Potential 20-week / graduation work packages:
- F13 rear-body 3D scan;
- battery enclosure CAD/FEA;
- cooling-plate CFD;
- hybrid energy-management strategy;
- N63/8P75 mechanical interface;
- CAN signal identification;
- driveline load analysis;
- vehicle energy/TCO model.

Relevant Dutch routes being approached:
- HAN Engineering & Automotive / PartnerDesk;
- HAN Mobility Innovation Center;
- ACE Mobility;
- InMotion / TU Eindhoven;
- Regterschot Engineering / student collaboration ecosystem.

This is intended to reduce commercial engineering hours while providing bounded, useful academic work.

## Donor strategy

Avoid buying a complete healthy X5 45e unless the whole donor is clearly cheaper than the sum of required parts.

Preferred staged procurement:

### Phase A – research
- faulty GA8P75HZ core;
- scrap/used ATC components;
- used EME;
- connectors/harness sections;
- F04 MSD85_HY ECU;
- donor HV connectors / junction hardware where safe.

### Phase B – validated architecture
- final good transmission;
- final EME;
- final cell batch;
- final BMS;
- contactors / pyro / IMD / HVIL hardware;
- OBC/DC-DC;
- cooling hardware.

### Phase C – certification/final build
- replace any questionable used HV safety parts with new traceable items;
- final enclosure;
- certified cabling/connectors;
- final fasteners and protection.

## Parts that can sensibly be used

Good candidates for used/reconditioned parts:
- transmission case and geartrain;
- e-machine;
- EME after specialist test/reset;
- transfer case;
- OBC/DC-DC if tested;
- coolant pumps;
- brackets;
- connectors/pigtails;
- donor ECU/modules;
- non-pyrotechnic mechanical hardware.

## Parts that should generally be new / traceable

Prefer new or fully traceable:
- HV contactors;
- main fuse / pyrofuse;
- HV cable if condition is uncertain;
- service disconnect;
- critical seals;
- battery cells for the final pack;
- pack fasteners in structural joints;
- insulation/barriers;
- pressure relief / vent components;
- coolant hoses in inaccessible pack areas.

## Cost gates

No major purchase should happen unless one of these is true:

- it closes a known research question;
- compatibility is already measured;
- it is reusable in the final vehicle;
- resale value is high if the hypothesis fails.

Every procurement item should be tagged:
- RESEARCH ONLY
- PROTOTYPE REUSABLE
- FINAL BUILD
- SAFETY CRITICAL

## Current high-value low-cost opportunities

1. Faulty X5 45e GA8P75HZ core for teardown.
2. Used EME + professional reset rather than new module.
3. foxBMS 2 as BMS R&D baseline.
4. ZombieVerter/OpenInverter as VCU reference.
5. HAN/MIC student projects for CAD/FEA/thermal/controls.
6. ZF specialists approached for damaged cores and final inspection rather than full bespoke engineering.
7. Battery suppliers approached before committing to cells.

## Target philosophy

Spend money on:
- measurements;
- safety;
- final machining;
- final validation.

Avoid spending money on:
- duplicate donor parts;
- early good-condition transmissions;
- proprietary black-box controllers where open alternatives exist;
- new BMW electronics when tested used modules can be reset;
- battery cells before package-space validation.
