# Golden Gate Manual Assembly Protocol

## Overview
Golden Gate assembly is a one-pot DNA cloning method that uses a Type IIS restriction enzyme, such as BsaI, together with DNA ligase to assemble multiple DNA fragments in a predefined order.
Because Type IIS enzymes cut outside their recognition sites, they generate custom overhangs that direct fragment assembly and allow the recognition sites to be removed from the final construct.
In this protocol, plasmids containing DNA parts and a destination backbone are combined with the restriction enzyme and ligase in a single tube, then cycled in a thermocycler between digestion and ligation temperatures. Repetition of these cycles enriches for the correctly assembled composite plasmid, after which the enzymes are heat-inactivated and the reaction is held at 4 °C until collection.

## Inputs
- Number of target products: 2
- `composite_1` (https://SBOL2Build.org/composite_1/1)
- `composite_2` (https://SBOL2Build.org/composite_2/1)

## Reaction summary
| Product | Backbone | Parts | Restriction Enzyme | # DNA Components | DNA each (µL) | Enzyme (µL) | Ligase (µL) | Buffer (µL) | Water (µL) | Total (µL) |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| composite_1 | pSB1C3 | J23101, B0034, GFP, B0015 | BsaI | 5 | 2 | 2 | 4 | 2 | 2 | 20 |
| composite_2 | pSB1C3 | J23106, B0034, RFP, B0015 | BsaI | 5 | 2 | 2 | 4 | 2 | 2 | 20 |

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
- Use a cycling profile that holds 42°C for 2 minutes and 16°C for 5 minutes; repeat this profile 75 times.
- Denature/inactivate proteins by holding 60°C for 10 minutes followed by 80°C for 10 minutes.
- Hold at 4°C until samples are collected.

## Notes
- If the assembly was designed correctly, the final product should lack the Type IIS recognition sites used during assembly.
- This generated document is a manual instruction sheet and not an automated OT-2 protocol.
- Assumes all DNA parts are available at suitable concentrations and added at equal per-part volume.
- Store the assembly product at 4 °C for better stability until used for downstream applications.
- Validate assembled plasmids by restriction digest and gel electrophoresis, Sanger sequencing, or whole-plasmid sequencing.
