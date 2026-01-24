import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.etl.pdf_processor import process_pdf


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse a PDF into JSON.")
    parser.add_argument(
        "--pdf",
        default="docs/Q3FY25 Duolingo 9-30-25 Shareholder Letter Final.pdf",
        help="Path to the PDF to parse",
    )
    parser.add_argument(
        "--out",
        default="parsed_output.json",
        help="Output JSON file path",
    )
    args = parser.parse_args()

    result = process_pdf(args.pdf)
    output_path = Path(args.out)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
