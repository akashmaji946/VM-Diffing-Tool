# file: vmtool_list_all_files_in_disk.py
# location: VM-Diffing-Tool/frontend/vmtool_scripts/vmtool_list_all_files_in_disk.py
# author: Akash Maji
# date: 2025-10-15
# version: 0.1
# description: List all files in a VM disk image with metadata (via C++ backend)

import argparse
import sys
import vmtool

def print_entries(entries):
    print(f"{'Size':>10} {'Permission':>10} {'Last Modified':>20} {'Name':>20}")
    print("=" * 60)
    for e in entries:
        size = e["size"]
        perms = e["perms"]
        mtime = e["mtime"]
        path = e["path"]
        print(f"{str(size):>10} {perms:>10} {mtime:>20} {path}")


def main():
    parser = argparse.ArgumentParser(description="List all files in a VM disk image with metadata (via C++ backend)")
    parser.add_argument("--file", required=True, help="Path to the disk image (.qcow2)")
    parser.add_argument("--out", required=True, help="Path to output text file")
    parser.add_argument("--verbose", action="store_true", help="Print file list to console")
    args = parser.parse_args()

    try:

        # get entries from vmtool
        entries = vmtool.list_files_with_metadata(args.file, verbose=args.verbose)
        
        # write entries to file
        vmtool.write_files_with_metadata(entries, args.out)

        if args.verbose:
            print_entries(entries)
        print(f"\nFile listing saved to: {args.out}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()


# USAGE
"""
sudo python3 vmtool_list_all_files_in_disk.py \
    --file /full/path/to/disk.qcow2 \
    --out /full/path/to/output.txt \
    [--verbose]
"""


