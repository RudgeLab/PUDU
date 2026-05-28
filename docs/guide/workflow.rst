End-to-end workflow
===================

PUDU automates three sequential lab stages.  Each stage reads the output of
the previous one, creating a traceable chain from DNA design to plated
colonies.

.. code-block:: text

    SBOL JSON design
         │
         ▼
    ┌─────────────┐     opentrons_simulate
    │  Assembly   │ ──────────────────────▶  transformation_input.json
    └─────────────┘
         │
         ▼
    ┌──────────────────┐  opentrons_simulate
    │  Transformation  │ ──────────────────▶  plating_input.json
    └──────────────────┘
         │
         ▼
    ┌─────────┐  opentrons_simulate
    │ Plating │ ──────────────────────────▶  plating_layout.json / .xlsx
    └─────────┘

Stage 1 — Assembly
------------------

Golden Gate DNA assembly in a thermocycler.  Parts and backbone are loaded
onto a temperature module (4 °C), combined in a thermocycler plate, and
cycled 75 times between 42 °C (digest) and 16 °C (ligate).

Generate and simulate the protocol::

    python -m pudu.generate_protocol \
        scripts/manual/manual_assembly_input.json \
        -o assembly_protocol.py \
        --protocol-type assembly

    opentrons_simulate assembly_protocol.py

This writes ``transformation_input.json`` mapping each assembled product URI
to its thermocycler well location.

Stage 2 — Transformation
-------------------------

Heat-shock transformation of assembled plasmids into competent bacteria.
DNA is transferred from the assembly plate (or temp module) into the
thermocycler plate alongside competent cells, heat-shocked, and incubated
with recovery media.

Generate and simulate::

    python -m pudu.generate_protocol \
        scripts/manual/manual_transformation_input.json \
        -o transformation_protocol.py \
        --protocol-type transformation \
        --plasmid-locations transformation_input.json

    opentrons_simulate transformation_protocol.py

This writes ``plating_input.json`` mapping each thermocycler well to its
transformed construct.

Stage 3 — Plating
------------------

Serial dilution and spot-plating onto agar.  Bacteria from the thermocycler
plate are diluted (up to 2×) and spotted onto agar plates with replicates.

Generate and simulate::

    python -m pudu.generate_protocol \
        plating_input.json \
        -o plating_protocol.py \
        --protocol-type plating

    opentrons_simulate plating_protocol.py

This writes ``plating_layout.json`` and ``plating_layout.xlsx`` — a coloured
grid showing which agar well receives which construct at which dilution ratio.

Manual bench protocols
-----------------------

If you don't have access to an OT-2, PUDU can generate human-readable
Markdown guides for each stage::

    python scripts/manual/generate_manual_assembly_protocol.py \
        --input  scripts/manual/manual_assembly_input.json \
        --output scripts/manual/manual_assembly_protocol.md

    python scripts/manual/generate_manual_transformation_protocol.py \
        --input  scripts/manual/manual_transformation_input.json \
        --output scripts/manual/manual_transformation_protocol.md

    python scripts/manual/generate_manual_plating_protocol.py \
        --input  scripts/manual/manual_plating_input.json \
        --output scripts/manual/manual_plating_protocol.md

Input file formats
------------------

See :mod:`pudu.generate_protocol` for the full JSON schemas for each input
type and the advanced parameters file.

Calibration
-----------

Before running fluorescence or OD600 measurements, calibrate your plate
reader using the iGEM 2022 protocol.  Two calibration classes are provided:

* :class:`pudu.calibration.GFPODCalibration` — fluorescein + microspheres (GFP + OD600)
* :class:`pudu.calibration.RGBODCalibration` — fluorescein + sulforhodamine + cascade blue + microspheres

Example script: ``scripts/automated_ot2/run_iGEM_rgb_od.py``
