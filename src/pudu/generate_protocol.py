"""
Protocol Generator for PUDU
============================

Generates standalone Opentrons OT-2 protocol ``.py`` files from JSON inputs.
The generated files can be uploaded directly to the Opentrons App or simulated
on a laptop to verify the deck layout before running on the robot.

This module supports two usage modes:

* **Command-line** (recommended) — run as ``python -m pudu.generate_protocol``
* **Python API** — call :func:`generate_protocol` programmatically from a script
  or notebook (see the API section below)


Overview of the three protocol stages
--------------------------------------

A typical PUDU synthetic-biology workflow has three sequential stages that each
produce a robot protocol file:

1. **Assembly** — Golden Gate DNA assembly in a thermocycler.  Outputs
   ``transformation_input.json`` (well locations of assembled products).
2. **Transformation** — Heat-shock transformation of assembled DNA into competent
   bacteria.  Outputs ``plating_input.json`` (thermocycler well locations of
   transformed cultures).
3. **Plating** — Serial dilution and spot-plating onto agar plates.


Input file formats
-------------------

**Assembly input** (SBOL-style list of constructs)::

    [
        {
            "Product":            "https://SBOL2Build.org/composite_1/1",
            "Backbone":           "https://sbolcanvas.org/pSB1C3/1",
            "PartsList": [
                "https://sbolcanvas.org/J23101/1",
                "https://sbolcanvas.org/B0034/1",
                "https://sbolcanvas.org/GFP/1",
                "https://sbolcanvas.org/B0015/1"
            ],
            "Restriction Enzyme": "https://SBOL2Build.org/BsaI/1"
        }
    ]

**Transformation input** (list of strain/chassis/plasmid mappings)::

    [
        {
            "Strain":   "https://SBOL2Build.org/strain_GFP/1",
            "Chassis":  "https://sbolcanvas.org/DH5alpha/1",
            "Plasmids": ["https://SBOL2Build.org/composite_1/1"]
        }
    ]

**Plating input** (bacterium locations from transformation output)::

    {
        "bacterium_locations": {
            "A1": "https://SBOL2Build.org/composite_1/1",
            "B1": "https://SBOL2Build.org/composite_2/1"
        }
    }

**Advanced parameters** (optional ``json_params`` file — any protocol type)::

    {
        "replicates": 2,
        "volume_part": 3,
        "initial_tip": "B1",
        "protocol_name": "GFP_RFP_assembly"
    }

**Metadata** (optional ``--metadata`` file — any protocol type)::

    {
        "protocolName": "GFP RFP Assembly",
        "author": "Oscar Rodriguez",
        "description": "Loop assembly of GFP and RFP constructs",
        "apiLevel": "2.21"
    }

All four keys are optional; omitted keys fall back to the defaults in
``DEFAULT_METADATA``.


Full automated OT-2 workflow (terminal commands)
-------------------------------------------------

Run all commands from the repository root (the directory containing ``src/``).

**Step 1 — Generate the assembly protocol**::

    python -m pudu.generate_protocol \\
        assembly_input.json \\
        -o assembly_protocol.py \\
        --protocol-type assembly

Pass a parameters file as the **second positional argument** to override
defaults (volumes, replicates, starting tip, etc.)::

    python -m pudu.generate_protocol \\
        assembly_input.json \\
        params.json \\
        -o assembly_protocol.py \\
        --protocol-type assembly

Override the Opentrons metadata (protocol name shown in the app, author,
API level) with ``--metadata``::

    python -m pudu.generate_protocol \\
        assembly_input.json \\
        -o assembly_protocol.py \\
        --protocol-type assembly \\
        --metadata metadata.json

Force a specific assembly subtype with ``--assembly-type`` (useful when
auto-detection is ambiguous)::

    python -m pudu.generate_protocol \\
        assembly_input.json \\
        -o domestication_protocol.py \\
        --protocol-type assembly \\
        --assembly-type Domestication

**Step 1a — Simulate the assembly protocol to produce plasmid locations**::

    opentrons_simulate assembly_protocol.py

This writes ``transformation_input.json`` in the current directory.

**Step 2 — Generate the transformation protocol**

Without assembly output (plasmids loaded manually onto the temperature module)::

    python -m pudu.generate_protocol \\
        transformation_spec.json \\
        -o transformation_protocol.py \\
        --protocol-type transformation

With assembly output (plasmids sourced from the 96-well PCR plate at the
exact well positions recorded by the assembly simulation)::

    python -m pudu.generate_protocol \\
        transformation_spec.json \\
        -o transformation_protocol.py \\
        --protocol-type transformation \\
        --plasmid-locations transformation_input.json

**Step 2a — Simulate to produce bacteria locations**::

    opentrons_simulate transformation_protocol.py

This writes ``plating_input.json`` in the current directory.

**Step 3 — Generate the plating protocol**::

    python -m pudu.generate_protocol \\
        plating_input.json \\
        -o plating_protocol.py \\
        --protocol-type plating

**Step 3a — Simulate to verify the agar plate map**::

    opentrons_simulate plating_protocol.py

This writes ``plating_layout.json`` and ``plating_layout.xlsx`` showing which
well on which agar plate receives which construct at which dilution.


Manual (bench) protocol generation
------------------------------------

PUDU can also produce human-readable **Markdown** protocols for manual bench
work, without any OT-2 involvement.

**Manual assembly protocol**::

    python scripts/manual/generate_manual_assembly_protocol.py \\
        --input  assembly_input.json \\
        --output scripts/manual/manual_assembly_protocol.md

**Manual transformation protocol**::

    python scripts/manual/generate_manual_transformation_protocol.py \\
        --input  transformation_spec.json \\
        --output scripts/manual/manual_transformation_protocol.md

**Manual plating protocol**::

    python scripts/manual/generate_manual_plating_protocol.py \\
        --input  plating_input.json \\
        --output scripts/manual/manual_plating_protocol.md


Python API usage
-----------------

You can call :func:`generate_protocol` directly from a script or Jupyter
notebook and write the result yourself::

    import json
    from pudu.generate_protocol import generate_protocol, detect_protocol_type

    with open("assembly_input.json") as f:
        data = json.load(f)

    protocol_type, assembly_subtype = detect_protocol_type(data)

    code = generate_protocol(
        protocol_data=data,
        protocol_type=protocol_type,
        assembly_subtype=assembly_subtype,
        json_params={"replicates": 2, "volume_part": 3},
    )

    with open("assembly_protocol.py", "w") as f:
        f.write(code)


CLI flag reference
-------------------

Positional arguments (order matters, both must come before any flags):

``input``
    **Required.** Path to the primary protocol data JSON file (assembly list,
    transformation list, or plating dict).

``json_params``
    **Optional.** Path to an advanced parameters JSON file.  Must be the
    *second positional argument* — placed immediately after ``input`` and
    before any ``--flag``.  Keys must match the ``__init__`` parameter names
    of the target protocol class (see the parameter reference block appended
    to every generated ``.py`` file for the full list).

Named flags:

``-o`` / ``--output``
    **Required.** Destination path for the generated ``.py`` protocol file
    (e.g. ``-o assembly_protocol.py``).

``--protocol-type``
    Choices: ``assembly``, ``transformation``, ``plating``.
    When omitted, the type is auto-detected from the input JSON structure
    (see *Auto-detect rules* below).

``--assembly-type``
    Choices: ``SBOL``, ``Manual``, ``Domestication``.
    Only relevant when ``--protocol-type assembly`` is used.  When omitted,
    the subtype is auto-detected from the assembly input keys.  Pass
    explicitly when the input is ambiguous (e.g. a Domestication JSON whose
    keys happen to overlap with SBOL format).

``--plasmid-locations``
    Path to the ``transformation_input.json`` produced by simulating an
    assembly protocol.  When provided, the generated transformation protocol
    reads DNA directly from the assembly output plate at its fixed well
    positions instead of sequentially from the temperature module.  Only
    applicable with ``--protocol-type transformation``.

``--metadata``
    Path to a JSON file with Opentrons protocol metadata.  Valid keys:
    ``protocolName``, ``author``, ``description``, ``apiLevel``.  Any key
    omitted here falls back to the default in ``DEFAULT_METADATA``.  The
    metadata appears in the Opentrons App header and simulation output.


Auto-detect rules
------------------

When ``--protocol-type`` is omitted, :func:`detect_protocol_type` inspects the
JSON keys to guess the type:

* List with ``"Product"`` / ``"Backbone"`` / ``"PartsList"`` / ``"Restriction Enzyme"`` → **SBOL assembly**
* List with ``"receiver"`` key → **Manual/combinatorial assembly**
* List with ``"parts"`` / ``"backbone"`` / ``"restriction_enzyme"`` keys → **Domestication assembly**
* List with ``"Strain"`` / ``"Chassis"`` / ``"Plasmids"`` → **Transformation**
* Dict with ``"bacterium_locations"`` key → **Plating**

Pass ``--protocol-type`` explicitly when the auto-detection is ambiguous.
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

# Default metadata that can be overridden
DEFAULT_METADATA = {
    'protocolName': 'PUDU Protocol',
    'author': 'Researcher',
    'description': 'Automated protocol',
    'apiLevel': '2.21'
}

# Protocol type configurations
PROTOCOL_CONFIGS = {
    'assembly': {
        'data_key': 'assembly_data',  # Unified: all protocols use <type>_data
        'data_param': 'assembly_data',  # Parameter name for class init
        'class_map': {
            'SBOL': 'SBOLLoopAssembly',
            'Manual': 'ManualLoopAssembly',
            'Domestication': 'Domestication'
        },
        'module': 'pudu.assembly',
        'metadata_name': 'PUDU Assembly Protocol'
    },
    'transformation': {
        'data_key': 'transformation_data',
        'data_param': 'transformation_data',  # Parameter name for class init
        'class_name': 'HeatShockTransformation',
        'module': 'pudu.transformation',
        'metadata_name': 'PUDU Transformation Protocol'
    },
    'plating': {
        'data_key': 'plating_data',
        'data_param': 'plating_data',  # Parameter name for class init
        'class_name': 'Plating',
        'module': 'pudu.plating',
        'metadata_name': 'PUDU Plating Protocol'
    }
}

def detect_protocol_type(data) -> tuple[str, Optional[str]]:
    """
    Detect the protocol type and assembly subtype from the data structure.

    Args:
        data: Protocol data (can be dict or list)

    Returns:
        Tuple of (protocol_type, assembly_subtype)
        - protocol_type: 'assembly', 'transformation', or 'plating'
        - assembly_subtype: 'SBOL', 'Manual', 'Domestication', or None
    """
    # Handle bare list formats
    if isinstance(data, list):
        if not data:
            raise ValueError("Empty data provided")

        first_item = data[0]

        # Check for transformation format (Strain/Chassis/Plasmids)
        if 'Strain' in first_item and 'Chassis' in first_item and 'Plasmids' in first_item:
            return 'transformation', None

        # Check for SBOL assembly format
        sbol_keys = {'Product', 'Backbone', 'PartsList', 'Restriction Enzyme'}
        if sbol_keys.issubset(set(first_item.keys())):
            return 'assembly', 'SBOL'

        # Check for Manual format
        if 'receiver' in first_item:
            return 'assembly', 'Manual'

        # Check for Domestication format
        if 'parts' in first_item and 'backbone' in first_item and 'restriction_enzyme' in first_item:
            return 'assembly', 'Domestication'

        # Default to SBOL
        return 'assembly', 'SBOL'

    # Handle new format: wrapped dict
    if isinstance(data, dict):
        # Check for assembly types
        if 'assemblies' in data:
            assemblies = data['assemblies']
            if not assemblies:
                raise ValueError("No assemblies provided")

            first_assembly = assemblies[0]

            # Check for SBOL format
            sbol_keys = {'Product', 'Backbone', 'PartsList', 'Restriction Enzyme'}
            if sbol_keys.issubset(set(first_assembly.keys())):
                return 'assembly', 'SBOL'

            # Check for Manual format
            if 'receiver' in first_assembly:
                return 'assembly', 'Manual'

            # Check for Domestication format
            if 'parts' in first_assembly and 'backbone' in first_assembly and 'restriction_enzyme' in first_assembly:
                return 'assembly', 'Domestication'

            # Default to SBOL
            return 'assembly', 'SBOL'

        # Check for transformation (new SBOL format: list with Strain/Chassis/Plasmids)
        if isinstance(data, list) and data and 'Strain' in data[0] and 'Chassis' in data[0] and 'Plasmids' in data[0]:
            return 'transformation', None

        # Check for plating
        if 'bacterium_locations' in data:
            return 'plating', None

    raise ValueError("Unable to detect protocol type. Please specify --protocol-type explicitly.")

def format_python_value(value, indent_level=0):
    """
    Format a Python value for code generation with proper indentation.

    Args:
        value: The value to format (dict, list, str, int, float, bool, None)
        indent_level: Current indentation level

    Returns:
        Formatted string representation
    """
    indent = '    ' * indent_level

    if value is None:
        return 'None'
    elif isinstance(value, bool):
        return str(value)
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, str):
        # Escape quotes and use repr for safety
        return repr(value)
    elif isinstance(value, list):
        if not value:
            return '[]'
        # Format list with proper indentation
        items = [format_python_value(item, indent_level + 1) for item in value]
        if all(isinstance(item, str) for item in value):
            # Simple list of strings - keep on one line if short
            formatted = ', '.join(items)
            if len(formatted) < 100:
                return f'[{formatted}]'
        # Multi-line list
        formatted_items = ',\n'.join(f'{indent}    {item}' for item in items)
        return f'[\n{formatted_items}\n{indent}]'
    elif isinstance(value, dict):
        if not value:
            return '{}'
        # Format dict with proper indentation
        items = []
        for key, val in value.items():
            formatted_key = repr(key)
            formatted_val = format_python_value(val, indent_level + 1)
            items.append(f'{indent}    {formatted_key}: {formatted_val}')
        return '{\n' + ',\n'.join(items) + f'\n{indent}' + '}'
    else:
        return repr(value)

def _format_annotation(ann) -> str:
    """Format a type annotation as a clean string for display in comments."""
    import inspect
    if ann is inspect.Parameter.empty:
        return ''
    if hasattr(ann, '__name__'):
        return ann.__name__
    # Clean up typing generics: typing.Optional[typing.Dict] -> Optional[Dict]
    return str(ann).replace('typing.', '')


def generate_param_reference(protocol_type: str, class_name: str, module_str: str) -> str:
    """
    Generate a commented parameter reference block for the end of the protocol file.

    Dynamically imports the protocol class and uses inspect to extract the full
    __init__ signature and class docstrings, formatted as comments so users can
    see all available parameters when making last-minute edits before running on
    the robot.

    Args:
        protocol_type: Protocol type string (e.g. 'transformation')
        class_name: Protocol class name (e.g. 'HeatShockTransformation')
        module_str: Fully-qualified module path (e.g. 'pudu.transformation')

    Returns:
        Commented parameter reference block as a string, or a short error comment
        if the class cannot be imported.
    """
    try:
        import importlib
        import inspect

        mod = importlib.import_module(module_str)
        cls = getattr(mod, class_name)

        lines = []
        lines.append("")
        lines.append("")
        lines.append("# " + "=" * 70)
        lines.append(f"# PARAMETER REFERENCE — {class_name}")
        lines.append("#")
        lines.append("# To customize your protocol, add any of the parameters below")
        lines.append(f"# to the {class_name}() constructor call in run() above.")
        lines.append("# Example:  protocol_instance = " + class_name + "(")
        lines.append(f"#               {PROTOCOL_CONFIGS[protocol_type]['data_param']}={PROTOCOL_CONFIGS[protocol_type]['data_key']},")
        lines.append("#               replicates=3,")
        lines.append("#               initial_tip='B1',")
        lines.append("#           )")
        lines.append("# " + "=" * 70)

        # Collect all __init__ params walking the MRO from most-specific to base.
        # Use an ordered dict so subclass params appear first.
        seen_params = set()
        mro_params = []  # list of (class, [(name, default, annotation), ...])

        for klass in cls.__mro__:
            if klass is object:
                continue
            try:
                sig = inspect.signature(klass.__init__)
            except (ValueError, TypeError):
                continue

            klass_params = []
            for name, param in sig.parameters.items():
                if name in ('self', 'args', 'kwargs') or name in seen_params:
                    continue
                seen_params.add(name)
                default = param.default if param.default is not inspect.Parameter.empty else '(required)'
                ann = _format_annotation(param.annotation)
                klass_params.append((name, default, ann))

            if klass_params:
                mro_params.append((klass.__name__, klass_params))

        # Build parameter table — group by class
        if mro_params:
            # Determine column widths across all params
            all_param_entries = [(n, d, a) for _, params in mro_params for n, d, a in params]
            max_name = max(len(n) for n, _, _ in all_param_entries)
            max_type = max((len(a) for _, _, a in all_param_entries if a), default=0)

            for klass_name, params in mro_params:
                lines.append("#")
                lines.append(f"# [{klass_name}]")
                for name, default, ann in params:
                    type_col = ann.ljust(max_type) if ann else ' ' * max_type
                    default_repr = repr(default) if not isinstance(default, str) else default
                    lines.append(f"#   {name:<{max_name}}  {type_col}  = {default_repr}")

        # Append full docstrings for detailed descriptions
        lines.append("#")
        lines.append("# " + "-" * 70)
        lines.append("# Full parameter descriptions:")

        seen_docs: set = set()
        for klass in cls.__mro__:
            if klass is object:
                continue
            doc = inspect.getdoc(klass)
            if not doc or doc in seen_docs:
                continue
            seen_docs.add(doc)
            lines.append("#")
            lines.append(f"# [{klass.__name__}]")
            for doc_line in doc.split('\n'):
                lines.append(f"# {doc_line}" if doc_line.strip() else "#")

        return '\n'.join(lines)

    except Exception as e:
        return f"\n\n# (Parameter reference unavailable: {e})"


def generate_protocol(
    protocol_data: Any,
    json_params: Optional[Dict] = None,
    metadata: Optional[Dict] = None,
    protocol_type: str = 'assembly',
    assembly_subtype: Optional[str] = None,
    plasmid_locations: Optional[Dict] = None
) -> str:
    """
    Generate a complete Opentrons protocol file as a Python source string.

    The returned string is a self-contained ``.py`` file that can be written
    to disk and uploaded to the Opentrons App or passed to
    ``opentrons_simulate``.  It contains:

    * The protocol data embedded as a Python literal.
    * An optional ``json_params`` dict (when provided) embedded as a literal.
    * An optional ``plasmid_locations`` dict (transformation only).
    * A ``metadata`` dict for the Opentrons App.
    * A ``run()`` function that instantiates the correct PUDU class and calls
      its ``.run()`` method.
    * A commented parameter-reference block at the end listing every available
      constructor parameter with its type and default value.

    Args:
        protocol_data: The primary protocol payload.  For assembly and
            transformation protocols this is a list of dicts; for plating it
            is a dict with a ``"bacterium_locations"`` key.
        json_params: Dict of parameter overrides to embed in the generated
            file.  Keys must match the ``__init__`` parameters of the target
            protocol class.  These are passed as ``json_params=json_params``
            in the generated constructor call.
        metadata: Dict of Opentrons metadata keys to merge over the defaults
            in ``DEFAULT_METADATA``.  Valid keys: ``protocolName``,
            ``author``, ``description``, ``apiLevel``.
        protocol_type: One of ``'assembly'``, ``'transformation'``, or
            ``'plating'``.
        assembly_subtype: Required when ``protocol_type='assembly'``.  One of
            ``'SBOL'``, ``'Manual'``, or ``'Domestication'``.
        plasmid_locations: Dict mapping plasmid URIs (strings) to lists of
            well names, as produced by simulating an assembly protocol
            (``transformation_input.json``).  When provided, the generated
            transformation protocol sources DNA from the assembly output plate
            at its fixed positions instead of sequentially from the temp
            module.  Ignored for non-transformation protocol types.

    Returns:
        The complete protocol file as a Python source string.

    Raises:
        ValueError: If ``protocol_type`` is not recognised, or if
            ``assembly_subtype`` is ``None`` when ``protocol_type='assembly'``.
    """
    # Get protocol configuration
    if protocol_type not in PROTOCOL_CONFIGS:
        raise ValueError(f"Unknown protocol type: {protocol_type}")

    config = PROTOCOL_CONFIGS[protocol_type]

    # Merge metadata with defaults
    final_metadata = DEFAULT_METADATA.copy()
    final_metadata['protocolName'] = config['metadata_name']
    if metadata:
        final_metadata.update(metadata)

    # Determine class name and data key
    data_key = config['data_key']

    if protocol_type == 'assembly':
        if assembly_subtype is None:
            raise ValueError("assembly_subtype required for assembly protocols")
        class_name = config['class_map'].get(assembly_subtype, 'SBOLLoopAssembly')

        # Handle both legacy (list) and new (dict) formats
        if isinstance(protocol_data, list):
            actual_data = protocol_data
        elif isinstance(protocol_data, dict) and 'assemblies' in protocol_data:
            actual_data = protocol_data['assemblies']
        else:
            actual_data = protocol_data
    else:
        class_name = config['class_name']
        actual_data = protocol_data

    module = config['module']

    # Build the protocol file
    lines = []

    # Imports
    lines.append(f"from {module} import {class_name}")
    lines.append("from opentrons import protocol_api")
    lines.append("")
    lines.append("")

    # Protocol data
    lines.append(f"# Protocol data")
    lines.append(f"{data_key} = {format_python_value(actual_data)}")
    lines.append("")

    # Plasmid locations (transformation only, from assembly output)
    if plasmid_locations is not None:
        lines.append("# Plasmid well locations from assembly protocol output")
        lines.append(f"plasmid_locations = {format_python_value(plasmid_locations)}")
        lines.append("")

    # Advanced params (if provided)
    if json_params:
        lines.append("# Advanced parameters for protocol customization")
        lines.append(f"json_params = {format_python_value(json_params)}")
        lines.append("")

    # Metadata
    lines.append("# Protocol metadata")
    lines.append(f"metadata = {format_python_value(final_metadata)}")
    lines.append("")
    lines.append("")

    # Run function
    lines.append("def run(protocol: protocol_api.ProtocolContext):")
    lines.append('    """Main protocol execution function"""')
    lines.append("")

    # Protocol initialization - unified data-driven approach
    # All protocols now use <type>_data + advanced_params pattern
    data_param = config['data_param']

    # Build constructor arguments
    constructor_args = [f"{data_param}={data_key}"]
    if plasmid_locations is not None:
        constructor_args.append("plasmid_locations=plasmid_locations")
    if json_params:
        constructor_args.append("json_params=json_params")

    if len(constructor_args) > 1:
        lines.append(f"    protocol_instance = {class_name}(")
        for i, arg in enumerate(constructor_args):
            comma = "," if i < len(constructor_args) - 1 else ""
            lines.append(f"        {arg}{comma}")
        lines.append("    )")
    else:
        lines.append(f"    protocol_instance = {class_name}({constructor_args[0]})")

    lines.append("    protocol_instance.run(protocol)")
    lines.append("")

    # Parameter reference block — appended as comments for last-minute editing
    param_ref = generate_param_reference(protocol_type, class_name, module)
    if param_ref:
        lines.append(param_ref)

    return '\n'.join(lines)

def main():
    """
    Entry point for ``python -m pudu.generate_protocol``.

    Parses command-line arguments, loads the input JSON files, calls
    :func:`generate_protocol`, and writes the result to the output path.
    See the module docstring for full usage, flag descriptions, and
    copy-paste workflow examples.
    """
    parser = argparse.ArgumentParser(
        description='Generate Opentrons protocol files from JSON inputs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate assembly protocol (auto-detect type)
  python -m pudu.generate_protocol data.json params.json -o protocol.py --protocol-type assembly

  # Generate transformation protocol with assembly output
  python -m pudu.generate_protocol synbiosuite.json params.json -o protocol.py --protocol-type transformation --plasmid-locations transformation_input.json

  # Generate transformation protocol without prior assembly (manual input)
  python -m pudu.generate_protocol synbiosuite.json params.json -o protocol.py --protocol-type transformation

  # Generate plating protocol
  python -m pudu.generate_protocol plating.json -o protocol.py --protocol-type plating

  # Auto-detect protocol type
  python -m pudu.generate_protocol data.json -o protocol.py

  # Specify assembly subtype explicitly
  python -m pudu.generate_protocol assemblies.json -o protocol.py --protocol-type assembly --assembly-type Manual
        """
    )

    parser.add_argument(
        'input',
        type=Path,
        help='Path to protocol data JSON file'
    )

    parser.add_argument(
        'json_params',
        type=Path,
        nargs='?',
        default=None,
        help='Path to advanced parameters JSON file (optional)'
    )

    parser.add_argument(
        '-o', '--output',
        type=Path,
        required=True,
        help='Output protocol file path (e.g., protocol.py)'
    )

    parser.add_argument(
        '--protocol-type',
        choices=['assembly', 'transformation', 'plating'],
        default=None,
        help='Protocol type (default: auto-detect)'
    )

    parser.add_argument(
        '--assembly-type',
        choices=['SBOL', 'Manual', 'Domestication'],
        default=None,
        help='Assembly subtype for assembly protocols (default: auto-detect)'
    )

    parser.add_argument(
        '--plasmid-locations',
        type=Path,
        default=None,
        help='Path to plasmid locations JSON file from assembly simulation (transformation protocols only)'
    )

    parser.add_argument(
        '--metadata',
        type=Path,
        default=None,
        help='Path to metadata JSON file (optional)'
    )

    args = parser.parse_args()

    # Load protocol data
    try:
        with open(args.input, 'r') as f:
            protocol_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file: {e}", file=sys.stderr)
        sys.exit(1)

    # Load advanced params if provided
    json_params = None
    if args.json_params:
        try:
            with open(args.json_params, 'r') as f:
                json_params = json.load(f)
        except FileNotFoundError:
            print(f"Error: Advanced params file not found: {args.json_params}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in advanced params file: {e}", file=sys.stderr)
            sys.exit(1)

    # Load plasmid locations if provided
    plasmid_locations = None
    if args.plasmid_locations:
        try:
            with open(args.plasmid_locations, 'r') as f:
                plasmid_locations = json.load(f)
        except FileNotFoundError:
            print(f"Error: Plasmid locations file not found: {args.plasmid_locations}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in plasmid locations file: {e}", file=sys.stderr)
            sys.exit(1)

    # Load metadata if provided
    metadata = None
    if args.metadata:
        try:
            with open(args.metadata, 'r') as f:
                metadata = json.load(f)
        except FileNotFoundError:
            print(f"Error: Metadata file not found: {args.metadata}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in metadata file: {e}", file=sys.stderr)
            sys.exit(1)

    # Detect or use specified assembly type
    if args.protocol_type:
        protocol_type = args.protocol_type
        assembly_subtype = args.assembly_type  # May be None

        # If assembly type and no subtype specified, try to detect
        if protocol_type == 'assembly' and assembly_subtype is None:
            try:
                _, assembly_subtype = detect_protocol_type(protocol_data)
                print(f"Detected assembly subtype: {assembly_subtype}")
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)
    else:
        try:
            protocol_type, assembly_subtype = detect_protocol_type(protocol_data)
            print(f"Detected protocol type: {protocol_type}", end="")
            if assembly_subtype:
                print(f" ({assembly_subtype})")
            else:
                print()
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    # Generate protocol
    try:
        protocol_code = generate_protocol(
            protocol_data=protocol_data,
            json_params=json_params,
            metadata=metadata,
            protocol_type=protocol_type,
            assembly_subtype=assembly_subtype,
            plasmid_locations=plasmid_locations
        )
    except Exception as e:
        print(f"Error generating protocol: {e}", file=sys.stderr)
        sys.exit(1)

    # Write output
    try:
        with open(args.output, 'w') as f:
            f.write(protocol_code)
        print(f"✓ Protocol generated successfully: {args.output}")
        print(f"  Protocol type: {protocol_type}")
        if assembly_subtype:
            print(f"  Assembly subtype: {assembly_subtype}")
        if json_params:
            print(f"  Advanced params: {len(json_params)} parameters")
    except IOError as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
