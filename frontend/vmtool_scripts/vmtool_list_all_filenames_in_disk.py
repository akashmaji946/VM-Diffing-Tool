# file: vmtool_list_all_filenames_in_disk.py
# location: VM-Diffing-Tool/frontend/vmtool_scripts/vmtool_list_all_filenames_in_disk.py
# author: Akash Maji
# date: 2025-10-18
# version: 0.1
# description: List all files in a VM disk image

import argparse
import json
import vmtool


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vmtool_list_all_filenames_in_disk",
        description="List all files in a VM disk image",
    )
    parser.add_argument("--disk", required=True, help="Path to qcow2/raw disk image (required)")
    parser.add_argument("--json", type=str, help="Save output to JSON file")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    ans = vmtool.list_files_in_disk(args.disk)
    
    if args.json:
        with open(args.json, 'w') as f:
            json.dump(ans, f, indent=2)
        print(f"Output saved to {args.json}")
    else:
        print(ans)


if __name__ == "__main__":
    main()