#!/usr/bin/env python3

# filename: list_all_files_in_disk.py
# location: VM-Diffing-Tool/frontend/python_scripts/list_all_files_in_disk.py
# author: Akash Maji
# date: 2025-10-14
# description: List all files in a VM disk image with metadata (size, permissions, modification date, filename)
# using libguestfs. Optionally prints to console in --verbose mode.

"""
List all files in a VM disk image with metadata (size, permissions, modification date, filename)
using libguestfs. Optionally prints to console in verbose mode.
"""

import argparse
import sys
import guestfs
from datetime import datetime
import stat

def human_readable_permissions(mode):
    """Convert a file mode to rwxrwxrwx format."""
    perms = ""
    for who in [stat.S_IRUSR, stat.S_IWUSR, stat.S_IXUSR,
                stat.S_IRGRP, stat.S_IWGRP, stat.S_IXGRP,
                stat.S_IROTH, stat.S_IWOTH, stat.S_IXOTH]:
        perms += (mode & who) and "rwxrwxrwx"[list(bin(who)[2:]).count('1')-1] or "-"
    # Alternative simpler approach:
    perms = ""
    mapping = [(stat.S_IRUSR,"r"),(stat.S_IWUSR,"w"),(stat.S_IXUSR,"x"),
               (stat.S_IRGRP,"r"),(stat.S_IWGRP,"w"),(stat.S_IXGRP,"x"),
               (stat.S_IROTH,"r"),(stat.S_IWOTH,"w"),(stat.S_IXOTH,"x")]
    for flag, char in mapping:
        perms += char if mode & flag else "-"
    return perms

def list_files_with_metadata(disk_path, output_file, verbose=False):
    """Mount the VM disk image read-only and list all files with metadata."""
    g = guestfs.GuestFS(python_return_dict=True)
    g.add_drive_opts(disk_path, readonly=1)
    g.launch()

    roots = g.inspect_os()
    if not roots:
        raise RuntimeError("No OS found in image")

    # Mount all partitions
    for root in roots:
        mountpoints = g.inspect_get_mountpoints(root)
        for mountpoint, device in sorted(mountpoints.items(), key=lambda x: len(x[0])):
            g.mount_ro(device, mountpoint)

    with open(output_file, "w") as f:
        f.write(f"{'Size':>10} {'Permission':>10} {'Last Modified':>20} {'Name':>20}\n")
        f.write("="*60 + "\n")
        for path in g.find("/"):
            if path == ".":
                full_path = "/"
            else:
                full_path = "/" + path
            try:
                st = g.stat(full_path)
                size = st["size"]
                perms = human_readable_permissions(st["mode"])
                mtime = datetime.fromtimestamp(st["mtime"]).strftime("%Y-%m-%d %H:%M:%S")
            except RuntimeError:
                size = "-"
                perms = "-"
                mtime = "-"

            line = f"{str(size):>10} {perms:>10} {mtime:>20} {full_path}"
            f.write(line + "\n")
            if verbose:
                print(line)

    g.shutdown()
    g.close()
    print(f"\nFile listing saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="List all files in a VM disk image with metadata.")
    parser.add_argument("--file", required=True, help="Path to the disk image (.qcow2)")
    parser.add_argument("--out", required=True, help="Path to output text file")
    parser.add_argument("--verbose", action="store_true", help="Print file list to console")
    args = parser.parse_args()

    try:
        list_files_with_metadata(args.file, args.out, verbose=args.verbose)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
