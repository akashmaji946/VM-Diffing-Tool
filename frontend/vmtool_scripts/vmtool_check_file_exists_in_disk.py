# file: vmtool_check_file_exists_in_disk.py
# location: VM-Diffing-Tool/frontend/vmtool_scripts/vmtool_check_file_exists_in_disk.py
# author: Akash Maji
# date: 2025-10-15
# version: 0.1
# description: Check if a file exists in a VM disk image

import argparse
import vmtool

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vmtool_check_file_exists_in_disk",
        description="Check if a file exists in a VM disk image",
    )
    parser.add_argument("--disk", required=True, help="Path to qcow2/raw disk image (required)")
    parser.add_argument("--name", required=True, help="Path to file to check (required)")
    return parser

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    ans = vmtool.check_file_exists_in_disk(args.disk, args.name)
    print(ans)

if __name__ == "__main__":
    main()


# USAGE
"""
sudo python3 vmtool_check_file_exists_in_disk.py \
    --disk /full/path/to/disk.qcow2 \
    --name /full/path/to/file
"""

# example input
"""
sudo python3 vmtool_check_file_exists_in_disk.py \
    --disk /home/akashmaji/Desktop/vm1.qcow2 \
    --name /etc/hosts
"""



