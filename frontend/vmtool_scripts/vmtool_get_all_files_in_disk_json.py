
# file: vmtool_get_all_files_in_disk_json.py
# location: VM-Diffing-Tool/frontend/vmtool_scripts/vmtool_get_all_files_in_disk_json.py
# author: Akash Maji
# date: 2025-10-15
# version: 0.1
# description: Get full file listing as JSON (numbered keys) from a VM disk image

import argparse
import json
import sys
import vmtool

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vmtool_get_all_files_in_disk_json",
        description="Get full file listing as JSON (numbered keys) from a VM disk image",
    )
    parser.add_argument("--disk", required=True, help="Path to qcow2/raw disk image (required)")
    parser.add_argument("--json", help="Path to write JSON listing; if omitted, prints to stdout")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose vmtool logs")
    return parser


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    args = build_parser().parse_args(argv)

    data = vmtool.get_files_with_metadata_json(args.disk, args.verbose)

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"JSON listing saved to: {args.json}")
    else:
        print(json.dumps(data, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
