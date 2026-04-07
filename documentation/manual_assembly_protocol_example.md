# Golden Gate Manual Assembly Protocol

## Overview
This document provides human-readable Golden Gate assembly instructions from SBOL-style JSON input.
It is an instruction sheet for manual execution and is not an Opentrons OT-2 script.

## Inputs
- Number of target products: 2
- `composite_1` (https://SBOL2Build.org/composite_1/1)
- `composite_2` (https://SBOL2Build.org/composite_2/1)

## Default reagent assumptions
- Total reaction volume: 20 µL
- Per DNA component volume (backbone or part): 2 µL
- Restriction enzyme volume: 2 µL
- T4 DNA ligase volume: 4 µL
- T4 DNA ligase buffer volume: 2 µL
- Water volume is calculated per reaction from the configured defaults.

## Reaction summary
| Product | Backbone | Parts | Restriction Enzyme | # DNA Components | Water (µL) | Total (µL) |
| --- | --- | --- | --- | ---: | ---: | ---: |
| composite_1 | pSB1C3 | J23101, B0034, GFP, B0015 | BsaI | 5 | 2 | 20 |
| composite_2 | pSB1C3 | J23106, B0034, RFP, B0015 | BsaI | 5 | 2 | 20 |

## Per-reaction instructions

### Product: composite_1
URI: https://SBOL2Build.org/composite_1/1

1. Label one tube as `composite_1`.
2. Add 2 µL nuclease-free water.
3. Add 2 µL 10X T4 DNA Ligase Buffer.
4. Add 4 µL T4 DNA Ligase.
5. Add 2 µL BsaI (URI: https://SBOL2Build.org/BsaI/1).
6. Add 2 µL backbone `pSB1C3` (URI: https://sbolcanvas.org/pSB1C3/1).
7. Add 2 µL part `J23101` (URI: https://sbolcanvas.org/J23101/1).
8. Add 2 µL part `B0034` (URI: https://sbolcanvas.org/B0034/1).
9. Add 2 µL part `GFP` (URI: https://sbolcanvas.org/GFP/1).
10. Add 2 µL part `B0015` (URI: https://sbolcanvas.org/B0015/1).
11. Mix gently by pipetting. Do not vortex unless explicitly intended.
12. Briefly spin down if appropriate.

### Product: composite_2
URI: https://SBOL2Build.org/composite_2/1

1. Label one tube as `composite_2`.
2. Add 2 µL nuclease-free water.
3. Add 2 µL 10X T4 DNA Ligase Buffer.
4. Add 4 µL T4 DNA Ligase.
5. Add 2 µL BsaI (URI: https://SBOL2Build.org/BsaI/1).
6. Add 2 µL backbone `pSB1C3` (URI: https://sbolcanvas.org/pSB1C3/1).
7. Add 2 µL part `J23106` (URI: https://sbolcanvas.org/J23106/1).
8. Add 2 µL part `B0034` (URI: https://sbolcanvas.org/B0034/1).
9. Add 2 µL part `RFP` (URI: https://sbolcanvas.org/RFP/1).
10. Add 2 µL part `B0015` (URI: https://sbolcanvas.org/B0015/1).
11. Mix gently by pipetting. Do not vortex unless explicitly intended.
12. Briefly spin down if appropriate.

## Thermocycling
- Program a Golden Gate cycling profile suitable for your Type IIS enzyme and ligase system.
- Typical high-level pattern:
  - 25-35 cycles alternating between digestion and ligation temperatures.
  - Follow with a final digestion/inactivation step as appropriate for enzyme cleanup.
  - Hold at 4°C until samples are recovered.
- Use your lab's validated Golden Gate settings for the selected restriction enzyme.

## Notes
- If the assembly was designed correctly, the final product should lack the Type IIS recognition sites used during assembly.
- This generated document is a manual instruction sheet and not an automated OT-2 protocol.
- Assumes all DNA parts are available at suitable concentrations and added at equal per-part volume.
