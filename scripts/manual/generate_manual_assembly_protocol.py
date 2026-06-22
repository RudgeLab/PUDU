import json
import argparse
from pathlib import Path

from pudu.assembly import ManualAssembly


def main():
    parser = argparse.ArgumentParser(description="Generate a manual Golden Gate Markdown protocol.")
    parser.add_argument("--input", default="scripts/manual/manual_assembly_input.json", help="Path to SBOL-style JSON input file.")
    parser.add_argument("--output", default="scripts/manual/manual_assembly_protocol.md", help="Path to Markdown output file.")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    assemblies = json.loads(input_path.read_text(encoding="utf-8"))

    manual_protocol = ManualAssembly(assemblies=assemblies)
    manual_protocol.process_assemblies()
    manual_protocol.write_markdown(str(output_path))

    print(f"Manual protocol written to {output_path}")


if __name__ == "__main__":
    main()
