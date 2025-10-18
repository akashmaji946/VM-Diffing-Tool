# file: vmtool_list_blocks_difference_in_disks.py
# location: VM-Diffing-Tool/frontend/vmtool_scripts/vmtool_list_blocks_difference_in_disks.py
# author: Akash Maji
# date: 2025-10-18
# version: 0.1
# description: Compare two VM disk images block by block and list differing blocks

import argparse
import json
import vmtool

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vmtool_list_blocks_difference_in_disks",
        description="Compare two VM disk images block by block and list differing blocks",
    )
    parser.add_argument("--disk1", required=True, help="Path to first qcow2/raw disk image (required)")
    parser.add_argument("--disk2", required=True, help="Path to second qcow2/raw disk image (required)")
    parser.add_argument("--block-size", type=int, default=4096, help="Block size in bytes (default: 4096)")
    parser.add_argument("--start", type=int, default=0, help="Starting block number (default: 0)")
    parser.add_argument("--end", type=int, default=-1, help="Ending block number (default: -1 for last block)")
    parser.add_argument("--json", help="Path to output JSON file (optional)")
    parser.add_argument("--verbose", action="store_true", help="Print verbose output")
    return parser

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    
    if args.verbose:
        print(f"Comparing disk images:")
        print(f"  Disk 1: {args.disk1}")
        print(f"  Disk 2: {args.disk2}")
        print(f"  Block size: {args.block_size} bytes")
        print(f"  Start block: {args.start}")
        print(f"  End block: {args.end if args.end >= 0 else 'last'}")
        print(f"Starting comparison (this may take a while)...")
    
    # Call the C++ backend function
    result = vmtool.list_blocks_difference_in_disks(args.disk1, args.disk2, args.block_size, args.start, args.end)
    
    if args.verbose:
        print(f"\nComparison complete!")
        print(f"Found {result.get('total_differing_blocks', 0)} differing blocks")
    
    # Print results
    differing_blocks = result.get('differing_blocks', {})
    if len(differing_blocks) == 0:
        print("No differences found - disk images are identical at block level")
    else:
        print(f"\nDiffering blocks ({len(differing_blocks)} total):")
        # Print first 20 blocks
        count = 0
        for key in sorted(differing_blocks.keys(), key=lambda x: int(x)):
            if count < 20:
                print(f"  {key}: {differing_blocks[key]}")
                count += 1
            else:
                print(f"  ... and {len(differing_blocks) - 20} more blocks")
                break
    
    # Save to JSON if requested
    if args.json:
        with open(args.json, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nResults saved to: {args.json}")

if __name__ == "__main__":
    main()


# USAGE
"""
sudo python3 vmtool_list_blocks_difference_in_disks.py \
    --disk1 /full/path/to/disk1.qcow2 \
    --disk2 /full/path/to/disk2.qcow2 \
    --block-size 4096 \
    --start 0 \
    --end -1 \
    --json output.json \
    --verbose
"""

# example input
"""
sudo python3 vmtool_list_blocks_difference_in_disks.py \
    --disk1 /home/akashmaji/Desktop/vm3.qcow2 \
    --disk2 /home/akashmaji/Desktop/vm3c.qcow2 \
    --block-size 4096 \
    --start 0 \
    --end 1000 \
    --json diff_results.json \
    --verbose
"""
