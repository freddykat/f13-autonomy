# Battery Partner RFI – F13 N63 PHEV

## Project objective

We are seeking a battery-cell supplier and/or European HV pack engineering partner for a one-off engineering prototype with potential low-volume follow-on.

Vehicle: BMW F13 650i xDrive / N63B44A.

The conversion retains the V8 and adds a BMW/ZF P2 hybrid transmission with K0 disconnect clutch. The battery is intended primarily to make the daily commute electric and inexpensive, while retaining ICE range and hybrid performance when required.

## Preliminary electrical targets

- Gross energy: **40–45 kWh**
- Nominal voltage: **approximately 315–330 V**, final value to be matched to the selected BMW/ZF EME/inverter operating window
- Daily-use continuous discharge target: **80–100 kW**
- Short-duration discharge design target: **120–150 kW**
- Regenerative charge capability: to be matched to the PHEV e-machine and cell limits
- AC charging target: **11 kW**
- DC charging: optional/future provision, not mandatory for V1

These are engineering targets, not frozen specifications.

## Packaging constraints

All traction cells must fit inside a custom enclosure in the **rear shell/sub-shell / lower trunk structure**.

No traction cells are planned behind the rear quarter trim panels.

Those side volumes are reserved for auxiliary systems such as:
- OBC / charge electronics;
- DC/DC;
- 12 V lithium auxiliary battery;
- coolant pumps / valves / reservoir;
- HV junction/service hardware;
- gateway / control electronics.

The final pack geometry will be defined from a 3D scan of the stripped rear body.

## Preferred cell technology

Priority is high usable energy density with credible automotive safety and cycle life.

We are interested in:
- high-energy automotive pouch cells;
- advanced NMC/NCA pouch cells;
- silicon-rich / silicon-anode cells where automotive suitability is demonstrated;
- Amprius SiCore / SA08-class cells or technically comparable alternatives.

We are not committed to a specific supplier or chemistry.

Cell selection will be based on:
- Wh/kg;
- Wh/L;
- continuous/pulse power;
- cycle life at a conservative SOC window;
- low-temperature performance;
- thermal stability;
- swelling/compression requirements;
- traceability;
- availability;
- safety documentation;
- realistic prototype MOQ.

## Mechanical / thermal requirements

Preferred pack architecture:
- custom structural aluminium/composite enclosure after body scan;
- liquid cooling plate(s);
- externally directed pressure/vent strategy;
- replaceable/serviceable module strategy where practical;
- underbody impact protection;
- mounting to defined structural hard points rather than thin luggage-floor sheet metal.

We welcome supplier guidance on whether pouch cells should be grouped into serviceable modules or integrated more directly into a structural pack.

## BMS / HV safety requirements

Required functions include:
- cell-voltage monitoring;
- cell-temperature monitoring;
- SOC / SOH estimation;
- CAN interface;
- contactor control;
- precharge;
- HVIL;
- current measurement;
- isolation monitoring;
- service disconnect;
- main fuse / pyrofuse strategy;
- charge/discharge power limits;
- fault logging and safe-state strategy.

We are open to a supplier BMS, an automotive third-party BMS, or integration with a BMW-style SME-equivalent architecture.

## Validation / approval context

The vehicle is intended for approval in the Netherlands.

Therefore we value:
- traceable cell provenance;
- cell test data;
- transport documentation where applicable;
- documented electrical/thermal limits;
- pack FMEA / hazard analysis support;
- UN38.3 guidance where applicable;
- insulation/isolation validation;
- thermal propagation strategy;
- structural analysis and documented fastener/load paths.

## Development route

Preferred sequence:

1. rear-body 3D scan and usable-volume definition;
2. cell shortlist;
3. preliminary pack layout;
4. electrical/thermal model;
5. structural concept / FEA;
6. prototype module if useful;
7. full pack prototype;
8. bench/HIL electrical validation;
9. vehicle integration;
10. controlled validation before road approval.

## What we are asking suppliers for

Please advise:

1. Whether a **single prototype / very-low-volume** project is within your scope.
2. Recommended cell for the energy/power targets.
3. Whether cells, modules or a complete custom pack can be supplied.
4. Prototype MOQ.
5. Required compression/support for the proposed pouch cell.
6. Cooling approach and maximum recommended cell temperature.
7. BMS options.
8. Documentation available for approval/validation.
9. Approximate engineering route and commercial model.
10. What CAD/package-space information you require from us.

## Public project

Repository:
https://github.com/freddykat/f13-autonomy

Hybrid powertrain work:
https://github.com/freddykat/f13-autonomy/tree/feature/n63-phev-research-v2/hybrid-powertrain

Contributions from battery engineers are welcome. Supplier-sensitive commercial information does not need to be public.
