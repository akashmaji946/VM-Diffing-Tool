"""
VMT console script entry point.
This module lazily imports the native 'vmtool' extension only when needed,
so invoking 'vmtool' without subcommands won't touch libguestfs.
"""
from __future__ import annotations

import sys
import argparse
import json

VERSION = "0.1"


def print_welcome() -> None:
    print(f"Welcome to VMT {VERSION} version")


def do_list(args: argparse.Namespace) -> int:
    disk = args.disk
    out = args.out
    verbose = bool(args.verbose)

    try:
        import vmtool
        entries = vmtool.list_files_with_metadata(disk, verbose=verbose)
        vmtool.write_files_with_metadata(entries, out)
        if verbose:
            print(f"Wrote {len(entries)} entries to: {out}")
        else:
            print(f"File listing saved to: {out}")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 2


def do_meta(args: argparse.Namespace) -> int:
    disk = args.disk
    verbose = bool(args.verbose)
    json_out = args.json

    try:
        import vmtool
        meta = vmtool.get_meta_data(disk, verbose=verbose)
        if json_out:
            with open(json_out, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)
            print(f"Metadata saved to: {json_out}")
        else:
            print("Totals:")
            print(f"  files: {meta['files_count']}")
            print(f"  dirs: {meta['dirs_count']}")
            print(f"  total_file_bytes: {meta['total_file_bytes']}")
            print(f"  total_dir_bytes: {meta['total_dir_bytes']}")
            print(f"  total_bytes: {meta['total_bytes']}")
            print("\nTop users by bytes:")
            for row in meta['per_user'][:5]:
                print(f"  {row['user']} (uid={row['uid']}): files={row['files']} dirs={row['dirs']} bytes={row['bytes']}")
            print("\nTop groups by bytes:")
            for row in meta['per_group'][:5]:
                print(f"  {row['group']} (gid={row['gid']}): files={row['files']} dirs={row['dirs']} bytes={row['bytes']}")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vmtool",
        description="VMT CLI - Utilities for diffing and inspecting VM disk images",
        add_help=True,
    )
    parser.add_argument(
        "-v", "--version", action="version", version=f"vmtool {VERSION}"
    )

    sub = parser.add_subparsers(dest="command", metavar="<command>")

    p_list = sub.add_parser("list", help="List all files with metadata and write to a file")
    p_list.add_argument("--disk", required=True, help="Path to qcow2/raw disk image")
    p_list.add_argument("--out", required=True, help="Output text file path")
    p_list.add_argument("--verbose", action="store_true", help="Verbose output")
    p_list.set_defaults(func=do_list)

    p_meta = sub.add_parser("meta", help="Get aggregated metadata for the disk image")
    p_meta.add_argument("--disk", required=True, help="Path to qcow2/raw disk image")
    p_meta.add_argument("--verbose", action="store_true", help="Verbose output")
    p_meta.add_argument("--json", help="Optional path to save full JSON metadata")
    p_meta.set_defaults(func=do_meta)

    return parser


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if len(argv) == 0:
        print_welcome()
        print("Use -h for help.")
        return 0

    parser = build_parser()
    args = parser.parse_args(argv)

    if not getattr(args, "command", None):
        print_welcome()
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
