import argparse
import sys
import vmtool


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vmtool_get_file_contents_in_disk",
        description="Read a file from inside a VM disk image (text or binary)",
    )
    parser.add_argument("--disk", required=True, help="Path to qcow2/raw disk image (required)")
    parser.add_argument("--name", required=True, help="Path to file inside the guest (e.g., /etc/hosts)")
    parser.add_argument("--binary", action="store_true", help="Return bytes instead of text")
    parser.add_argument("--read", type=int, default=-1, help="Bytes to read (-1 means all)")
    parser.add_argument("--stop", default="", help="Stop at first occurrence of this delimiter (not included)")
    parser.add_argument("--out", help="Optional output file path; writes bytes if --binary else text")
    return parser


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    args = build_parser().parse_args(argv)

    try:
        data = vmtool.get_file_contents_in_disk(
            args.disk, args.name, binary=args.binary, read=args.read, stop=args.stop
        )
        if args.out:
            if args.binary:
                # Write raw bytes
                with open(args.out, "wb") as f:
                    f.write(data)
            else:
                with open(args.out, "w", encoding="utf-8") as f:
                    f.write(data)
            print(f"Saved to: {args.out}")
        else:
            if args.binary:
                # Stream bytes to stdout safely
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()
            else:
                print(data)
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())


# USAGE
"""
sudo python3 vmtool_get_file_contents_in_disk.py \
    --disk /full/path/to/disk.qcow2 \
    --name /full/path/to/file \
    [--out /full/path/to/output] \
    [--binary] \
    [--read <bytes>] \
    [--stop <delimiter>] \
"""

# example input
"""
sudo python3 vmtool_get_file_contents_in_disk.py \
    --disk /home/akashmaji/Desktop/vm1.qcow2 \
    --name /bin/bash \
    --binary \
    --out $PWD/output2.txt \
    --read -1
"""

