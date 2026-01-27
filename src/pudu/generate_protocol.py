"""
Protocol Generator for PUDU

Generates standalone Opentrons protocol files from JSON inputs.
The generated protocols can be uploaded directly to the Opentrons App.

Usage:
    # Assembly protocols
    python -m pudu.generate_protocol input.json [params.json] -o output.py --protocol-type assembly

    # Transformation protocols
    python -m pudu.generate_protocol input.json [params.json] -o output.py --protocol-type transformation

    # Plating protocols
    python -m pudu.generate_protocol input.json [params.json] -o output.py --protocol-type plating
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
    # Handle legacy format: bare list of assemblies
    if isinstance(data, list):
        if not data:
            raise ValueError("Empty data provided")

        first_item = data[0]

        # Check for SBOL format
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

        # Check for transformation
        if 'list_of_dna' in data and 'competent_cells' in data:
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
            if len(formatted) < 80:
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

def generate_protocol(
    protocol_data: Any,
    json_params: Optional[Dict] = None,
    metadata: Optional[Dict] = None,
    protocol_type: str = 'assembly',
    assembly_subtype: Optional[str] = None
) -> str:
    """
    Generate a complete Opentrons protocol file as a string.

    Args:
        protocol_data: Protocol data (list for assemblies, or dict for other protocols)
        json_params: Optional advanced parameters dictionary
        metadata: Optional metadata dictionary (merged with defaults)
        protocol_type: Type of protocol ('assembly', 'transformation', 'plating')
        assembly_subtype: Subtype for assembly protocols ('SBOL', 'Manual', 'Domestication')

    Returns:
        Complete protocol file as a string
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

    # Assemblies
    lines.append(f"# Protocol data")
    lines.append(f"{data_key} = {format_python_value(actual_data)}")
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

    if json_params:
        lines.append(f"    protocol_instance = {class_name}(")
        lines.append(f"        {data_param}={data_key},")
        lines.append("        json_params=json_params")
        lines.append("    )")
    else:
        lines.append(f"    protocol_instance = {class_name}({data_param}={data_key})")

    lines.append("    protocol_instance.run(protocol)")
    lines.append("")

    return '\n'.join(lines)

def main():
    """Command-line interface for protocol generation"""
    parser = argparse.ArgumentParser(
        description='Generate Opentrons protocol files from JSON inputs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate assembly protocol (auto-detect type)
  python -m pudu.generate_protocol data.json params.json -o protocol.py --protocol-type assembly

  # Generate transformation protocol
  python -m pudu.generate_protocol transformation.json params.json -o protocol.py --protocol-type transformation

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
            assembly_subtype=assembly_subtype
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
