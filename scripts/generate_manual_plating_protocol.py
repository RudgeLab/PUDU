import json
import argparse
from pathlib import Path

from pudu.plating import ManualPlating


def main():
    parser = argparse.ArgumentParser(description="Generate a manual plating Markdown protocol.")
    parser.add_argument("--input", default="scripts/plating_input.json", help="Path to plating JSON input file.")
    parser.add_argument("--output", default="scripts/manual_plating_protocol.md", help="Path to Markdown output file.")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    plating_data = json.loads(input_path.read_text(encoding="utf-8"))

    manual_protocol = ManualPlating(plating_data=plating_data)
    manual_protocol.process_bacterium_locations()
    manual_protocol.write_markdown(str(output_path))

    print(f"Manual plating protocol written to {output_path}")


if __name__ == "__main__":
    main()
