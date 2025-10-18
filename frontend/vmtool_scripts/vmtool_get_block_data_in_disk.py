# file: vmtool_get_block_data_in_disk.py
# location: VM-Diffing-Tool/frontend/vmtool_scripts/vmtool_get_block_data_in_disk.py
# author: Akash Maji
# date: 2025-10-18
# version: 0.1
# description: Read a specific block from a VM disk image and display its contents

import argparse
import json
import vmtool

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vmtool_get_block_data_in_disk",
        description="Read a specific block from a VM disk image and display its contents",
    )
    parser.add_argument("--disk", required=True, help="Path to qcow2/raw disk image (required)")
    parser.add_argument("--block", type=int, required=True, help="Block number to read (required)")
    parser.add_argument("--block-size", type=int, default=4096, help="Block size in bytes (default: 4096)")
    parser.add_argument("--format", choices=["hex", "bits"], default="hex", help="Output format: hex or bits (default: hex)")
    parser.add_argument("--json", help="Path to output JSON file (optional)")
    parser.add_argument("--verbose", action="store_true", help="Print verbose output")
    return parser

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    
    if args.verbose:
        print(f"Reading block from disk image:")
        print(f"  Disk: {args.disk}")
        print(f"  Block number: {args.block}")
        print(f"  Block size: {args.block_size} bytes")
        print(f"  Format: {args.format}")
        print(f"Reading block data...")
    
    # Call the C++ backend function
    result = vmtool.get_block_data_in_disk(args.disk, args.block, args.block_size, args.format)
    
    if args.verbose:
        print(f"\nBlock data retrieved successfully!")
    
    # Print results
    for block_num, data in result.items():
        print(f"\nBlock {block_num}:")
        if args.format == "hex":
            # Print hex data in rows of 16 bytes for readability
            hex_bytes = data.split()
            for i in range(0, len(hex_bytes), 16):
                row = hex_bytes[i:i+16]
                offset = i
                print(f"  {offset:04X}: {' '.join(row)}")
        else:
            # Print bits data in rows of 64 bits for readability
            for i in range(0, len(data), 64):
                row = data[i:i+64]
                offset = i // 8
                print(f"  {offset:04X}: {row}")
    
    # Save to JSON if requested
    if args.json:
        with open(args.json, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nResults saved to: {args.json}")

if __name__ == "__main__":
    main()


# USAGE
"""
sudo python3 vmtool_get_block_data_in_disk.py \
    --disk /full/path/to/disk.qcow2 \
    --block 12 \
    --block-size 4096 \
    --format hex \
    --json block_data.json \
    --verbose
"""

# example input
"""
sudo python3 vmtool_get_block_data_in_disk.py \
    --disk /home/akashmaji/Desktop/vm3.qcow2 \
    --block 12 \
    --block-size 4096 \
    --format hex \
    --json block_12_data.json \
    --verbose
"""

# example with bits format
"""
sudo python3 vmtool_get_block_data_in_disk.py \
    --disk /home/akashmaji/Desktop/vm3.qcow2 \
    --block 42 \
    --format bits \
    --verbose
"""
