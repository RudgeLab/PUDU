import json
import argparse
from pathlib import Path

from pudu.transformation import ManualTransformation


def main():
    parser = argparse.ArgumentParser(description="Generate a manual heat-shock transformation Markdown protocol.")
    parser.add_argument("--input", default="scripts/manual_transformation_input.json", help="Path to SBOL-style JSON input file.")
    parser.add_argument("--output", default="scripts/manual_transformation_protocol.md", help="Path to Markdown output file.")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    transformations = json.loads(input_path.read_text(encoding="utf-8"))

    manual_protocol = ManualTransformation(transformation_data=transformations)
    manual_protocol.process_transformations()
    manual_protocol.write_markdown(str(output_path))

    print(f"Manual transformation protocol written to {output_path}")


if __name__ == "__main__":
    main()
