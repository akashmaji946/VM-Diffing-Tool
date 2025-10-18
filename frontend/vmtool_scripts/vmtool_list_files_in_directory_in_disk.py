# file: vmtool_list_files_in_directory_in_disk.py
# location: VM-Diffing-Tool/frontend/vmtool_scripts/vmtool_list_files_in_directory_in_disk.py
# author: Akash Maji
# date: 2025-10-15
# version: 0.1
# description: List all files in a directory in the guest image

import argparse
import vmtool


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vmtool_list_files_in_directory_in_disk",
        description="List all files in a directory in the guest image",
    )
    parser.add_argument("--disk", required=True, help="Path to qcow2/raw disk image (required)")
    parser.add_argument("--directory", required=True, help="Path to directory to list (required)")
    parser.add_argument("--detailed", action="store_true", help="List detailed file information")
    return parser   


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    ans = vmtool.list_files_in_directory_in_disk(args.disk, args.directory, args.detailed)
    print(ans)

if __name__ == "__main__":
    main()


# USAGE
"""
sudo python3 vmtool_list_files_in_directory_in_disk.py \
    --disk /full/path/to/disk.qcow2 \
    --directory /full/path/to/directory \
    [--detailed]
"""

# example input
"""
sudo python3 vmtool_list_files_in_directory_in_disk.py \
    --disk /home/akashmaji/Desktop/vm1.qcow2 \
    --directory /etc \
    --detailed
"""
