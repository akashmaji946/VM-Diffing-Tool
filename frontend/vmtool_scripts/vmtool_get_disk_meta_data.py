# file: vmtool_get_disk_meta_data.py
# location: VM-Diffing-Tool/frontend/vmtool_scripts/vmtool_get_disk_meta_data.py
# author: Akash Maji
# date: 2025-10-15
# version: 0.1
# description: Get aggregated metadata from a VM disk image using vmtool

import argparse
import json
import sys
import vmtool

disk = "/home/akashmaji/Desktop/vm1.qcow2"
file = "meta.json"
verbose = False

# The values above are defaults; CLI args can override them.

def print_meta_data(meta):
    print("===========================================================")
    print("Totals:")
    print("  files:", meta["files_count"])
    print("  dirs:", meta["dirs_count"])
    print("  total_file_bytes:", meta["total_file_bytes"])
    print("  total_dir_bytes:", meta["total_dir_bytes"])
    print("  total_bytes:", meta["total_bytes"])

    print("===========================================================")
    print("\nUsers (all, including zero):")
    for row in meta["per_user"]:
        print(f"  {row['user']} (uid={row['uid']}): files={row['files']} dirs={row['dirs']} bytes={row['bytes']}")

    print("===========================================================")
    print("\nGroups (all, including zero):")
    for row in meta["per_group"]:
        print(f"  {row['group']} (gid={row['gid']}): files={row['files']} dirs={row['dirs']} bytes={row['bytes']}")

    print("===========================================================")

# print_meta_data(meta)


def write_meta_data(meta, filename):
    with open(filename, "w") as f:
        f.write("===========================================================")
        f.write("\n")
        f.write("Totals:")
        f.write("\n")
        f.write("  files: " + str(meta["files_count"]))
        f.write("\n")
        f.write("  dirs: " + str(meta["dirs_count"]))
        f.write("\n")
        f.write("  total_file_bytes: " + str(meta["total_file_bytes"]))
        f.write("\n")
        f.write("  total_dir_bytes: " + str(meta["total_dir_bytes"]))
        f.write("\n")
        f.write("  total_bytes: " + str(meta["total_bytes"]))
        f.write("\n")
        f.write("===========================================================")
        f.write("\n")
        f.write("\nUsers (all, including zero):")
        f.write("\n")
        for row in meta["per_user"]:
            f.write(f"  {row['user']} (uid={row['uid']}): files={row['files']} dirs={row['dirs']} bytes={row['bytes']}")
            f.write("\n")
        f.write("===========================================================")
        f.write("\n")
        f.write("\nGroups (all, including zero):")
        f.write("\n")
        for row in meta["per_group"]:
            f.write(f"  {row['group']} (gid={row['gid']}): files={row['files']} dirs={row['dirs']} bytes={row['bytes']}")
            f.write("\n")
        f.write("===========================================================")


def save_meta_data(meta, filename):
    with open(filename, "w") as f:
        json.dump(meta, f, indent=4)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vmtool_get_meta_data",
        description="Fetch aggregated metadata from a VM disk image using vmtool",
    )
    parser.add_argument("--disk", required=True, help="Path to qcow2/raw disk image (required)")
    parser.add_argument("--json", help="Path to write JSON metadata output")
    parser.add_argument("--out", help="Path to write human-readable TEXT output")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose vmtool logs")
    return parser


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    args = build_parser().parse_args(argv)

    # Require at least one of --json/--out/--verbose to be set
    if not (args.json or args.out or args.verbose):
        print("error: at least one of --json, --out, or --verbose must be provided", file=sys.stderr)
        build_parser().print_help()
        return 2

    # Fetch meta from backend
    meta = vmtool.get_disk_meta_data(args.disk, args.verbose)

    wrote_any = False
    if args.json:
        save_meta_data(meta, args.json)
        print(f"JSON saved to: {args.json}")
        wrote_any = True
    if args.out:
        write_meta_data(meta, args.out)
        print(f"Text saved to: {args.out}")
        wrote_any = True

    if not wrote_any and args.verbose:
        # If only verbosity requested, still print summary to stdout
        print_meta_data(meta)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# USAGE
"""
sudo python3 vmtool_get_disk_meta_data.py \
    --disk /full/path/to/disk.qcow2 \
    [--json /full/path/to/output.json] \
    [--out /full/path/to/output.txt] \
    [--verbose]
"""

# example input
"""
sudo python3 vmtool_get_disk_meta_data.py \
    --disk /home/akashmaji/Desktop/vm1.qcow2 \
    --json $PWD/meta.json \
    --out $PWD/meta.txt \
    --verbose
"""


